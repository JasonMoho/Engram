"""Shared utilities for example scripts."""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def get_results_base_dir(base_dir: Path) -> Path:
    """Return results base directory, respecting GLIA_RESULTS_BASE_DIR env var."""
    return Path(os.environ.get("GLIA_RESULTS_BASE_DIR") or str(base_dir / "results"))


def normalize_initial_program_path(initial_program_path):
    """Filter non-existing paths and normalize to strings."""
    if not initial_program_path:
        return None
    if isinstance(initial_program_path, list):
        result = [str(p) for p in initial_program_path if Path(p).exists()]
        return result if result else None
    return str(initial_program_path) if Path(initial_program_path).exists() else None


def auto_increment_run_dir(results_dir: Path) -> Path:
    """Bump the trailing runN suffix until the directory does not exist."""
    i = 0
    while results_dir.exists():
        results_dir = Path(str(results_dir).replace(f"run{i}", f"run{i + 1}"))
        i += 1
    return results_dir


def print_initial_program(initial_program_path) -> None:
    """Print initial program path(s) in a standardized format."""
    if not initial_program_path:
        return
    if isinstance(initial_program_path, list):
        print(f"Initial Programs: {', '.join(initial_program_path)}")
    else:
        print(f"Initial Program: {initial_program_path}")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_model_label(model: str) -> str:
    """Return a filesystem-safe model/provider label."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", model).strip("_") or "model"


def configure_model_provider(model: str) -> tuple[str, str, dict[str, Any]]:
    """Normalize provider aliases used by benchmark runners.

    The runtime model is what LangChain sees. The label is only for
    stable result paths and report metadata.
    """
    raw_model = model.strip()
    provider = "openai"
    runtime_model = raw_model
    api_base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")

    if raw_model.startswith("openrouter:"):
        provider = "openrouter"
        runtime_model = raw_model.split(":", 1)[1].strip()
        if not runtime_model:
            raise ValueError("--model openrouter:<slug> requires a non-empty OpenRouter model slug")
        os.environ.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
        if not os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENROUTER_API_KEY"):
            os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        api_base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    elif api_base_url and "openrouter.ai" in api_base_url:
        provider = "openrouter"

    metadata = {
        "requested_model": raw_model,
        "runtime_model": runtime_model,
        "model_label": safe_model_label(raw_model),
        "provider": provider,
        "api_base_url_class": classify_api_base(api_base_url),
    }
    return runtime_model, metadata["model_label"], metadata


def classify_api_base(api_base_url: str | None) -> str:
    if not api_base_url:
        return "default"
    lowered = api_base_url.lower()
    if "openrouter.ai" in lowered:
        return "openrouter"
    if "api.openai.com" in lowered:
        return "openai"
    if "api.groq.com" in lowered:
        return "groq"
    return "custom"


def load_json_if_present(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"OKG context metadata file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def infer_context_packet_metadata(packet_text: str) -> dict[str, Any]:
    """Best-effort metadata extraction from a rendered context packet."""
    generation_id = None
    generation_match = re.search(r"^\*\*Generation:\*\*\s*(\d+)\s*$", packet_text, flags=re.MULTILINE)
    if generation_match:
        generation_id = int(generation_match.group(1))

    evidence_ids: set[str] = set()
    for line in packet_text.splitlines():
        stripped = line.strip()
        if "Evidence:" in stripped:
            tail = stripped.split("Evidence:", 1)[1].strip()
            if tail and not tail.startswith("("):
                for item in tail.split(","):
                    item = item.strip()
                    if item and not item.startswith("("):
                        evidence_ids.add(item)
        index_match = re.match(r"^-\s+([^:\s][^:]*:[^:]+):\s+", stripped)
        if index_match:
            evidence_ids.add(index_match.group(1).strip())

    return {
        "generation_id": generation_id,
        "evidence_ids": sorted(evidence_ids),
    }


def create_okg_augmented_task_prompt(
    *,
    task_prompt_path: Path,
    okg_context_file: Path,
    results_dir: Path,
    okg_context_metadata_file: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create a context-first task prompt artifact for an OKG run."""
    packet_text = okg_context_file.read_text(encoding="utf-8")
    original_prompt = task_prompt_path.read_text(encoding="utf-8")
    augmented_prompt = packet_text.rstrip() + "\n\n---\n\n" + original_prompt

    results_dir.mkdir(parents=True, exist_ok=True)
    augmented_path = results_dir / "task_prompt_with_okg_context.md"
    augmented_path.write_text(augmented_prompt, encoding="utf-8")

    explicit_metadata = load_json_if_present(okg_context_metadata_file)
    inferred_metadata = infer_context_packet_metadata(packet_text)
    inputs = explicit_metadata.get("inputs") if isinstance(explicit_metadata.get("inputs"), dict) else {}

    generation_id = (
        explicit_metadata.get("generation_id")
        or inputs.get("generation_id")
        or inferred_metadata.get("generation_id")
    )
    evidence_ids = (
        explicit_metadata.get("evidence_ids")
        or explicit_metadata.get("evidence")
        or inferred_metadata.get("evidence_ids")
        or []
    )

    context_metadata = {
        "okg_context_file": str(okg_context_file),
        "okg_context_hash": sha256_file(okg_context_file),
        "okg_context_metadata_file": str(okg_context_metadata_file) if okg_context_metadata_file else None,
        "okg_context_metadata": explicit_metadata,
        "okg_generation_id": generation_id,
        "okg_evidence_ids": evidence_ids,
        "original_task_prompt_path": str(task_prompt_path),
        "original_task_prompt_hash": sha256_text(original_prompt),
        "augmented_task_prompt_path": str(augmented_path),
        "augmented_task_prompt_hash": sha256_text(augmented_prompt),
    }
    return augmented_path, context_metadata


