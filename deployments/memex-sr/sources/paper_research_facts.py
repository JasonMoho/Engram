"""Manifest-backed systems-research facts extracted from full-text papers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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


def _sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _node_suffix(*parts: Any) -> str:
    return hashlib.sha256(
        json.dumps(parts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]


def _node_id(subtype: str, paper_id: str, local_id: str, payload: Any) -> str:
    return f"{subtype}:paper-fulltext:{_node_suffix(paper_id, local_id, payload)}"


def _node(
    node_id: str,
    subtype: str,
    attrs: dict[str, Any],
    revision: dict[str, Any],
) -> NodeFact:
    return NodeFact(
        node_id=node_id,
        subtype=subtype,
        attrs=attrs,
        source_record_id={"id": node_id},
        source_revision=revision,
    )


def _edge(
    src: str,
    edge_type: str,
    dst: str,
    revision: dict[str, Any],
    attrs: dict[str, Any] | None = None,
) -> EdgeFact:
    return EdgeFact(
        src=src,
        dst=dst,
        edge_type=edge_type,
        attrs=attrs or {},
        source_record_id={"edge": f"{src}|{edge_type}|{dst}"},
        source_revision=revision,
    )


def _text(attrs: dict[str, Any], keys: Iterable[str]) -> str:
    return " ".join(str(attrs.get(key) or "") for key in keys).strip()


def _records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SubstrateError(
                f"Invalid paper research facts JSONL at line {line_no}: {path}",
                data={"facts_manifest": str(path), "line": line_no},
            ) from exc
        if not isinstance(record, dict):
            raise SubstrateError(
                f"Paper research facts JSONL line must be an object: {path}:{line_no}",
                data={"facts_manifest": str(path), "line": line_no},
            )
        records.append(record)
    return records


def _compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


@dataclass
class PaperResearchFactsSource:
    """Emit paper-derived systems-research facts from an extraction manifest."""

    name: str = "paper_research_facts"
    profile: str = "discovery_crawl"
    facts_manifest: Path | str = ""

    def run(self, run_id: str, *, mode: str = "cursor") -> SourceRun:
        path = Path(self.facts_manifest)
        if not path.is_file():
            raise SubstrateError(
                f"Paper research facts manifest not found: {path}",
                data={"facts_manifest": str(path)},
            )
        records = _records(path)
        revision = {
            "content_hash": _sha(records),
            "path": str(path),
        }
        facts = list(self._facts(records, revision))
        counts = self._counts(records)
        return SourceRun(
            facts=facts,
            completed_scope=True,
            run_mode=mode,
            record_set=self._record_set_from_facts(facts),
            health=SourceHealth(
                status="ok",
                mode="manifest",
                record_count=sum(1 for fact in facts if isinstance(fact, NodeFact)),
                content_hash=revision["content_hash"],
                cache_path=str(path),
                reason=(
                    f"papers={len(records)} evidence={counts['evidence']} "
                    f"design_principles={counts['design_principles']} "
                    f"mechanisms={counts['mechanisms']} "
                    f"trade_offs={counts['trade_offs']} "
                    f"anti_patterns={counts['anti_patterns']}"
                ),
            ),
        )

    @staticmethod
    def _counts(records: list[dict[str, Any]]) -> dict[str, int]:
        keys = ("evidence", "design_principles", "mechanisms", "trade_offs", "anti_patterns")
        return {
            key: sum(len(record.get(key) or []) for record in records)
            for key in keys
        }

    @staticmethod
    def _record_set_from_facts(facts: list[NodeFact | EdgeFact]) -> RecordSet:
        records: dict[str, RecordEmission] = {}
        nodes: dict[str, NodeFact] = {
            fact.node_id: fact
            for fact in facts
            if isinstance(fact, NodeFact)
        }
        for node in nodes.values():
            records[node.node_id] = RecordEmission(
                primary=RecordNode(
                    node_id=node.node_id,
                    subtype=node.subtype,
                    source_record_id=node.source_record_id,
                    source_revision=node.source_revision,
                )
            )
        for edge in (fact for fact in facts if isinstance(fact, EdgeFact)):
            record_key = edge.src if edge.src in nodes else edge.dst
            records.setdefault(record_key, RecordEmission()).edges.append(
                EdgeKey(
                    src=edge.src,
                    dst=edge.dst,
                    edge_type=edge.edge_type,
                    attrs=edge.attrs,
                    provenance=edge.provenance,
                    confidence=edge.confidence,
                    source_record_id=edge.source_record_id,
                    source_revision=edge.source_revision,
                )
            )
        return RecordSet(records=records)

    def _facts(
        self,
        records: list[dict[str, Any]],
        revision: dict[str, Any],
    ) -> Iterable[NodeFact | EdgeFact]:
        for record in records:
            yield from self._record_facts(record, revision)

    def _record_facts(
        self,
        record: dict[str, Any],
        revision: dict[str, Any],
    ) -> Iterable[NodeFact | EdgeFact]:
        paper_id = str(record.get("paper_id") or "")
        if not paper_id:
            return
        document_id = str(record.get("document_id") or "")
        source_chunk_ids = list(record.get("source_chunk_ids") or [])
        created_at = str(record.get("extracted_at") or "2026-05-20T00:00:00+00:00")
        domain = str(record.get("domain") or "other")
        local_to_node: dict[tuple[str, str], str] = {}

        def common(item: dict[str, Any]) -> dict[str, Any]:
            chunk_ids = list(item.get("source_chunk_ids") or [])
            if item.get("source_chunk_id"):
                chunk_ids.append(item["source_chunk_id"])
            if not chunk_ids:
                chunk_ids.extend(source_chunk_ids[:2])
            return {
                "domain": item.get("domain") or domain,
                "topic_slugs": list(item.get("topic_slugs") or []),
                "strength": item.get("strength") or "moderate",
                "evidence_ids": [
                    local_to_node[("evidence", str(ref))]
                    for ref in item.get("evidence_ids") or []
                    if ("evidence", str(ref)) in local_to_node
                ],
                "source_paper_id": paper_id,
                "source_document_id": document_id,
                "source_chunk_ids": chunk_ids,
                "source_title": record.get("title"),
                "source_venue_id": record.get("venue_id"),
                "source_year": record.get("year"),
                "extractor": record.get("extractor"),
                "model": record.get("model"),
                "created_at": created_at,
                "last_modified_at": created_at,
                "observed_at": created_at,
                "source_note": "paper_research_fact_extraction",
            }

        for item in record.get("evidence") or []:
            if not isinstance(item, dict):
                continue
            local_id = str(item.get("id") or _node_suffix(paper_id, item))
            node_id = _node_id("generic_evidence", paper_id, local_id, item)
            local_to_node[("evidence", local_id)] = node_id
            attrs = {
                **common(item),
                "evidence_id": node_id,
                "kind": item.get("kind") or "paper_extraction",
                "statement": item.get("statement"),
                "rationale": item.get("rationale"),
                "source_path": f"{paper_id}#{item.get('source_chunk_id') or document_id}",
                "source_subtype": "paper_research_extraction",
                "hypothesis_ref": f"paper-fact:{node_id}",
                "observation_ref": item.get("source_chunk_id") or document_id or paper_id,
                "support_polarity": "supports",
                "frontmatter_schema_version": 1,
            }
            attrs["text"] = _text(attrs, ["kind", "statement", "rationale", "source_path"])
            yield _node(node_id, "generic_evidence", attrs, revision)

        for item in record.get("design_principles") or []:
            if not isinstance(item, dict):
                continue
            local_id = str(item.get("id") or _node_suffix(paper_id, item))
            node_id = _node_id("design_principle", paper_id, local_id, item)
            local_to_node[("design_principle", local_id)] = node_id
            attrs = {
                **common(item),
                "statement": item.get("statement"),
                "why_it_matters": item.get("why_it_matters"),
            }
            attrs["text"] = _text(attrs, ["statement", "why_it_matters", "domain"])
            yield _node(node_id, "design_principle", attrs, revision)
            yield _edge(
                node_id,
                "emerged_from",
                paper_id,
                revision,
                {"source": "paper_research_fact_extraction"},
            )

        for item in record.get("mechanisms") or []:
            if not isinstance(item, dict):
                continue
            local_id = str(item.get("id") or _node_suffix(paper_id, item))
            node_id = _node_id("mechanism", paper_id, local_id, item)
            local_to_node[("mechanism", local_id)] = node_id
            attrs = {
                **common(item),
                "name": item.get("name"),
                "mechanism_kind": item.get("mechanism_kind") or "other",
                "applicability": item.get("applicability"),
                "known_limits": item.get("known_limits"),
            }
            attrs["text"] = _text(attrs, ["name", "mechanism_kind", "applicability", "known_limits"])
            yield _node(node_id, "mechanism", attrs, revision)
            yield _edge(
                node_id,
                "cited_in",
                paper_id,
                revision,
                {"source": "paper_research_fact_extraction"},
            )

        for item in record.get("trade_offs") or []:
            if not isinstance(item, dict):
                continue
            local_id = str(item.get("id") or _node_suffix(paper_id, item))
            node_id = _node_id("trade_off", paper_id, local_id, item)
            local_to_node[("trade_off", local_id)] = node_id
            attrs = {
                **common(item),
                "objective_a": item.get("objective_a"),
                "objective_b": item.get("objective_b"),
                "tension": item.get("tension"),
                "failure_modes": item.get("failure_modes"),
            }
            attrs["text"] = _text(attrs, ["objective_a", "objective_b", "tension", "failure_modes"])
            yield _node(node_id, "trade_off", attrs, revision)

        for item in record.get("anti_patterns") or []:
            if not isinstance(item, dict):
                continue
            local_id = str(item.get("id") or _node_suffix(paper_id, item))
            node_id = _node_id("anti_pattern", paper_id, local_id, item)
            local_to_node[("anti_pattern", local_id)] = node_id
            attrs = {
                **common(item),
                "approach": item.get("approach"),
                "why_it_tends_to_fail": item.get("why_it_tends_to_fail"),
            }
            attrs["text"] = _text(attrs, ["approach", "why_it_tends_to_fail"])
            yield _node(node_id, "anti_pattern", attrs, revision)

        for item in record.get("mechanisms") or []:
            mechanism_id = local_to_node.get(("mechanism", str(item.get("id"))))
            if mechanism_id is None:
                continue
            for principle in item.get("instantiates") or []:
                principle_id = local_to_node.get(("design_principle", str(principle)))
                if principle_id is not None:
                    yield _edge(mechanism_id, "instantiates", principle_id, revision)

        for item in record.get("trade_offs") or []:
            trade_off_id = local_to_node.get(("trade_off", str(item.get("id"))))
            if trade_off_id is None:
                continue
            for mechanism in item.get("restricts") or []:
                mechanism_id = local_to_node.get(("mechanism", str(mechanism)))
                if mechanism_id is not None:
                    yield _edge(trade_off_id, "restricts", mechanism_id, revision)

        for item in record.get("anti_patterns") or []:
            anti_pattern_id = local_to_node.get(("anti_pattern", str(item.get("id"))))
            if anti_pattern_id is None:
                continue
            for mechanism in item.get("mitigated_by") or []:
                mechanism_id = local_to_node.get(("mechanism", str(mechanism)))
                if mechanism_id is not None:
                    yield _edge(anti_pattern_id, "mitigated_by", mechanism_id, revision)
