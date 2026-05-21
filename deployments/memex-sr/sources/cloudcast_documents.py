"""Cache-backed Cloudcast document ingestion source."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from okg.substrate.errors import SubstrateError
from okg.substrate.library.sources.base import (
    EdgeFact,
    EdgeKey,
    NodeFact,
    RecordEmission,
    RecordNode,
    RecordSet,
    SourceHealth,
    SourceRun,
)


_SAFE_RE = re.compile(r"[^a-zA-Z0-9_.:-]+")


def _safe(value: str) -> str:
    return _SAFE_RE.sub("-", value).strip("-") or "unknown"


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _node(
    node_id: str,
    subtype: str,
    attrs: dict[str, Any],
    source_record_id: dict[str, Any],
    revision: dict[str, Any],
) -> NodeFact:
    return NodeFact(
        node_id=node_id,
        subtype=subtype,
        attrs=attrs,
        source_record_id=source_record_id,
        source_revision=revision,
    )


def _edge(
    src: str,
    edge_type: str,
    dst: str,
    source_record_id: dict[str, Any],
    revision: dict[str, Any],
) -> EdgeFact:
    return EdgeFact(
        src=src,
        dst=dst,
        edge_type=edge_type,
        attrs={},
        source_record_id=source_record_id,
        source_revision=revision,
    )


class _HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "br", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)

    def text(self) -> str:
        return "\n".join(self.parts)


def _html_to_text(raw: bytes, warnings: list[str]) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        return soup.get_text("\n")
    except ModuleNotFoundError:
        parser = _HTMLTextParser()
        parser.feed(raw.decode("utf-8", errors="replace"))
        return parser.text()
    except Exception as exc:
        warnings.append(f"bs4_failed:{type(exc).__name__}")
        parser = _HTMLTextParser()
        parser.feed(raw.decode("utf-8", errors="replace"))
        return parser.text()


def _pdf_to_text(path: Path, warnings: list[str]) -> str:
    try:
        from pdfminer.high_level import extract_text
    except Exception as exc:
        warnings.append(f"pdf_parser_unavailable:{type(exc).__name__}")
        return ""
    try:
        return extract_text(str(path)) or ""
    except Exception as exc:
        warnings.append(f"pdf_parse_failed:{type(exc).__name__}")
        return ""


def _decode_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _format_for(path: Path, mime_type: str | None) -> str:
    mime = (mime_type or "").lower()
    suffix = path.suffix.lower()
    if suffix == ".pdf" or "pdf" in mime:
        return "pdf"
    if suffix in {".html", ".htm"} or "html" in mime:
        return "html"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".py", ".cpp", ".cc", ".c", ".h", ".hpp", ".rs", ".go", ".java", ".js", ".ts"}:
        return "code"
    return "text"


def _extract_text(path: Path, record: dict[str, Any]) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    fmt = _format_for(path, record.get("mime_type"))
    raw = path.read_bytes()
    if fmt == "pdf":
        text = _pdf_to_text(path, warnings)
    elif fmt == "html":
        text = _html_to_text(raw, warnings)
    else:
        text = _decode_text(raw)
    text = _normalize_text(text)
    if not text:
        warnings.append("empty_text")
    elif len(text) < 200:
        warnings.append("short_text")
    return text, fmt, warnings


def _chunks(text: str, *, max_chars: int, overlap: int) -> list[tuple[int, str]]:
    if not text:
        return []
    if overlap >= max_chars:
        raise ValueError("overlap must be less than max_chars")
    out: list[tuple[int, str]] = []
    step = max_chars - overlap
    offset = 0
    while offset < len(text):
        end = min(len(text), offset + max_chars)
        out.append((offset, text[offset:end]))
        if end == len(text):
            break
        offset += step
    return out


@dataclass
class CloudcastDocumentsSource:
    """Emit source-backed Cloudcast documents and chunks.

    The source reads the JSONL acquisition manifest produced by
    `fetch_cloudcast_sources.py`. It never performs network I/O.
    """

    assets_manifest: Path | str
    repo_root: Path | str
    source_pack: str = "cloudcast-actionable-v0"
    problem_name: str = "cloudcast"
    chunk_max_chars: int = 3200
    chunk_overlap: int = 250

    name: str = "cloudcast_documents"
    profile: str = "discovery_crawl"

    def __post_init__(self) -> None:
        self.assets_manifest = Path(self.assets_manifest).expanduser().resolve()
        self.repo_root = Path(self.repo_root).expanduser().resolve()
        self.last_run_stats: dict[str, Any] = {}

    def run(
        self,
        run_id: str,
        *,
        mode: str = "cursor",
        cursor: Optional[dict[str, Any]] = None,
        sync_scope: Optional[dict[str, Any]] = None,
    ) -> SourceRun:
        if not self.assets_manifest.is_file():
            raise SubstrateError(
                f"Cloudcast acquired-assets manifest not found: {self.assets_manifest}",
                data={"assets_manifest": str(self.assets_manifest)},
            )

        records = self._load_records()
        manifest_fingerprint = _hash_json(
            [
                {
                    "source_id": record.get("source_id"),
                    "state": record.get("acquisition_state"),
                    "available": bool(record.get("available")),
                    "local_path": record.get("local_path"),
                    "content_sha256": record.get("content_sha256"),
                    "byte_count": record.get("byte_count"),
                }
                for record in records
            ]
        )
        completed_scope = mode in {"reconcile", "scope_complete"}
        prior_record_set = self._prior_record_set(cursor)
        if (
            completed_scope
            and isinstance(cursor, dict)
            and cursor.get("manifest_fingerprint") == manifest_fingerprint
            and prior_record_set is not None
        ):
            self.last_run_stats = {
                "records": len(records),
                "available_records": sum(1 for r in records if r.get("available")),
                "documents": 0,
                "chunks": 0,
                "no_op": True,
            }
            return SourceRun(
                facts=[],
                completed_scope=True,
                next_cursor={
                    **cursor,
                    "manifest_fingerprint": manifest_fingerprint,
                    "last_run_id": run_id,
                },
                run_mode=mode,
                record_set=prior_record_set,
                health=SourceHealth(
                    status="ok",
                    mode="manifest",
                    record_count=len(records),
                    content_hash=manifest_fingerprint,
                    cache_path=str(self.assets_manifest),
                    reason="cloudcast document manifest unchanged; no-op",
                ),
            )

        revision = {
            "run_id": run_id,
            "manifest": str(self.assets_manifest),
            "manifest_fingerprint": manifest_fingerprint,
        }
        emitted: list[NodeFact | EdgeFact] = []
        emissions: dict[str, dict[str, Any]] = {}
        stats = {
            "records": len(records),
            "available_records": 0,
            "unavailable_records": 0,
            "documents": 0,
            "chunks": 0,
            "parse_failures": 0,
            "no_op": False,
        }

        for record in records:
            record_key = str(record.get("source_id") or record.get("plan_id"))
            if not record_key:
                continue
            facts, emission, record_stats = self._record_facts(record, revision)
            emitted.extend(facts)
            emissions[record_key] = emission
            for key, value in record_stats.items():
                stats[key] = stats.get(key, 0) + value

        self.last_run_stats = stats
        record_set = (
            self._record_set_from_emissions(emissions, revision=revision)
            if completed_scope else None
        )

        return SourceRun(
            facts=iter(emitted),
            completed_scope=completed_scope,
            next_cursor={
                "manifest_fingerprint": manifest_fingerprint,
                "last_run_id": run_id,
                "records": len(records),
            },
            run_mode=mode,
            record_set=record_set,
            health=SourceHealth(
                status="ok",
                mode="manifest",
                record_count=len(records),
                content_hash=manifest_fingerprint,
                cache_path=str(self.assets_manifest),
                reason=(
                    f"available={stats['available_records']} "
                    f"documents={stats['documents']} chunks={stats['chunks']} "
                    f"parse_failures={stats['parse_failures']}"
                ),
            ),
        )

    def _load_records(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for line_no, line in enumerate(self.assets_manifest.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SubstrateError(
                    f"invalid JSONL in {self.assets_manifest}:{line_no}",
                    data={"line_no": line_no, "error": str(exc)},
                ) from None
            if not isinstance(raw, dict):
                raise SubstrateError(
                    f"asset manifest row must be an object: {self.assets_manifest}:{line_no}",
                    data={"line_no": line_no},
                )
            out.append(raw)
        out.sort(key=lambda row: str(row.get("source_id") or row.get("plan_id") or ""))
        return out

    @staticmethod
    def _prior_record_set(cursor: Optional[dict[str, Any]]) -> RecordSet | None:
        if not isinstance(cursor, dict):
            return None
        raw = cursor.get("record_set")
        if raw is None:
            return None
        try:
            return RecordSet.from_cursor(raw)
        except (TypeError, ValueError):
            return None

    def _record_facts(
        self,
        record: dict[str, Any],
        revision: dict[str, Any],
    ) -> tuple[list[NodeFact | EdgeFact], dict[str, Any], dict[str, int]]:
        source_id = str(record.get("source_id") or record.get("plan_id"))
        safe_id = _safe(source_id)
        source_record_id = {"source_id": source_id}
        asset_id = f"document_asset:cloudcast:{safe_id}"
        topic_slugs = list(record.get("topic_slugs") or [])
        if not topic_slugs:
            topic_slugs = [
                "cloudcast",
                "multicast",
                "routing",
                "traffic-engineering",
            ]

        available = bool(record.get("available"))
        stats = {
            "available_records": 1 if available else 0,
            "unavailable_records": 0 if available else 1,
            "documents": 0,
            "chunks": 0,
            "parse_failures": 0,
        }
        facts: list[NodeFact | EdgeFact] = []
        asset_attrs = {
            "asset_id": asset_id,
            "asset_kind": "full_text" if available else "acquisition_target",
            "url": record.get("source_url"),
            "access_basis": record.get("access_basis"),
            "source": "cloudcast_sources",
            "downloaded": available,
            "source_id": source_id,
            "source_pack": self.source_pack,
            "problem_name": self.problem_name,
            "title": record.get("title"),
            "category": record.get("category"),
            "tier": record.get("tier"),
            "local_path": record.get("local_path"),
            "content_sha256": record.get("content_sha256"),
            "byte_count": record.get("byte_count"),
            "mime_type": record.get("mime_type"),
            "acquisition_action": record.get("acquisition_action"),
            "acquisition_state": record.get("acquisition_state"),
            "review_state": record.get("review_state"),
            "transfer_to_cloudcast": record.get("transfer_to_cloudcast"),
            "extraction_targets": list(record.get("extraction_targets") or []),
            "topic_slugs": topic_slugs,
        }
        asset_attrs["text"] = " ".join(
            str(value)
            for value in [
                asset_attrs.get("title"),
                asset_attrs.get("url"),
                asset_attrs.get("access_basis"),
                asset_attrs.get("transfer_to_cloudcast"),
                asset_attrs.get("acquisition_state"),
            ]
            if value
        )
        facts.append(_node(asset_id, "document_asset", asset_attrs, source_record_id, revision))
        emission: dict[str, Any] = {
            "asset_id": asset_id,
            "document_id": None,
            "chunks": [],
            "edges": [],
        }

        local_path = record.get("local_path")
        if not available or not local_path:
            return facts, emission, stats
        path = (self.repo_root / str(local_path)).resolve()
        try:
            path.relative_to(self.repo_root)
        except ValueError:
            stats["parse_failures"] += 1
            return facts, emission, stats
        if not path.is_file():
            stats["parse_failures"] += 1
            return facts, emission, stats

        text, fmt, warnings = _extract_text(path, record)
        if not text:
            stats["parse_failures"] += 1
        text_hash = _hash_text(text)
        doc_id = f"doc:cloudcast:{safe_id}:{text_hash[:16]}"
        parsed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        doc_attrs = {
            "doc_id": doc_id,
            "repo": "cloudcast_sources",
            "path": str(local_path),
            "format": fmt,
            "byte_count": record.get("byte_count") or path.stat().st_size,
            "content_sha256": record.get("content_sha256"),
            "text_sha256": text_hash,
            "parsed_at": parsed_at,
            "parse_warnings": warnings,
            "title": record.get("title") or source_id,
            "source_id": source_id,
            "source_pack": self.source_pack,
            "problem_name": self.problem_name,
            "category": record.get("category"),
            "tier": record.get("tier"),
            "access_basis": record.get("access_basis"),
            "review_state": record.get("review_state"),
            "topic_slugs": topic_slugs,
            "transfer_to_cloudcast": record.get("transfer_to_cloudcast"),
            "extraction_targets": list(record.get("extraction_targets") or []),
            "document_asset_id": asset_id,
            "text": f"{record.get('title') or source_id}\n\n{text[:4000]}",
        }
        facts.append(_node(doc_id, "document", doc_attrs, source_record_id, revision))
        emission["document_id"] = doc_id
        stats["documents"] += 1

        for index, (offset, chunk_text) in enumerate(
            _chunks(text, max_chars=self.chunk_max_chars, overlap=self.chunk_overlap)
        ):
            chunk_hash = _hash_text(f"{source_id}|{index}|{chunk_text}")
            chunk_id = f"chunk:cloudcast:{chunk_hash[:20]}"
            chunk_source_record_id = {"source_id": source_id, "chunk_index": index}
            chunk_attrs = {
                "chunk_id": chunk_id,
                "text": chunk_text,
                "char_offset": offset,
                "char_length": len(chunk_text),
                "content_sha256": _hash_text(chunk_text),
                "chunker_name": "cloudcast_window",
                "chunk_index": index,
                "source_id": source_id,
                "source_pack": self.source_pack,
                "problem_name": self.problem_name,
                "title": record.get("title") or source_id,
                "category": record.get("category"),
                "tier": record.get("tier"),
                "topic_slugs": topic_slugs,
                "transfer_to_cloudcast": record.get("transfer_to_cloudcast"),
                "extraction_targets": list(record.get("extraction_targets") or []),
                "document_id": doc_id,
                "document_asset_id": asset_id,
            }
            facts.append(_node(chunk_id, "document_chunk", chunk_attrs, chunk_source_record_id, revision))
            facts.append(_edge(doc_id, "contains", chunk_id, chunk_source_record_id, revision))
            facts.append(_edge(chunk_id, "member_of", doc_id, chunk_source_record_id, revision))
            emission["chunks"].append(chunk_id)
            emission["edges"].append(
                {
                    "src": doc_id,
                    "dst": chunk_id,
                    "edge_type": "contains",
                    "source_record_id": chunk_source_record_id,
                }
            )
            emission["edges"].append(
                {
                    "src": chunk_id,
                    "dst": doc_id,
                    "edge_type": "member_of",
                    "source_record_id": chunk_source_record_id,
                }
            )
            stats["chunks"] += 1

        return facts, emission, stats

    @staticmethod
    def _record_set_from_emissions(
        emissions: dict[str, dict[str, Any]],
        *,
        revision: dict[str, Any],
    ) -> RecordSet:
        records: dict[str, RecordEmission] = {}
        for record_key, emitted in emissions.items():
            source_record_id = {"source_id": record_key}
            primary = RecordNode(
                node_id=emitted["asset_id"],
                subtype="document_asset",
                source_record_id=source_record_id,
                source_revision=revision,
            )
            descendants: list[RecordNode] = []
            if emitted.get("document_id"):
                descendants.append(
                    RecordNode(
                        node_id=emitted["document_id"],
                        subtype="document",
                        source_record_id=source_record_id,
                        source_revision=revision,
                    )
                )
            for chunk_id in emitted.get("chunks") or []:
                descendants.append(
                    RecordNode(
                        node_id=chunk_id,
                        subtype="document_chunk",
                        source_record_id={"source_id": record_key, "chunk_id": chunk_id},
                        source_revision=revision,
                    )
                )
            edges = [
                EdgeKey(
                    src=edge["src"],
                    dst=edge["dst"],
                    edge_type=edge["edge_type"],
                    source_record_id=edge.get("source_record_id") or source_record_id,
                    source_revision=revision,
                )
                for edge in emitted.get("edges") or []
            ]
            records[record_key] = RecordEmission(
                primary=primary,
                descendants=descendants,
                edges=edges,
            )
        return RecordSet(records=records)


__all__ = ["CloudcastDocumentsSource"]
