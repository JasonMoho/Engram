#!/usr/bin/env python3
"""Fetch/cache reviewed open Cloudcast sources.

This script is intentionally outside OKG publish. Publish must be
network-free and repeatable from local files; this command is the
operator-controlled acquisition step that creates those local files.
MIT-authenticated and metadata-only records are queued/recorded but not
downloaded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import time
from pathlib import Path
from typing import Any

import requests

from plan_cloudcast_acquisition import (
    DEFAULT_HOST_POLICY,
    DEFAULT_POLICY,
    DEFAULT_SOURCES,
    REPO_ROOT,
    classify_source,
    display_path,
    host_policy_for,
    load_yaml,
)


DEPLOYMENT_DIR = REPO_ROOT / "deployments" / "memex-sr"
DEFAULT_ASSETS_OUT = DEPLOYMENT_DIR / "manifests" / "cloudcast_acquired_assets.jsonl"
DEFAULT_REPORT_OUT = DEPLOYMENT_DIR / "reports" / "cloudcast-ab" / "cloudcast-acquisition-status.md"


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _mime_for(path: Path, content_type: str | None = None) -> str:
    if content_type:
        return content_type.split(";", 1)[0].strip().lower()
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _session(user_agent: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/pdf,text/plain,*/*;q=0.8",
        }
    )
    return session


def _fetch_open(
    record: dict[str, Any],
    *,
    session: requests.Session,
    force: bool,
    timeout: int,
) -> dict[str, Any]:
    target_rel = record.get("target_cache_path")
    url = record.get("source_url")
    if not target_rel or not url:
        return {
            **record,
            "available": False,
            "acquisition_state": "missing_fetch_target",
            "error": "fetch_open record has no source_url or cache path",
        }

    target = (REPO_ROOT / target_rel).resolve()
    if target.exists() and not force:
        return {
            **record,
            "available": True,
            "acquisition_state": "cached",
            "local_path": _repo_relative(target),
            "content_sha256": _sha256_file(target),
            "byte_count": target.stat().st_size,
            "mime_type": _mime_for(target),
            "fetched_at": None,
        }

    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    data = response.content
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        **record,
        "available": True,
        "acquisition_state": "fetched",
        "local_path": _repo_relative(target),
        "content_sha256": _sha256_bytes(data),
        "byte_count": len(data),
        "mime_type": _mime_for(target, response.headers.get("content-type")),
        "final_url": response.url,
        "fetched_at": _utc_now(),
    }


def _local_file(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("local_path")
    if not raw:
        return {**record, "available": False, "acquisition_state": "missing_local_path"}
    path = (REPO_ROOT / raw).resolve()
    if not path.is_file():
        return {
            **record,
            "available": False,
            "acquisition_state": "missing_local_file",
            "error": f"local source not found: {raw}",
        }
    return {
        **record,
        "available": True,
        "acquisition_state": "local_available",
        "local_path": _repo_relative(path),
        "content_sha256": _sha256_file(path),
        "byte_count": path.stat().st_size,
        "mime_type": _mime_for(path),
        "fetched_at": None,
    }


def _passthrough_unavailable(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "available": False,
        "local_path": None,
        "content_sha256": None,
        "byte_count": None,
        "mime_type": None,
        "fetched_at": None,
    }


def _build_markdown(records: list[dict[str, Any]], *, generated_at: str) -> str:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get("acquisition_state") or record.get("acquisition_action"))
        counts[key] = counts.get(key, 0) + 1
    lines = [
        "# Cloudcast Acquisition Status",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Summary",
        "",
        f"- Records: `{len(records)}`",
        f"- Available local files: `{sum(1 for r in records if r.get('available'))}`",
        f"- States: `{json.dumps(dict(sorted(counts.items())), sort_keys=True)}`",
        "",
        "## Records",
        "",
        "| Source | Action | State | Available | Bytes | Local file |",
        "|:--|:--|:--|:--:|--:|:--|",
    ]
    for record in records:
        lines.append(
            "| `{source}` | {action} | {state} | {available} | {bytes} | `{local}` |".format(
                source=record.get("source_id"),
                action=record.get("acquisition_action"),
                state=record.get("acquisition_state"),
                available="yes" if record.get("available") else "no",
                bytes=record.get("byte_count") or 0,
                local=record.get("local_path") or "",
            )
        )
    lines.append("")
    lines.append(
        "`queue_mit_manual` records are not downloaded by this script. "
        "Retrieve them through approved MIT/operator workflows, put the "
        "files in the cache, and rerun acquisition with explicit provenance."
    )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--host-policy", default=str(DEFAULT_HOST_POLICY))
    parser.add_argument("--out", default=str(DEFAULT_ASSETS_OUT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT))
    parser.add_argument("--include-holdout", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources_path = Path(args.sources)
    policy = load_yaml(Path(args.policy))
    host_policy = load_yaml(Path(args.host_policy))
    source_doc = load_yaml(sources_path)
    host_defaults = host_policy.get("defaults") or {}
    session = _session(str(host_defaults.get("user_agent") or "memex-sr-source-fetcher/0.1"))
    timeout = int(args.timeout or host_defaults.get("timeout_seconds") or 20)

    planned = [
        record
        for source in source_doc.get("sources") or []
        if (
            record := classify_source(
                source,
                policy=policy,
                host_policy=host_policy,
                include_holdout=args.include_holdout,
            )
        )
        is not None
    ]
    if args.limit is not None:
        planned = planned[: args.limit]

    generated_at = _utc_now()
    out_records: list[dict[str, Any]] = []
    last_fetch_by_host: dict[str, float] = {}
    for record in planned:
        action = record.get("acquisition_action")
        if action == "use_local_file":
            acquired = _local_file(record)
        elif action == "fetch_open":
            host = record.get("host")
            host_cfg = host_policy_for(host_policy, host)
            min_delay = float(host_cfg.get("min_delay_seconds") or 0)
            elapsed = time.monotonic() - last_fetch_by_host.get(str(host), 0.0)
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
            if args.dry_run:
                acquired = {
                    **record,
                    "available": False,
                    "acquisition_state": "dry_run_open_fetch",
                    "local_path": record.get("target_cache_path"),
                }
            else:
                try:
                    acquired = _fetch_open(
                        record,
                        session=session,
                        force=args.force,
                        timeout=timeout,
                    )
                except requests.RequestException as exc:
                    acquired = {
                        **record,
                        "available": False,
                        "acquisition_state": "fetch_failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                last_fetch_by_host[str(host)] = time.monotonic()
        else:
            acquired = _passthrough_unavailable(record)

        acquired["acquisition_manifest_generated_at"] = generated_at
        out_records.append(acquired)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in out_records),
        encoding="utf-8",
    )

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_build_markdown(out_records, generated_at=generated_at), encoding="utf-8")

    print(f"wrote {display_path(out_path)}")
    print(f"wrote {display_path(report_path)}")
    print(
        json.dumps(
            {
                "records": len(out_records),
                "available": sum(1 for record in out_records if record.get("available")),
                "fetched": sum(1 for record in out_records if record.get("acquisition_state") == "fetched"),
                "cached": sum(1 for record in out_records if record.get("acquisition_state") == "cached"),
                "local_available": sum(
                    1 for record in out_records if record.get("acquisition_state") == "local_available"
                ),
                "fetch_failed": sum(1 for record in out_records if record.get("acquisition_state") == "fetch_failed"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
