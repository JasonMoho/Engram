"""Manifest-backed Cloudcast design-knowledge facts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

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


def _node_id(subtype: str, problem_name: str, local_id: str) -> str:
    return f"{subtype}:{problem_name}:{local_id}"


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


@dataclass
class CloudcastFactsSource:
    """Emit curated Cloudcast systems-research facts.

    This source is deliberately manifest-backed and deterministic. It is
    the first bridge from the Cloudcast benchmark into the systems
    research ontology: design principles, mechanisms, trade-offs,
    anti-patterns, and evidence nodes.
    """

    name: str = "cloudcast_facts"
    profile: str = "discovery_crawl"
    facts_path: Path | str = ""

    def run(self, run_id: str, *, mode: str = "cursor") -> SourceRun:
        path = Path(self.facts_path)
        if not path.is_file():
            raise SubstrateError(
                f"Cloudcast facts manifest not found: {path}",
                data={"facts_path": str(path)},
            )
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(doc, dict):
            raise SubstrateError(
                f"Cloudcast facts manifest must be a mapping: {path}",
                data={"facts_path": str(path)},
            )
        revision = {"content_hash": _sha(doc), "path": str(path)}
        facts = list(self._facts(doc, revision))
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
                    f"design_principles={len(doc.get('design_principles') or [])} "
                    f"mechanisms={len(doc.get('mechanisms') or [])} "
                    f"trade_offs={len(doc.get('trade_offs') or [])} "
                    f"anti_patterns={len(doc.get('anti_patterns') or [])} "
                    f"evidence={len(doc.get('evidence') or [])}"
                ),
            ),
        )

    @staticmethod
    def _record_set_from_facts(
        facts: list[NodeFact | EdgeFact],
    ) -> RecordSet:
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
        doc: dict[str, Any],
        revision: dict[str, Any],
    ) -> Iterable[NodeFact | EdgeFact]:
        problem_name = str(doc.get("problem_name") or "cloudcast")
        domain = str(doc.get("domain") or "networking")
        default_topics = list(doc.get("topic_slugs") or [])
        now = str(doc.get("generated_at") or "2026-05-20T00:00:00Z")

        local_to_node: dict[tuple[str, str], str] = {}

        def common(item: dict[str, Any]) -> dict[str, Any]:
            topics = list(item.get("topic_slugs") or default_topics)
            return {
                "problem_name": problem_name,
                "domain": domain,
                "topic_slugs": topics,
                "strength": item.get("strength") or "moderate",
                "evidence_ids": list(item.get("evidence_ids") or []),
                "observed_at": item.get("observed_at") or now,
                "created_at": item.get("created_at") or now,
                "last_modified_at": item.get("last_modified_at") or now,
                "source_note": doc.get("source_note"),
            }

        for item in doc.get("evidence") or []:
            local_id = str(item["id"])
            node_id = _node_id("generic_evidence", problem_name, local_id)
            local_to_node[("evidence", local_id)] = node_id
            attrs = {
                **common(item),
                "evidence_id": node_id,
                "kind": item.get("kind") or "observation",
                "statement": item.get("statement"),
                "rationale": item.get("rationale"),
                "source_path": item.get("source_path") or revision["path"],
                "source_subtype": "memex_sr_cloudcast_fact_seed",
                "hypothesis_ref": f"cloudcast:{local_id}",
                "observation_ref": f"cloudcast:{local_id}",
                "support_polarity": "supports",
                "frontmatter_schema_version": 1,
            }
            attrs["text"] = _text(attrs, ["kind", "statement", "rationale", "source_path"])
            yield _node(node_id, "generic_evidence", attrs, revision)

        for item in doc.get("design_principles") or []:
            local_id = str(item["id"])
            node_id = _node_id("design_principle", problem_name, local_id)
            local_to_node[("design_principle", local_id)] = node_id
            attrs = {
                **common(item),
                "statement": item.get("statement"),
                "why_it_matters": item.get("why_it_matters"),
            }
            attrs["text"] = _text(attrs, ["statement", "why_it_matters", "domain"])
            yield _node(node_id, "design_principle", attrs, revision)

        for item in doc.get("mechanisms") or []:
            local_id = str(item["id"])
            node_id = _node_id("mechanism", problem_name, local_id)
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

        for item in doc.get("trade_offs") or []:
            local_id = str(item["id"])
            node_id = _node_id("trade_off", problem_name, local_id)
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

        for item in doc.get("anti_patterns") or []:
            local_id = str(item["id"])
            node_id = _node_id("anti_pattern", problem_name, local_id)
            local_to_node[("anti_pattern", local_id)] = node_id
            attrs = {
                **common(item),
                "approach": item.get("approach"),
                "why_it_tends_to_fail": item.get("why_it_tends_to_fail"),
            }
            attrs["text"] = _text(attrs, ["approach", "why_it_tends_to_fail"])
            yield _node(node_id, "anti_pattern", attrs, revision)

        for item in doc.get("mechanisms") or []:
            mechanism_id = local_to_node.get(("mechanism", str(item["id"])))
            if mechanism_id is None:
                continue
            for principle in item.get("instantiates") or []:
                principle_id = local_to_node.get(("design_principle", str(principle)))
                if principle_id is not None:
                    yield _edge(mechanism_id, "instantiates", principle_id, revision)

        for item in doc.get("trade_offs") or []:
            trade_off_id = local_to_node.get(("trade_off", str(item["id"])))
            if trade_off_id is None:
                continue
            for mechanism in item.get("restricts") or []:
                mechanism_id = local_to_node.get(("mechanism", str(mechanism)))
                if mechanism_id is not None:
                    yield _edge(trade_off_id, "restricts", mechanism_id, revision)

        for item in doc.get("anti_patterns") or []:
            anti_pattern_id = local_to_node.get(("anti_pattern", str(item["id"])))
            if anti_pattern_id is None:
                continue
            for mechanism in item.get("mitigated_by") or []:
                mechanism_id = local_to_node.get(("mechanism", str(mechanism)))
                if mechanism_id is not None:
                    yield _edge(anti_pattern_id, "mitigated_by", mechanism_id, revision)
