#!/usr/bin/env python3
"""Run Codex CLI Cloudcast baseline arms.

The runner creates a clean benchmark workspace, invokes `codex exec`
with the requested model/reasoning controls, optionally injects the
Memex-SR OKG MCP server, and scores the resulting candidate with the
Cloudcast evaluator outside Codex's final message.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any


OKG_MCP_APPROVED_TOOLS = (
    # Keep the Codex benchmark arm on the compact AKMON operator
    # surface. This intentionally hides deployment-specific derived
    # artifact tools such as generate_context_packet while still giving
    # the agent bounded graph access.
    "inspect",
    "search",
    "expand",
    "filter",
    "map",
    "aggregate",
    "propose",
    "query",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def load_cloudcast_evaluator(root: Path):
    evaluator_dir = root / "SystemBench" / "ADRS" / "cloudcast"
    evaluator_file = evaluator_dir / "evaluator.py"
    if str(evaluator_dir) not in sys.path:
        sys.path.insert(0, str(evaluator_dir))
    spec = importlib.util.spec_from_file_location("cloudcast_codex_eval", evaluator_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load evaluator from {evaluator_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate


def normalize_evaluation(raw: dict[str, Any], elapsed_seconds: float) -> dict[str, Any]:
    score = float(raw.get("combined_score") or 0.0)
    total_cost = raw.get("total_cost")
    inferred_total_cost = (1.0 / score - 1.0) if score > 0 else None
    error = raw.get("error") or ""
    runs_successfully = float(raw.get("runs_successfully") or 0.0)
    success = bool(score > 0 and runs_successfully > 0 and not error)
    return {
        "success": success,
        "score": score,
        "combined_score": score,
        "total_cost": total_cost,
        "inferred_total_cost": inferred_total_cost,
        "runs_successfully": runs_successfully,
        "successful_configs": raw.get("successful_configs"),
        "failed_configs": raw.get("failed_configs"),
        "max_transfer_time": raw.get("max_transfer_time"),
        "sim_dir": raw.get("sim_dir"),
        "error": error,
        "elapsed_seconds": elapsed_seconds,
    }


def evaluate_candidate(root: Path, candidate_path: Path, small_test: bool) -> dict[str, Any]:
    evaluate = load_cloudcast_evaluator(root)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    start = time.monotonic()
    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        raw = evaluate(str(candidate_path), small_test=small_test)
    elapsed = time.monotonic() - start
    normalized = normalize_evaluation(raw, elapsed)
    normalized["candidate_path"] = str(candidate_path)
    normalized["candidate_hash"] = sha256_file(candidate_path)
    normalized["raw_results"] = raw
    normalized["stdout_tail"] = stdout_buffer.getvalue()[-8000:]
    normalized["stderr_tail"] = stderr_buffer.getvalue()[-8000:]
    return normalized


def copy_cloudcast_evaluator_bundle(root: Path, workspace: Path) -> dict[str, str]:
    """Copy only the non-oracle files needed by the Cloudcast evaluator."""
    src = root / "SystemBench" / "ADRS" / "cloudcast"
    dst = workspace / "cloudcast_eval"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    files = [
        "evaluator.py",
        "simulator.py",
        "broadcast.py",
        "utils.py",
        "baselines.py",
        "cloudcast_opt.py",
    ]
    for name in files:
        shutil.copy2(src / name, dst / name)

    (dst / "examples" / "config").mkdir(parents=True)
    for config in sorted((src / "examples" / "config").glob("*.json")):
        shutil.copy2(config, dst / "examples" / "config" / config.name)

    shutil.copytree(src / "profiles", dst / "profiles")
    (dst / "simulator_output").mkdir()

    manifest: dict[str, str] = {}
    for path in sorted(p for p in dst.rglob("*") if p.is_file()):
        rel = path.relative_to(workspace).as_posix()
        manifest[rel] = sha256_file(path)
    return manifest


def evaluator_wrapper_source(root: Path, result_dir: Path, max_evals: int, small_test: bool) -> str:
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env python3
        from __future__ import annotations

        import contextlib
        import hashlib
        import importlib.util
        import io
        import json
        import sys
        import time
        from pathlib import Path

        REPO_ROOT = Path({json.dumps(str(root))})
        RESULT_DIR = Path({json.dumps(str(result_dir))})
        WORKSPACE_DIR = Path(__file__).resolve().parent
        MAX_EVALS = {int(max_evals)}
        SMALL_TEST = {str(bool(small_test))}
        STATE_FILE = WORKSPACE_DIR / "evaluation_state.json"
        ATTEMPTS_FILE = WORKSPACE_DIR / "evaluation_attempts.jsonl"


        def sha256_file(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()


        def load_evaluator():
            evaluator_dir = WORKSPACE_DIR / "cloudcast_eval"
            evaluator_file = evaluator_dir / "evaluator.py"
            if str(evaluator_dir) not in sys.path:
                sys.path.insert(0, str(evaluator_dir))
            spec = importlib.util.spec_from_file_location("cloudcast_codex_eval", evaluator_file)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Could not load evaluator from {{evaluator_file}}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.evaluate


        def load_state() -> dict:
            if STATE_FILE.exists():
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return {{"attempts": 0, "max_evals": MAX_EVALS}}


        def save_state(state: dict) -> None:
            STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


        def normalize(raw: dict, elapsed_seconds: float, candidate: Path) -> dict:
            score = float(raw.get("combined_score") or 0.0)
            inferred_total_cost = (1.0 / score - 1.0) if score > 0 else None
            error = raw.get("error") or ""
            runs_successfully = float(raw.get("runs_successfully") or 0.0)
            success = bool(score > 0 and runs_successfully > 0 and not error)
            return {{
                "success": success,
                "score": score,
                "combined_score": score,
                "total_cost": raw.get("total_cost"),
                "inferred_total_cost": inferred_total_cost,
                "runs_successfully": runs_successfully,
                "successful_configs": raw.get("successful_configs"),
                "failed_configs": raw.get("failed_configs"),
                "max_transfer_time": raw.get("max_transfer_time"),
                "sim_dir": raw.get("sim_dir"),
                "error": error,
                "elapsed_seconds": elapsed_seconds,
                "candidate_path": str(candidate),
                "candidate_hash": sha256_file(candidate),
                "small_test": SMALL_TEST,
            }}


        def main() -> int:
            candidate_arg = sys.argv[1] if len(sys.argv) > 1 else "candidate.py"
            candidate = Path(candidate_arg).resolve()
            if not candidate.exists():
                print(json.dumps({{"success": False, "error": f"candidate not found: {{candidate}}"}}))
                return 2

            state = load_state()
            if state.get("attempts", 0) >= MAX_EVALS:
                print(json.dumps({{
                    "success": False,
                    "error": f"evaluation cap reached: {{state.get('attempts')}}/{{MAX_EVALS}}",
                    "attempts": state.get("attempts"),
                    "max_evals": MAX_EVALS,
                }}, indent=2))
                return 3

            state["attempts"] = int(state.get("attempts", 0)) + 1
            state["last_candidate_hash"] = sha256_file(candidate)
            save_state(state)

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            start = time.monotonic()
            try:
                evaluate = load_evaluator()
                with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                    raw = evaluate(str(candidate), small_test=SMALL_TEST)
                elapsed = time.monotonic() - start
                summary = normalize(raw, elapsed, candidate)
                exit_code = 0 if summary["success"] else 1
            except Exception as exc:
                elapsed = time.monotonic() - start
                summary = {{
                    "success": False,
                    "score": 0.0,
                    "combined_score": 0.0,
                    "error": str(exc),
                    "elapsed_seconds": elapsed,
                    "candidate_path": str(candidate),
                    "candidate_hash": sha256_file(candidate),
                    "small_test": SMALL_TEST,
                }}
                exit_code = 1

            summary["attempt"] = state["attempts"]
            summary["stdout_tail"] = stdout_buffer.getvalue()[-4000:]
            summary["stderr_tail"] = stderr_buffer.getvalue()[-4000:]
            with ATTEMPTS_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(summary, sort_keys=True) + "\\n")
            print(json.dumps(summary, indent=2, sort_keys=True))
            return exit_code


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    )


def codex_arm(args: argparse.Namespace) -> str:
    return "codex_cli_gpt55_high_okg_mcp" if args.okg_mcp else "codex_cli_gpt55_high"


def codex_comparison_type(args: argparse.Namespace) -> str:
    return "fair_out_of_box_baseline_with_okg_mcp" if args.okg_mcp else "fair_out_of_box_baseline"


def okg_mcp_command(root: Path, args: argparse.Namespace) -> tuple[str, list[str]]:
    command = shutil.which("uv") or "uv"
    mcp_args = [
        "--directory",
        str(root / "external" / "okg"),
        "run",
        "--extra",
        "mcp",
        "okg",
        "mcp-serve",
        "--dsn",
        args.okg_dsn,
        "--deployment",
        args.okg_deployment,
    ]
    return command, mcp_args


def okg_status_summary(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    command = shutil.which("uv") or "uv"
    cmd = [
        command,
        "--directory",
        str(root / "external" / "okg"),
        "run",
        "--extra",
        "mcp",
        "okg",
        "status",
        "--deployment",
        args.okg_deployment,
        "--dsn",
        args.okg_dsn,
        "--json",
    ]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "command": cmd}

    summary: dict[str, Any] = {
        "ok": proc.returncode == 0,
        "command": cmd,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-4000:],
    }
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        summary["stdout_tail"] = proc.stdout[-4000:]
        return summary

    publishing = payload.get("publishing") if isinstance(payload.get("publishing"), dict) else {}
    live_subtypes = payload.get("live_subtypes") if isinstance(payload.get("live_subtypes"), list) else []
    summary.update(
        {
            "deployment_name": payload.get("deployment_name"),
            "stage": payload.get("stage"),
            "latest_published_generation": publishing.get("latest_published_generation"),
            "latest_catalog_version": publishing.get("latest_catalog_version"),
            "pending_generation": publishing.get("pending_generation"),
            "source_count": len(payload.get("sources") or []),
            "live_subtypes": live_subtypes[:20],
            "errors": payload.get("errors") or [],
        }
    )
    return summary


def okg_mcp_metadata(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    command, mcp_args = okg_mcp_command(root, args)
    status = okg_status_summary(root, args)
    return {
        "enabled": True,
        "server_name": args.okg_mcp_name,
        "dsn": args.okg_dsn,
        "deployment": args.okg_deployment,
        "command": command,
        "args": mcp_args,
        "env": {
            "OKG_DSN": args.okg_dsn,
            "MEMEX_SR_OKG_DSN": args.okg_dsn,
            "OKG_DEPLOYMENTS_DIR": str(root / "deployments"),
            "OKG_AGENT": "1",
            "OKG_MCP_TOOL_SURFACE": "operator",
        },
        "status": status,
        "latest_published_generation": status.get("latest_published_generation"),
        "approved_tools": list(OKG_MCP_APPROVED_TOOLS),
    }


def codex_okg_mcp_config_args(root: Path, args: argparse.Namespace) -> list[str]:
    command, mcp_args = okg_mcp_command(root, args)
    name = args.okg_mcp_name
    config_pairs: list[tuple[str, str]] = [
        (f"mcp_servers.{name}.command", json.dumps(command)),
        (f"mcp_servers.{name}.args", json.dumps(mcp_args)),
        (f"mcp_servers.{name}.startup_timeout_sec", "60"),
        (f"mcp_servers.{name}.env.OKG_DSN", json.dumps(args.okg_dsn)),
        (f"mcp_servers.{name}.env.MEMEX_SR_OKG_DSN", json.dumps(args.okg_dsn)),
        (f"mcp_servers.{name}.env.OKG_DEPLOYMENTS_DIR", json.dumps(str(root / "deployments"))),
        (f"mcp_servers.{name}.env.OKG_AGENT", json.dumps("1")),
        (f"mcp_servers.{name}.env.OKG_MCP_TOOL_SURFACE", json.dumps("operator")),
    ]
    for tool_name in OKG_MCP_APPROVED_TOOLS:
        config_pairs.append((f"mcp_servers.{name}.tools.{tool_name}.approval_mode", json.dumps("approve")))

    cli_args: list[str] = []
    for key, value in config_pairs:
        cli_args.extend(["-c", f"{key}={value}"])
    return cli_args


def summarize_mcp_usage(result_dir: Path, server_name: str) -> dict[str, Any]:
    events_path = result_dir / "codex_events.jsonl"
    summary: dict[str, Any] = {
        "server_name": server_name,
        "events_path": str(events_path),
        "attempted_calls": 0,
        "completed_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "tools": {},
        "errors": [],
    }
    if not events_path.exists():
        summary["missing_events"] = True
        return summary

    for line_number, line in enumerate(events_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            summary.setdefault("parse_errors", []).append({"line": line_number, "error": str(exc)})
            continue

        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if item.get("type") != "mcp_tool_call" or item.get("server") != server_name:
            continue

        tool_name = item.get("tool") or "unknown"
        tool_summary = summary["tools"].setdefault(
            tool_name,
            {"started": 0, "completed": 0, "successful": 0, "failed": 0},
        )
        event_type = event.get("type")
        status = item.get("status")
        if event_type == "item.started":
            summary["attempted_calls"] += 1
            tool_summary["started"] += 1
        elif event_type == "item.completed":
            summary["completed_calls"] += 1
            tool_summary["completed"] += 1
            if status == "failed" or item.get("error"):
                summary["failed_calls"] += 1
                tool_summary["failed"] += 1
                summary["errors"].append(
                    {
                        "line": line_number,
                        "tool": tool_name,
                        "error": item.get("error"),
                    }
                )
            else:
                summary["successful_calls"] += 1
                tool_summary["successful"] += 1

    return summary


def build_task_text(
    fair_prompt: str,
    python_executable: str,
    max_evals: int,
    small_test: bool,
    okg_mcp: bool,
    okg_mcp_name: str,
) -> str:
    mode_note = "This smoke run uses the evaluator's small_test mode." if small_test else "This run uses the full Cloudcast evaluator."
    title = "Cloudcast Codex CLI + OKG MCP" if okg_mcp else "Cloudcast Codex CLI Baseline"
    if okg_mcp:
        okg_rule = "\n        ".join(
            [
                f"- You have access to the `{okg_mcp_name}` MCP server. At the start of the run, call `inspect` with `target={{\"kind\":\"graph\"}}`, then use bounded `search`, `inspect`, `expand`, `filter`, `map`, and `aggregate` calls for relevant Cloudcast concepts.",
                "- Treat OKG output as research guidance with provenance, not ground truth.",
                "- Do not use raw SQL, broad graph dumps, generated context-packet tools, or pre-rendered context packets.",
            ]
        )
    else:
        okg_rule = "- Do not use OKG context, OKG MCP tools, or external literature for this baseline."
    return textwrap.dedent(
        f"""\
        # {title}

        You are running a fair out-of-box Codex benchmark arm for the Cloudcast benchmark.
        Work only in this benchmark workspace.

        Files:
        - `task.md`: this task description.
        - `initial_program.py`: the starting implementation.
        - `candidate.py`: write your final implementation here.
        - `evaluate_candidate.py`: evaluates `candidate.py` with the Cloudcast evaluator.
        - `cloudcast_eval/`: non-oracle evaluator bundle used only by `evaluate_candidate.py`.

        Rules:
        {okg_rule}
        - Do not look for or use `optimal.py` or `task_prompt_direction_with_optimal.txt`.
        - You may use normal Codex CLI behavior inside this workspace: edit files, search files, and run commands.
        - Do not edit files under `cloudcast_eval/`; treat them as the benchmark harness.
        - You have at most {max_evals} evaluation calls. Each invocation of `evaluate_candidate.py` consumes one call.
        - {mode_note}
        - The final scored file must be `candidate.py`.

        Useful commands:

        ```bash
        cp initial_program.py candidate.py
        {python_executable} evaluate_candidate.py candidate.py
        ```

        When done, leave your best implementation in `candidate.py` and briefly summarize what you tried.

        ----

        {fair_prompt}
        """
    )


def prepare_workspace(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    cloudcast_dir = root / "SystemBench" / "ADRS" / "cloudcast"
    fair_prompt_path = cloudcast_dir / "deepagents_files" / "task_prompt_direction.txt"
    initial_program_path = cloudcast_dir / "initial_program.py"
    oracle_paths = [
        cloudcast_dir / "optimal.py",
        cloudcast_dir / "deepagents_files" / "task_prompt_direction_with_optimal.txt",
    ]

    default_root_name = "codex_okg_mcp_cloudcast" if args.okg_mcp else "codex_baseline_cloudcast"
    result_dir = Path(args.results_dir).resolve() if args.results_dir else root / "results" / default_root_name / utc_timestamp()
    workspace = result_dir / "workspace"
    result_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)

    fair_prompt = fair_prompt_path.read_text(encoding="utf-8")
    task_text = build_task_text(
        fair_prompt=fair_prompt,
        python_executable=sys.executable,
        max_evals=args.max_evals,
        small_test=args.small_test,
        okg_mcp=args.okg_mcp,
        okg_mcp_name=args.okg_mcp_name,
    )
    (workspace / "task.md").write_text(task_text, encoding="utf-8")
    shutil.copy2(initial_program_path, workspace / "initial_program.py")
    shutil.copy2(initial_program_path, workspace / "candidate.py")
    evaluator_bundle_manifest = copy_cloudcast_evaluator_bundle(root, workspace)

    eval_wrapper = evaluator_wrapper_source(root, result_dir, args.max_evals, args.small_test)
    eval_path = workspace / "evaluate_candidate.py"
    eval_path.write_text(eval_wrapper, encoding="utf-8")
    eval_path.chmod(0o755)

    metadata = {
        "arm": codex_arm(args),
        "comparison_type": codex_comparison_type(args),
        "created_at_utc": utc_timestamp(),
        "repo_root": str(root),
        "result_dir": str(result_dir),
        "workspace": str(workspace),
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_evals": args.max_evals,
        "small_test": args.small_test,
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "python_executable": sys.executable,
        "prompt_path": str(fair_prompt_path),
        "prompt_hash": sha256_file(fair_prompt_path),
        "task_hash": sha256_text(task_text),
        "initial_program_path": str(initial_program_path),
        "initial_program_hash": sha256_file(initial_program_path),
        "evaluator_path": str(cloudcast_dir / "evaluator.py"),
        "evaluator_hash": sha256_file(cloudcast_dir / "evaluator.py"),
        "evaluator_bundle_root": str(workspace / "cloudcast_eval"),
        "evaluator_bundle_manifest": evaluator_bundle_manifest,
        "allowed_workspace_files": {
            "task.md": sha256_file(workspace / "task.md"),
            "initial_program.py": sha256_file(workspace / "initial_program.py"),
            "candidate.py": sha256_file(workspace / "candidate.py"),
            "evaluate_candidate.py": sha256_file(workspace / "evaluate_candidate.py"),
        },
        "excluded_oracle_artifacts": [
            {"path": str(path), "hash": sha256_file(path)} for path in oracle_paths if path.exists()
        ],
    }
    if args.okg_mcp:
        metadata["okg_mcp"] = okg_mcp_metadata(root, args)
    (result_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {"root": root, "result_dir": result_dir, "workspace": workspace, "metadata": metadata, "task_text": task_text}


def codex_version() -> str:
    try:
        result = subprocess.run(["codex", "--version"], check=False, capture_output=True, text=True)
        return (result.stdout or result.stderr).strip()
    except FileNotFoundError:
        return "codex-not-found"


def process_text(data: Any) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return str(data)


def run_codex(args: argparse.Namespace, prepared: dict[str, Any]) -> dict[str, Any]:
    result_dir: Path = prepared["result_dir"]
    workspace: Path = prepared["workspace"]
    root: Path = prepared["root"]
    task_text: str = prepared["task_text"]
    last_message = result_dir / "codex_last_message.md"
    stdout_path = result_dir / "codex_events.jsonl"
    stderr_path = result_dir / "codex_stderr.log"
    simulator_output_dir = root / "SystemBench" / "ADRS" / "cloudcast" / "simulator_output"

    cmd = [
        "codex",
        "exec",
        "-C",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "-s",
        args.sandbox,
        "-m",
        args.model,
        "-c",
        f'model_reasoning_effort="{args.reasoning_effort}"',
    ]
    if args.okg_mcp:
        cmd.extend(codex_okg_mcp_config_args(root, args))
    cmd.extend(
        [
            "--json",
            "--output-last-message",
            str(last_message),
            "-",
        ]
    )
    run_record: dict[str, Any] = {
        "codex_version": codex_version(),
        "command": cmd,
        "add_dirs": [],
        "started_at_utc": utc_timestamp(),
    }
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=task_text,
            text=True,
            capture_output=True,
            cwd=str(workspace),
            timeout=args.codex_timeout_seconds,
        )
        run_record.update(
            {
                "returncode": proc.returncode,
                "timed_out": False,
                "elapsed_seconds": time.monotonic() - start,
            }
        )
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        run_record.update(
            {
                "returncode": None,
                "timed_out": True,
                "elapsed_seconds": time.monotonic() - start,
                "timeout_seconds": args.codex_timeout_seconds,
            }
        )
        stdout_path.write_text(process_text(exc.stdout), encoding="utf-8")
        stderr_path.write_text(process_text(exc.stderr), encoding="utf-8")
    except FileNotFoundError as exc:
        run_record.update(
            {
                "returncode": None,
                "timed_out": False,
                "elapsed_seconds": time.monotonic() - start,
                "error": str(exc),
            }
        )
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(str(exc), encoding="utf-8")

    run_record["finished_at_utc"] = utc_timestamp()
    run_record["stdout_path"] = str(stdout_path)
    run_record["stderr_path"] = str(stderr_path)
    run_record["last_message_path"] = str(last_message)
    if args.okg_mcp:
        run_record["mcp_usage"] = summarize_mcp_usage(result_dir, args.okg_mcp_name)
        (result_dir / "mcp_usage_summary.json").write_text(
            json.dumps(run_record["mcp_usage"], indent=2, sort_keys=True),
            encoding="utf-8",
        )
    (result_dir / "codex_run.json").write_text(json.dumps(run_record, indent=2, sort_keys=True), encoding="utf-8")
    return run_record


def choose_candidate(workspace: Path) -> Path | None:
    for name in ("candidate.py", "new_algorithm.py"):
        path = workspace / name
        if path.exists() and path.read_text(encoding="utf-8", errors="ignore").strip():
            return path
    return None


def finalize(args: argparse.Namespace, prepared: dict[str, Any]) -> dict[str, Any]:
    root: Path = prepared["root"]
    result_dir: Path = prepared["result_dir"]
    workspace: Path = prepared["workspace"]
    candidate = choose_candidate(workspace)
    if candidate is None:
        final = {"success": False, "error": "No candidate.py or new_algorithm.py produced", "candidate_path": None}
    else:
        try:
            final = evaluate_candidate(root, candidate, small_test=args.small_test)
        except Exception as exc:
            final = {
                "success": False,
                "error": str(exc),
                "candidate_path": str(candidate),
                "candidate_hash": sha256_file(candidate) if candidate.exists() else None,
            }
    final["arm"] = codex_arm(args)
    final["comparison_type"] = codex_comparison_type(args)
    final["small_test"] = args.small_test
    (result_dir / "final_evaluation.json").write_text(json.dumps(final, indent=2, sort_keys=True), encoding="utf-8")
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default=None, help="Result directory. Defaults under results/codex_baseline_cloudcast/.")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--max-evals", type=int, default=5)
    parser.add_argument("--codex-timeout-seconds", type=int, default=900)
    parser.add_argument("--sandbox", default="workspace-write", choices=["read-only", "workspace-write", "danger-full-access"])
    parser.add_argument("--small-test", action="store_true", help="Use Cloudcast evaluator small_test mode for smoke runs.")
    parser.add_argument("--prepare-only", action="store_true", help="Create workspace and metadata, but do not invoke Codex.")
    parser.add_argument("--okg-mcp", action="store_true", help="Enable the Memex-SR OKG MCP server as the treatment arm.")
    parser.add_argument("--okg-mcp-name", default="okg-memex-sr", help="Codex MCP server name to inject for the OKG treatment.")
    parser.add_argument(
        "--okg-dsn",
        default=os.environ.get("MEMEX_SR_OKG_DSN") or "postgres://postgres:okg@localhost:5433/engram_memex_sr_phase0",
        help="Postgres DSN for the Memex-SR OKG deployment.",
    )
    parser.add_argument("--okg-deployment", default="memex-sr", help="OKG deployment name for MCP and status commands.")
    args = parser.parse_args()

    prepared = prepare_workspace(args)
    if args.prepare_only:
        print(json.dumps({"prepared": True, "result_dir": str(prepared["result_dir"]), "workspace": str(prepared["workspace"])}, indent=2))
        return 0

    run_record = run_codex(args, prepared)
    final = finalize(args, prepared)
    summary = {
        "result_dir": str(prepared["result_dir"]),
        "workspace": str(prepared["workspace"]),
        "codex_returncode": run_record.get("returncode"),
        "codex_timed_out": run_record.get("timed_out"),
        "final_success": final.get("success"),
        "final_score": final.get("score"),
        "final_inferred_total_cost": final.get("inferred_total_cost"),
        "final_error": final.get("error"),
    }
    (prepared["result_dir"] / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if final.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
