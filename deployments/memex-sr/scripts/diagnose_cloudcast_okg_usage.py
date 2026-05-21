#!/usr/bin/env python3
"""Diagnose whether a Cloudcast OKG run actually used graph evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "results" / "codex_okg_mcp_cloudcast"
DEFAULT_DSN = "postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke"
DEFAULT_REPORT = (
    REPO_ROOT
    / "deployments"
    / "memex-sr"
    / "reports"
    / "cloudcast-ab"
    / "okg-usage-diagnostic.md"
)
DEFAULT_JSON = DEFAULT_REPORT.with_suffix(".json")

TARGET_SUBTYPES = [
    "document",
    "document_chunk",
    "paper",
    "design_principle",
    "mechanism",
    "trade_off",
    "anti_pattern",
    "generic_evidence",
]

NODE_ID_RE = re.compile(
    r"\b(?:anti_pattern|design_principle|mechanism|trade_off|generic_evidence|"
    r"document|chunk|paper):[A-Za-z0-9_.:-]+\b"
)


def latest_child(path: Path) -> Path:
    children = [p for p in path.iterdir() if p.is_dir()]
    if not children:
        raise SystemExit(f"no result directories found under {path}")
    return max(children, key=lambda p: p.stat().st_mtime)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def walk_json(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_json(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_json(item))
    return values


def extract_node_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    for item in walk_json(value):
        if isinstance(item, dict) and isinstance(item.get("node_id"), str):
            ids.add(item["node_id"])
        elif isinstance(item, str):
            ids.update(NODE_ID_RE.findall(item))
    return ids


def item_type(event: dict[str, Any]) -> str | None:
    item = event.get("item")
    if isinstance(item, dict):
        return item.get("type")
    return None


def item_status(event: dict[str, Any]) -> str | None:
    item = event.get("item")
    if isinstance(item, dict):
        return item.get("status")
    return None


def command_text(event: dict[str, Any]) -> str:
    item = event.get("item")
    if isinstance(item, dict):
        return str(item.get("command") or "")
    return ""


def first_index(indexes: list[int]) -> int | None:
    return min(indexes) if indexes else None


def analyze_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    mcp_calls: list[dict[str, Any]] = []
    agent_message_node_ids: set[str] = set()
    candidate_edit_indexes: list[int] = []
    file_change_indexes: list[int] = []
    evaluation_indexes: list[int] = []

    for index, event in enumerate(events):
        kind = item_type(event)
        item = event.get("item") if isinstance(event.get("item"), dict) else {}

        if kind == "mcp_tool_call" and item_status(event) == "completed":
            result = item.get("result")
            node_ids = extract_node_ids(result)
            mcp_calls.append(
                {
                    "event_index": index,
                    "server": item.get("server"),
                    "tool": item.get("tool"),
                    "arguments": item.get("arguments") or {},
                    "node_ids": sorted(node_ids),
                    "cloudcast_node_ids": sorted(
                        node_id for node_id in node_ids if "cloudcast" in node_id
                    ),
                    "status": item.get("status"),
                    "error": item.get("error"),
                }
            )

        if kind == "agent_message":
            agent_message_node_ids.update(extract_node_ids(item.get("text") or ""))

        if kind == "file_change":
            file_change_indexes.append(index)
            for change in item.get("changes") or []:
                if str(change.get("path") or "").endswith("candidate.py"):
                    candidate_edit_indexes.append(index)

        if kind == "command_execution" and "evaluate_candidate.py candidate.py" in command_text(event):
            evaluation_indexes.append(index)

    retrieved_node_ids = sorted({node_id for call in mcp_calls for node_id in call["node_ids"]})
    retrieved_cloudcast_node_ids = sorted(
        {node_id for call in mcp_calls for node_id in call["cloudcast_node_ids"]}
    )
    tools = Counter(str(call["tool"]) for call in mcp_calls)
    first_mcp = first_index([int(call["event_index"]) for call in mcp_calls])
    first_edit = first_index(candidate_edit_indexes or file_change_indexes)
    first_eval = first_index(evaluation_indexes)
    cited_node_ids = sorted(agent_message_node_ids)
    cited_cloudcast_node_ids = sorted(
        node_id for node_id in cited_node_ids if "cloudcast" in node_id
    )

    evidence_before_edit = (
        first_mcp is not None
        and first_edit is not None
        and first_mcp < first_edit
        and bool(retrieved_cloudcast_node_ids)
    )
    evidence_before_eval = (
        first_mcp is not None
        and first_eval is not None
        and first_mcp < first_eval
        and bool(retrieved_cloudcast_node_ids)
    )
    cited_cloudcast_evidence = bool(cited_cloudcast_node_ids)

    if mcp_calls and not (evidence_before_edit and evidence_before_eval and cited_cloudcast_evidence):
        classification = "okg_attached_but_underused"
    elif mcp_calls:
        classification = "okg_evidence_used"
    else:
        classification = "no_okg_usage"

    return {
        "classification": classification,
        "mcp_call_count": len(mcp_calls),
        "tools": dict(sorted(tools.items())),
        "mcp_calls": mcp_calls,
        "retrieved_node_ids": retrieved_node_ids,
        "retrieved_cloudcast_node_ids": retrieved_cloudcast_node_ids,
        "cited_node_ids": cited_node_ids,
        "cited_cloudcast_node_ids": cited_cloudcast_node_ids,
        "event_indexes": {
            "first_mcp_call": first_mcp,
            "first_candidate_edit": first_edit,
            "first_evaluator_call": first_eval,
        },
        "usage_checks": {
            "retrieved_cloudcast_evidence": bool(retrieved_cloudcast_node_ids),
            "cited_cloudcast_evidence": cited_cloudcast_evidence,
            "evidence_before_first_edit": evidence_before_edit,
            "evidence_before_first_evaluation": evidence_before_eval,
        },
    }


def run_psql_json(dsn: str, sql: str) -> Any:
    proc = subprocess.run(
        ["psql", dsn, "-X", "-q", "-t", "-A", "-c", sql],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = proc.stdout.strip()
    if not payload:
        return None
    return json.loads(payload)


def coverage_snapshot(dsn: str, generation_id: int | None) -> dict[str, Any]:
    pin_stmt = (
        f"SET LOCAL okg.pin_generation='{generation_id}';"
        if generation_id is not None
        else ""
    )
    target_values = ", ".join(f"('{subtype}')" for subtype in TARGET_SUBTYPES)
    sql = f"""
