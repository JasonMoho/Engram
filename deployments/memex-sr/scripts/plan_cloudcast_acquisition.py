#!/usr/bin/env python3
"""Create a no-network acquisition plan for reviewed Cloudcast sources."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_DIR = REPO_ROOT / "deployments" / "memex-sr"
DEFAULT_SOURCES = DEPLOYMENT_DIR / "fixtures" / "cloudcast_sources.yaml"
DEFAULT_POLICY = DEPLOYMENT_DIR / "acquisition_policy.yaml"
DEFAULT_HOST_POLICY = DEPLOYMENT_DIR / "download_host_policy.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stable_id(*parts: object, prefix: str = "cloudcast-plan") -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def host_for(url: str | None) -> str | None:
    if not url:
        return None
    return urlparse(url).netloc.lower()


def display_path(path: str | Path | None) -> str | None:
    if not path:
        return None
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def host_policy_for(host_policy: dict[str, Any], host: str | None) -> dict[str, Any]:
    defaults = dict(host_policy.get("defaults") or {})
    if host:
        defaults.update((host_policy.get("hosts") or {}).get(host) or {})
    return defaults


def cache_path_for(source: dict[str, Any], url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".pdf", ".html", ".htm", ".txt", ".md"}:
        suffix = ".html"
    safe_id = str(source["id"]).replace(":", "_").replace("/", "_")
    return str(
        DEPLOYMENT_DIR
        / ".cache"
        / "cloudcast_sources"
        / safe_id
        / f"source{suffix}"
    )


def libproxy_url(url: str | None) -> str | None:
    if not url:
        return None
    return "https://libproxy.mit.edu/login?url=" + quote(url, safe=":/?&=%#")


def classify_source(
    source: dict[str, Any],
    *,
    policy: dict[str, Any],
    host_policy: dict[str, Any],
    include_holdout: bool,
) -> dict[str, Any] | None:
    holdout = bool(source.get("holdout"))
    if holdout and not include_holdout:
        return None

    url = source.get("source_url")
    local_path = source.get("local_path")
    access_basis = source.get("access_basis") or "metadata_only"
    host = host_for(url)
    host_cfg = host_policy_for(host_policy, host)
    manual_hosts = set(policy.get("publisher_hosts_manual_only") or [])

    if holdout:
        action = "skip_holdout"
        state = "blocked_holdout"
        reason = "source is marked holdout-only"
    elif local_path:
        local_abs = (REPO_ROOT / local_path).resolve()
        action = "use_local_file"
        state = "local_available" if local_abs.exists() else "missing_local_file"
        reason = "local benchmark or operator-managed file"
    elif access_basis == "metadata_only":
        action = "skip_metadata_only"
        state = "landing_only"
        reason = "metadata/landing page only until a local or open full-text asset is supplied"
    elif access_basis in {"mit_authenticated", "licensed_local"} or host in manual_hosts:
        action = "queue_mit_manual"
        state = "needs_mit_operator"
        reason = "manual MIT/operator retrieval required; no scripted authenticated download"
    elif access_basis == "open" and url and host_cfg.get("allowed", True):
        action = "fetch_open"
        state = "planned_open_fetch"
        reason = "open candidate allowed by host policy; dry run does not download"
    else:
        action = "skip_denied"
        state = "blocked"
        reason = "access basis or host policy blocks automated acquisition"

    target_cache_path = cache_path_for(source, url)
    return {
        "plan_id": stable_id(source.get("id"), url, local_path),
        "source_id": source.get("id"),
        "title": source.get("title"),
        "tier": source.get("tier"),
        "category": source.get("category"),
        "access_basis": access_basis,
        "holdout": holdout,
        "source_url": url,
        "local_path": local_path,
        "target_cache_path": display_path(target_cache_path),
        "host": host,
        "acquisition_action": action,
        "acquisition_state": state,
        "reason": reason,
        "rate_policy": {
            "allowed": host_cfg.get("allowed", True),
            "concurrency": host_cfg.get("concurrency"),
            "min_delay_seconds": host_cfg.get("min_delay_seconds"),
            "cache_first": host_cfg.get("cache_first"),
            "honor_retry_after": host_cfg.get("honor_retry_after"),
        },
        "mit_library": {"libproxy_url": libproxy_url(url)} if action == "queue_mit_manual" else None,
        "transfer_to_cloudcast": source.get("transfer_to_cloudcast"),
        "extraction_targets": source.get("extraction_targets") or [],
        "review_state": source.get("review_state"),
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_records": len(records),
        "non_holdout_records": sum(1 for record in records if not record["holdout"]),
        "by_action": {},
        "by_access_basis": {},
        "by_category": {},
        "by_tier": {},
    }
    for key, field in [
        ("by_action", "acquisition_action"),
        ("by_access_basis", "access_basis"),
        ("by_category", "category"),
        ("by_tier", "tier"),
    ]:
        counts: dict[str, int] = {}
        for record in records:
            raw_value = record.get(field)
            value = "(none)" if raw_value is None else str(raw_value)
            counts[value] = counts.get(value, 0) + 1
        summary[key] = dict(sorted(counts.items()))
    return summary


def build_markdown(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    records = plan["records"]
    lines = [
        "# Cloudcast Acquisition Plan",
        "",
        f"Generated: `{plan['generated_at']}`",
        f"Source manifest: `{plan['source_manifest']}`",
        "",
        "## Summary",
        "",
        f"- Non-holdout records: `{summary['non_holdout_records']}`",
        f"- Total records in plan: `{summary['total_records']}`",
        f"- Actions: `{json.dumps(summary['by_action'], sort_keys=True)}`",
        f"- Categories: `{json.dumps(summary['by_category'], sort_keys=True)}`",
        f"- Access basis: `{json.dumps(summary['by_access_basis'], sort_keys=True)}`",
        "",
        "## Records",
        "",
        "| Source | Tier | Category | Access | Action | State | Target |",
        "|:--|--:|:--|:--|:--|:--|:--|",
    ]
    for record in records:
        target = record.get("local_path") or record.get("target_cache_path") or record.get("source_url") or "n/a"
        lines.append(
            "| `{source}` | {tier} | {category} | {access} | {action} | {state} | `{target}` |".format(
                source=record.get("source_id"),
                tier=record.get("tier"),
                category=record.get("category"),
                access=record.get("access_basis"),
                action=record.get("acquisition_action"),
                state=record.get("acquisition_state"),
                target=target,
            )
        )
    lines.extend(
        [
            "",
            "This is a dry-run plan. It does not download sources. `queue_mit_manual` "
            "records require an operator to retrieve material through approved MIT "
            "library or browser workflows and then register local files with provenance.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--host-policy", default=str(DEFAULT_HOST_POLICY))
    parser.add_argument("--include-holdout", action="store_true")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout.")
    parser.add_argument("--markdown-output", default=None, help="Optional markdown summary path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources_path = Path(args.sources)
    doc = load_yaml(sources_path)
    policy = load_yaml(Path(args.policy))
    host_policy = load_yaml(Path(args.host_policy))

    records = [
        record
        for source in doc.get("sources") or []
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
    output = {
        "version": 1,
        "deployment": "memex-sr",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "source_manifest": display_path(sources_path),
        "policy": display_path(args.policy),
        "host_policy": display_path(args.host_policy),
        "summary": summarize(records),
        "records": records,
    }

    if args.out == "-":
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {out}")
        print(json.dumps(output["summary"], indent=2, sort_keys=True))
    if args.markdown_output:
        markdown_output = Path(args.markdown_output)
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(build_markdown(output) + "\n", encoding="utf-8")
        print(f"wrote {markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
