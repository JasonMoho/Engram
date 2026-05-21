#!/usr/bin/env python3
"""Generate a Cloudcast OKG context packet for Engram benchmark runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg

from okg.substrate.library.ontologies.reasoning.derived_artifacts.context_packet import run_context_packet


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def latest_published_generation(conn: psycopg.Connection[Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            select generation_id
            from okg.graph_generations
            where status = 'published'
            order by generation_id desc
            limit 1
            """
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError("No published OKG generation found")
    return int(row[0])


def evidence_ids_from_sections(sections: dict[str, Any]) -> list[str]:
    evidence_ids: set[str] = set()
    for rows in sections.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            node_id = row.get("node_id")
            if isinstance(node_id, str) and node_id:
                evidence_ids.add(node_id)
            linked = row.get("evidence_ids")
            if isinstance(linked, list):
                evidence_ids.update(str(item) for item in linked if item)
    return sorted(evidence_ids)


def main() -> int:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.environ.get("MEMEX_SR_OKG_DSN") or "postgres://postgres:okg@localhost:5433/engram_memex_sr_phase0",
    )
    parser.add_argument("--generation-id", default="latest", help="Published generation id or 'latest'.")
    parser.add_argument("--problem-name", default="cloudcast")
    parser.add_argument("--domain", default="networking")
    parser.add_argument(
        "--topic-slug",
        action="append",
        default=None,
        help="Topic slug to query. May be supplied multiple times.",
    )
    parser.add_argument("--evidence-budget", type=int, default=20)
    parser.add_argument("--token-budget", type=int, default=4000)
    parser.add_argument(
        "--output",
        default=str(root / "deployments" / "memex-sr" / "reports" / "cloudcast-ab" / "context-packet.md"),
    )
    parser.add_argument("--metadata-output", default=None)
    args = parser.parse_args()

    topic_slugs = args.topic_slug or ["multicast", "routing", "traffic-engineering", "cost-aware-routing"]

    with psycopg.connect(args.dsn) as conn:
        generation_id = latest_published_generation(conn) if args.generation_id == "latest" else int(args.generation_id)
        result = run_context_packet(
            conn,
            problem_name=args.problem_name,
            domain=args.domain,
            topic_slugs=topic_slugs,
            generation_id=generation_id,
            evidence_budget=args.evidence_budget,
            token_budget=args.token_budget,
        )

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.markdown, encoding="utf-8")

    sections = {name: list(rows) for name, rows in result.sections.items()}
    metadata = {
        "artifact_type": "okg/context-packet-v1",
        "definition_id": result.definition_id,
        "problem_name": args.problem_name,
        "domain": args.domain,
        "topic_slugs": topic_slugs,
        "generation_id": generation_id,
        "evidence_budget": args.evidence_budget,
        "token_budget": args.token_budget,
        "estimated_tokens": result.estimated_tokens,
        "trimmed": result.trimmed,
        "packet_path": str(output),
        "packet_hash": sha256_text(result.markdown),
        "evidence_ids": evidence_ids_from_sections(sections),
        "section_counts": {name: len(rows) for name, rows in sections.items()},
        "inputs": dict(result.inputs),
    }

    metadata_output = Path(args.metadata_output).resolve() if args.metadata_output else output.with_suffix(".metadata.json")
    metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    print(output)
    print(metadata_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
