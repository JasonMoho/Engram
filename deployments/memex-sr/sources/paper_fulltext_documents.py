"""Cache-backed full-text paper document source."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

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

from sources.cloudcast_documents import (
    _chunks,
    _edge,
    _extract_text,
    _hash_json,
    _hash_text,
    _node,
    _safe,
)


@dataclass
class PaperFulltextDocumentsSource:
    """Emit documents/chunks from acquired paper full-text files.

    The source consumes `paper_fulltext_assets.jsonl`; it never performs
    network I/O. Acquisition is a separate operator command.
    """

    assets_manifest: Path | str
    repo_root: Path | str
    source_pack: str = "systems-db-2022-2026"
    chunk_max_chars: int = 3200
    chunk_overlap: int = 250

    name: str = "paper_fulltext_documents"
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
                f"paper full-text manifest not found: {self.assets_manifest}",
                data={"assets_manifest": str(self.assets_manifest)},
            )
        records = self._load_records()
        manifest_fingerprint = _hash_json(
            [
                {
                    "paper_id": r.get("paper_id"),
                    "asset_id": r.get("asset_id"),
                    "state": r.get("acquisition_state"),
                    "available": bool(r.get("available")),
                    "local_path": r.get("local_path"),
                    "content_sha256": r.get("content_sha256"),
                    "byte_count": r.get("byte_count"),
                }
                for r in records
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
                "parse_failures": 0,
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
                    reason="paper full-text manifest unchanged; no-op",
                ),
            )

        revision = {
            "run_id": run_id,
            "manifest": str(self.assets_manifest),
            "manifest_fingerprint": manifest_fingerprint,
        }
        facts: list[NodeFact | EdgeFact] = []
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
            record_key = str(record.get("asset_id") or record.get("paper_id"))
            record_facts, emission, record_stats = self._record_facts(record, revision)
            facts.extend(record_facts)
            emissions[record_key] = emission
            for key, value in record_stats.items():
                stats[key] = stats.get(key, 0) + value

        self.last_run_stats = stats
        record_set = self._record_set(emissions, revision=revision) if completed_scope else None
        return SourceRun(
            facts=iter(facts),
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
                    f"manifest row must be an object: {self.assets_manifest}:{line_no}",
                    data={"line_no": line_no},
                )
            out.append(raw)
        out.sort(key=lambda r: (str(r.get("venue_id") or ""), int(r.get("year") or 0), str(r.get("paper_id") or "")))
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
        paper_id = str(record.get("paper_id") or "")
        asset_id = str(record.get("asset_id") or f"document_asset:paper-fulltext:{_safe(paper_id)}")
        source_record_id = {"paper_id": paper_id, "asset_id": asset_id}
        available = bool(record.get("available"))
        stats = {
            "available_records": 1 if available else 0,
            "unavailable_records": 0 if available else 1,
            "documents": 0,
            "chunks": 0,
            "parse_failures": 0,
        }
        facts: list[NodeFact | EdgeFact] = []
        title = str(record.get("title") or paper_id)
        venue = record.get("venue_id")
        year = record.get("year")
        asset_attrs = {
            "asset_id": asset_id,
            "asset_kind": "paper_full_text" if available else record.get("asset_kind"),
            "url": record.get("source_url"),
            "access_basis": record.get("access_basis"),
            "source": record.get("source") or "paper_cut",
            "downloaded": available,
            "paper_id": paper_id,
            "source_pack": self.source_pack,
            "title": title,
            "venue_id": venue,
            "year": year,
            "doi": record.get("doi"),
            "local_path": record.get("local_path"),
            "content_sha256": record.get("content_sha256"),
            "byte_count": record.get("byte_count"),
            "mime_type": record.get("mime_type"),
            "acquisition_state": record.get("acquisition_state"),
            "text": " ".join(str(x) for x in [title, venue, year, record.get("source_url")] if x),
        }
        facts.append(_node(asset_id, "document_asset", asset_attrs, source_record_id, revision))
        emission: dict[str, Any] = {
            "asset_id": asset_id,
            "document_id": None,
            "chunks": [],
            "edges": [],
        }
        if not available or not record.get("local_path"):
            return facts, emission, stats

        path = (self.repo_root / str(record["local_path"])).resolve()
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
        doc_id = f"doc:paper-fulltext:{_safe(asset_id)}:{text_hash[:16]}"
        doc_attrs = {
            "doc_id": doc_id,
            "repo": "paper_fulltext",
            "path": str(record.get("local_path")),
            "format": fmt,
            "byte_count": record.get("byte_count") or path.stat().st_size,
            "content_sha256": record.get("content_sha256"),
            "text_sha256": text_hash,
            "parse_warnings": warnings,
            "title": title,
            "paper_id": paper_id,
            "document_asset_id": asset_id,
            "source_pack": self.source_pack,
            "venue_id": venue,
            "year": year,
            "doi": record.get("doi"),
            "abstract": record.get("abstract"),
            "text": f"{title}\n\n{text[:4000]}",
        }
        facts.append(_node(doc_id, "document", doc_attrs, source_record_id, revision))
        emission["document_id"] = doc_id
        stats["documents"] += 1

        for index, (offset, chunk_text) in enumerate(
            _chunks(text, max_chars=self.chunk_max_chars, overlap=self.chunk_overlap)
        ):
            chunk_hash = _hash_text(f"{paper_id}|{asset_id}|{index}|{chunk_text}")
            chunk_id = f"chunk:paper-fulltext:{chunk_hash[:20]}"
            chunk_source_record_id = {
                "paper_id": paper_id,
                "asset_id": asset_id,
                "chunk_index": index,
            }
            chunk_attrs = {
                "chunk_id": chunk_id,
                "text": chunk_text,
                "char_offset": offset,
                "char_length": len(chunk_text),
                "content_sha256": _hash_text(chunk_text),
                "chunker_name": "paper_fulltext_window",
                "chunk_index": index,
                "paper_id": paper_id,
                "document_id": doc_id,
                "document_asset_id": asset_id,
                "source_pack": self.source_pack,
                "title": title,
                "venue_id": venue,
                "year": year,
                "doi": record.get("doi"),
            }
            facts.append(_node(chunk_id, "document_chunk", chunk_attrs, chunk_source_record_id, revision))
            facts.append(_edge(doc_id, "contains", chunk_id, chunk_source_record_id, revision))
            facts.append(_edge(chunk_id, "member_of", doc_id, chunk_source_record_id, revision))
            emission["chunks"].append(chunk_id)
            emission["edges"].extend(
                [
                    {
                        "src": doc_id,
                        "dst": chunk_id,
                        "edge_type": "contains",
                        "source_record_id": chunk_source_record_id,
                    },
                    {
                        "src": chunk_id,
                        "dst": doc_id,
                        "edge_type": "member_of",
                        "source_record_id": chunk_source_record_id,
                    },
                ]
            )
            stats["chunks"] += 1
        return facts, emission, stats

    @staticmethod
    def _record_set(
        emissions: dict[str, dict[str, Any]],
        *,
        revision: dict[str, Any],
    ) -> RecordSet:
        records: dict[str, RecordEmission] = {}
        for record_key, emitted in emissions.items():
            source_record_id = {"record_key": record_key}
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
                        source_record_id={"record_key": record_key, "chunk_id": chunk_id},
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


__all__ = ["PaperFulltextDocumentsSource"]