def resolve_problem_config(base_dir: Path, problem_name: str, give_files: bool = False) -> tuple[Path, Path, str | list[Path]]:
    # Problem-specific configuration.
    if problem_name == "vidur":
        task_prompt_path = base_dir / "SystemBench" / "vidur" / "deepagents_files" / "task_prompt.txt"
        evaluator_path = base_dir / "SystemBench" / "vidur"
        initial_program_path = base_dir / "SystemBench" / "vidur" / "deepagents_files" / "llq_scheduler.py"

    elif problem_name == "cloudcast":
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "cloudcast"
        if give_files:
            task_prompt_path = base_dir / "SystemBench" / "ADRS" / "cloudcast" / "deepagents_files" / "task_prompt_direction_with_optimal.txt"
            initial_program_path = [base_dir / "SystemBench" / "ADRS" / "cloudcast" / "initial_program.py",
                                    base_dir / "SystemBench" / "ADRS" / "cloudcast" / "optimal.py"]
        else:
            print("Using task prompt no cheat no file")
            task_prompt_path = base_dir / "SystemBench" / "ADRS" / "cloudcast" / "deepagents_files" / "task_prompt_direction.txt"
            initial_program_path = base_dir / "SystemBench" / "ADRS" / "cloudcast" / "initial_program.py"

    elif problem_name == "eplb":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "eplb" / "deepagents_files" / "adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "eplb"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "eplb" / "initial_program.py"

    elif problem_name == "llm_sql":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "normal" / "task_prompt.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "llm_sql"
        initial_program_path = [
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "normal" / "initial_program.py",
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "sample_data",
        ]
    elif problem_name == "llm_sql_ggr_ours":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "GGR_ours" / "task_prompt.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "llm_sql"
        initial_program_path = [
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "GGR_ours" / "initial_program.py",
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "sample_data",
        ]
    elif problem_name == "llm_sql_ggr_adrs":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "GGR_ADRS" / "task_prompt.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "llm_sql"
        initial_program_path = [
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "GGR_ADRS" / "initial_program.py",
            base_dir / "SystemBench" / "ADRS" / "llm_sql" / "deepagents_files" / "sample_data",
        ]
    elif problem_name == "cant-be-late":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late" / "deepagents_files" / "adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late" / "initial_program.py"
    elif problem_name == "cant-be-late-multi":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late-multi" / "deepagents_files" /"adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late-multi"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "cant-be-late-multi" / "initial_program.py"
    elif problem_name == "txn_scheduling":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "txn_scheduling" / "deepagents_files" / "adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "txn_scheduling"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "txn_scheduling" / "initial_program.py"
    elif problem_name == "prism":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "prism" / "deepagents_files" / "adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "prism"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "prism" / "initial_program.py"
    elif problem_name == "telemetry_repair":
        task_prompt_path = base_dir / "SystemBench" / "ADRS" / "telemetry_repair" / "deepagents_files" / "adrs.txt"
        evaluator_path = base_dir / "SystemBench" / "ADRS" / "telemetry_repair"
        initial_program_path = base_dir / "SystemBench" / "ADRS" / "telemetry_repair" / "initial_program.py"
    elif problem_name.startswith("fcs_alg_"):
        problem_id = problem_name.replace("fcs_alg_", "")
        fcs_base = base_dir / "SystemBench" / "FrontierCS"
        os.environ["FCS_TRACK"] = "algorithmic"
        os.environ["FCS_PROBLEM_ID"] = problem_id
        task_prompt_path = fcs_base / "frontier_cs_repo" / "algorithmic" / "problems" / problem_id / "statement.txt"
        initial_program_path = fcs_base / "algorithmic" / "initial_program.cpp"
        evaluator_path = fcs_base

    elif problem_name.startswith("fcs_res_"):
        problem_id = problem_name.replace("fcs_res_", "")
        fcs_base = base_dir / "SystemBench" / "FrontierCS"
        os.environ["FCS_TRACK"] = "research"
        os.environ["FCS_PROBLEM_ID"] = problem_id
        initial_program_path = fcs_base / "research" / "initial_program.py"
        fcs_repo = fcs_base / "frontier_cs_repo"
        task_prompt_path = fcs_repo / "research" / "problems" / problem_id / "readme"
        evaluator_path = fcs_base
    else:
        raise ValueError(f"Invalid problem name: {problem_name}.")
    return task_prompt_path, evaluator_path, initial_program_path