BEGIN;
{pin_stmt}
WITH target(subtype) AS (
  VALUES {target_values}
),
matches AS (
  SELECT subtype, count(*)::int AS count
  FROM okg.v_nodes
  WHERE subtype IN (SELECT subtype FROM target)
    AND (
      attrs->>'problem_name' = 'cloudcast'
      OR lower(coalesce(attrs->>'title', '')) LIKE '%cloudcast%'
      OR lower(coalesce(attrs->>'text', '')) LIKE '%cloudcast%'
      OR lower(coalesce(attrs->>'path', '')) LIKE '%cloudcast%'
      OR lower(coalesce(attrs->>'heading_path', '')) LIKE '%cloudcast%'
      OR (attrs->'topic_slugs') ?| ARRAY[
        'cloudcast',
        'multicast',
        'routing',
        'traffic-engineering',
        'cost-aware-routing',
        'steiner-tree',
        'wide-area-transfer'
      ]
    )
  GROUP BY subtype
),
payload AS (
  SELECT jsonb_build_object(
    'generation_id', current_setting('okg.pin_generation', true),
    'counts', jsonb_object_agg(target.subtype, coalesce(matches.count, 0) ORDER BY target.subtype)
  ) AS data
  FROM target
  LEFT JOIN matches USING (subtype)
)
SELECT data::text FROM payload;
COMMIT;
"""
    return run_psql_json(dsn, sql)


def build_markdown(report: dict[str, Any]) -> str:
    usage = report["usage"]
    final = report.get("final_evaluation") or {}
    metadata = report.get("metadata") or {}
    coverage = report.get("coverage") or {}
    counts = coverage.get("counts") or {}
    lines = [
        "# Cloudcast OKG Usage Diagnostic",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"Result dir: `{report['result_dir']}`",
        f"Classification: `{usage['classification']}`",
        f"OKG generation: `{metadata.get('okg_mcp', {}).get('latest_published_generation') or coverage.get('generation_id') or 'n/a'}`",
        "",
        "## Score",
        "",
        f"- Success: `{final.get('success')}`",
        f"- Score: `{final.get('score') or final.get('combined_score')}`",
        f"- Inferred total cost: `{final.get('inferred_total_cost')}`",
        f"- Evaluation calls: `{report.get('evaluation_state', {}).get('attempts')}`",
        "",
        "## OKG Usage",
        "",
        f"- MCP calls: `{usage['mcp_call_count']}`",
        f"- Tools: `{json.dumps(usage['tools'], sort_keys=True)}`",
        f"- Retrieved Cloudcast node ids: `{len(usage['retrieved_cloudcast_node_ids'])}`",
        f"- Cited Cloudcast node ids in agent messages: `{len(usage['cited_cloudcast_node_ids'])}`",
        f"- Event indexes: `{json.dumps(usage['event_indexes'], sort_keys=True)}`",
        f"- Usage checks: `{json.dumps(usage['usage_checks'], sort_keys=True)}`",
        "",
        "### Retrieved Cloudcast Nodes",
        "",
    ]
    if usage["retrieved_cloudcast_node_ids"]:
        for node_id in usage["retrieved_cloudcast_node_ids"]:
            lines.append(f"- `{node_id}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Coverage Snapshot", "", "| Subtype | Cloudcast-relevant count |", "|:--|--:|"])
    for subtype in TARGET_SUBTYPES:
        lines.append(f"| `{subtype}` | {counts.get(subtype, 0)} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This diagnostic treats attached-but-optional MCP access as insufficient. "
            "A useful OKG-assisted run should retrieve Cloudcast-specific evidence, "
            "cite it in a plan or final reasoning, and do so before coding or evaluator calls.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=None, help="Codex+OKG result directory. Defaults to latest.")
    parser.add_argument("--dsn", default=DEFAULT_DSN)
    parser.add_argument("--generation-id", type=int, default=None)
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve() if args.run_dir else latest_child(DEFAULT_RESULTS_ROOT).resolve()
    metadata = load_json(run_dir / "metadata.json")
    generation_id = args.generation_id
    if generation_id is None:
        okg_mcp = metadata.get("okg_mcp") if isinstance(metadata.get("okg_mcp"), dict) else {}
        generation_id = okg_mcp.get("latest_published_generation")

    events = read_jsonl(run_dir / "codex_events.jsonl")
    report = {
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "result_dir": str(run_dir),
        "metadata": metadata,
        "final_evaluation": load_json(run_dir / "final_evaluation.json"),
        "evaluation_state": load_json(run_dir / "workspace" / "evaluation_state.json"),
        "mcp_usage_summary": load_json(run_dir / "mcp_usage_summary.json"),
        "usage": analyze_events(events),
        "coverage": coverage_snapshot(args.dsn, generation_id),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(report) + "\n", encoding="utf-8")

    json_output = Path(args.json_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(output)
    print(json.dumps({"classification": report["usage"]["classification"], "coverage": report["coverage"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
