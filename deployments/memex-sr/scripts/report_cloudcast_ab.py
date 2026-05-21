#!/usr/bin/env python3
"""Build a Cloudcast comparison report from Engram and Codex run dirs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def latest_child(path: Path) -> Path | None:
    if not path.exists():
        return None
    children = [p for p in path.iterdir() if p.is_dir()]
    if not children:
        return None
    return max(children, key=lambda p: p.stat().st_mtime)


def inferred_cost(score: Any) -> float | None:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return (1.0 / value) - 1.0


def fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"


def find_handoff_result(run_dir: Path) -> Path | None:
    candidates = sorted(run_dir.glob("*/logs/*-agentic_handoff_*iterations.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_engram_run(run_dir: Path) -> dict[str, Any]:
    result_path = find_handoff_result(run_dir)
    result = load_json(result_path) if result_path else {}
    config = load_json(run_dir / "benchmark_run_config.json")
    usage_path = None
    if result_path:
        usage_candidates = sorted(result_path.parent.glob("*-agentic_handoff_*iterations_usage_stats.json"))
        usage_path = max(usage_candidates, key=lambda p: p.stat().st_mtime) if usage_candidates else None
    usage = load_json(usage_path) if usage_path else result.get("usage_stats", {})

    best_solution = result.get("best_solution") if isinstance(result.get("best_solution"), dict) else {}
    score = best_solution.get("score")
    try:
        score_value = float(score)
    except (TypeError, ValueError):
        score_value = None
    if score_value is not None and not math.isfinite(score_value):
        score_value = None

    agent_histories = result.get("agent_histories") if isinstance(result.get("agent_histories"), list) else []
    elapsed_seconds = sum(float(h.get("elapsed_minutes") or 0.0) * 60.0 for h in agent_histories if isinstance(h, dict))
    okg_context = config.get("okg_context") if isinstance(config.get("okg_context"), dict) else {}

    return {
        "arm": config.get("arm") or ("engram_okg_context" if okg_context else "engram_control"),
        "comparison_type": config.get("comparison_type") or "engram_benchmark_arm",
        "agent_family": "engram_handoff",
        "result_dir": str(run_dir),
        "result_file": str(result_path) if result_path else None,
        "success": bool(score_value is not None and score_value > 0),
        "best_score": score_value,
        "inferred_total_cost": inferred_cost(score_value),
        "total_simulations": result.get("total_simulations"),
        "evaluation_calls": result.get("total_simulations"),
        "elapsed_seconds": elapsed_seconds if elapsed_seconds else None,
        "model": config.get("model"),
        "runtime_model": config.get("runtime_model"),
        "provider": (config.get("model_metadata") or {}).get("provider"),
        "usage_cost_dollars": usage.get("total_cost"),
        "okg_generation_id": okg_context.get("okg_generation_id"),
        "okg_context_hash": okg_context.get("okg_context_hash"),
    }


def parse_codex_run(run_dir: Path) -> dict[str, Any]:
    final = load_json(run_dir / "final_evaluation.json")
    metadata = load_json(run_dir / "metadata.json")
    codex_run = load_json(run_dir / "codex_run.json")
    mcp_usage = load_json(run_dir / "mcp_usage_summary.json")
    state = load_json(run_dir / "workspace" / "evaluation_state.json")
    okg_mcp = metadata.get("okg_mcp") if isinstance(metadata.get("okg_mcp"), dict) else {}

    score = final.get("score") if "score" in final else final.get("combined_score")
    return {
        "arm": metadata.get("arm") or final.get("arm") or "codex_cli_gpt55_high",
        "comparison_type": metadata.get("comparison_type") or final.get("comparison_type") or "fair_out_of_box_baseline",
        "agent_family": "codex_cli",
        "result_dir": str(run_dir),
        "result_file": str(run_dir / "final_evaluation.json"),
        "success": final.get("success"),
        "best_score": score,
        "inferred_total_cost": final.get("inferred_total_cost") or inferred_cost(score),
        "total_simulations": None,
        "evaluation_calls": state.get("attempts"),
        "elapsed_seconds": codex_run.get("elapsed_seconds") or final.get("elapsed_seconds"),
        "model": metadata.get("model"),
        "runtime_model": metadata.get("model"),
        "provider": "codex_cli",
        "usage_cost_dollars": None,
        "okg_generation_id": okg_mcp.get("latest_published_generation"),
        "okg_context_hash": None,
        "okg_mcp_attempted_calls": mcp_usage.get("attempted_calls"),
        "okg_mcp_successful_calls": mcp_usage.get("successful_calls"),
        "okg_mcp_failed_calls": mcp_usage.get("failed_calls"),
    }


def build_markdown(rows: list[dict[str, Any]]) -> str:
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Cloudcast A/B Smoke Comparison",
        "",
        f"Generated: `{now}`",
        "",
        "This report separates Engram arms from the Codex CLI baseline. "
        "Codex is a fair out-of-box baseline, not a strict Engram architecture ablation.",
        "",
        "| Arm | Family | Success | Score | Inferred cost | Eval calls | Elapsed s | Model | OKG gen | OKG MCP calls | Result dir |",
        "|:--|:--|:--|--:|--:|--:|--:|:--|:--|:--|:--|",
    ]
    for row in rows:
        lines.append(
            "| {arm} | {family} | {success} | {score} | {cost} | {evals} | {elapsed} | {model} | {gen} | {mcp_calls} | `{result_dir}` |".format(
                arm=row.get("arm") or "n/a",
                family=row.get("agent_family") or row.get("comparison_type") or "n/a",
                success=fmt(row.get("success"), 0),
                score=fmt(row.get("best_score"), 12),
                cost=fmt(row.get("inferred_total_cost"), 6),
                evals=fmt(row.get("evaluation_calls"), 0),
                elapsed=fmt(row.get("elapsed_seconds"), 1),
                model=row.get("model") or "n/a",
                gen=row.get("okg_generation_id") or "n/a",
                mcp_calls=(
                    f"{row.get('okg_mcp_successful_calls') or 0}/{row.get('okg_mcp_attempted_calls') or 0}"
                    if row.get("okg_mcp_attempted_calls") is not None
                    else "n/a"
                ),
                result_dir=row.get("result_dir") or "n/a",
            )
        )

    codex_rows = [r for r in rows if r.get("agent_family") == "codex_cli"]
    engram_rows = [r for r in rows if r.get("agent_family") == "engram_handoff"]
    lines.extend(["", "## Readout", ""])
    if codex_rows:
        best_codex = max(codex_rows, key=lambda r: float(r.get("best_score") or 0.0))
        lines.append(
            f"- Best Codex smoke score: `{fmt(best_codex.get('best_score'), 12)}` "
            f"(cost `{fmt(best_codex.get('inferred_total_cost'), 6)}`)."
        )
    if engram_rows:
        best_engram = max(engram_rows, key=lambda r: float(r.get("best_score") or 0.0))
        lines.append(
            f"- Best Engram smoke score: `{fmt(best_engram.get('best_score'), 12)}` "
            f"(cost `{fmt(best_engram.get('inferred_total_cost'), 6)}`)."
        )
    else:
        lines.append("- No Engram run directories were supplied to this report.")

    lines.extend(
        [
            "",
            "## Contamination Notes",
            "",
            "- Fair Engram control runs should omit `--give_files`.",
            "- OKG-context runs should record `okg_context_hash` and `okg_generation_id` in `benchmark_run_config.json`.",
            "- Codex baseline workspaces exclude `optimal.py`, `task_prompt_direction_with_optimal.txt`, and OKG context packets.",
            "- Codex+OKG-MCP runs may query bounded graph tools, but their workspaces still exclude oracle files and pre-rendered OKG packets.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engram-dir", action="append", default=[], help="Engram result directory to include.")
    parser.add_argument("--codex-dir", action="append", default=[], help="Codex baseline result directory to include.")
    parser.add_argument(
        "--codex-root",
        default=str(root / "results" / "codex_baseline_cloudcast"),
        help="Root used to auto-select the latest Codex baseline when --codex-dir is omitted.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "deployments" / "memex-sr" / "reports" / "cloudcast-ab" / "smoke-comparison.md"),
    )
    parser.add_argument("--json-output", default=None, help="Optional JSON rows output.")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    codex_dirs = [Path(p).resolve() for p in args.codex_dir]
    if not codex_dirs:
        latest_codex = latest_child(Path(args.codex_root).resolve())
        if latest_codex:
            codex_dirs.append(latest_codex)

    for path in codex_dirs:
        rows.append(parse_codex_run(path))
    for path_str in args.engram_dir:
        rows.append(parse_engram_run(Path(path_str).resolve()))

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(rows), encoding="utf-8")

    if args.json_output:
        json_output = Path(args.json_output).resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
