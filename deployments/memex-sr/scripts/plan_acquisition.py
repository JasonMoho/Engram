#!/usr/bin/env python3
"""Plan Memex-SR reference-material acquisition without downloading."""

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
DEFAULT_PAPER_CUT = DEPLOYMENT_DIR / "manifests" / "paper_cut.json"
DEFAULT_POLICY = DEPLOYMENT_DIR / "acquisition_policy.yaml"
DEFAULT_HOST_POLICY = DEPLOYMENT_DIR / "download_host_policy.yaml"
DEFAULT_TEXTBOOKS = DEPLOYMENT_DIR / "textbook_sources.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_id(*parts: object, prefix: str = "plan") -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def host_for(url: str | None) -> str | None:
    if not url:
        return None
    return urlparse(url).netloc.lower()


def looks_like_pdf(url: str | None, asset_kind: str | None = None) -> bool:
    if asset_kind == "pdf_url_hint":
        return True
    if not url:
        return False
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or ".pdf" in path


def host_policy_for(host_policy: dict[str, Any], host: str | None) -> dict[str, Any]:
    defaults = dict(host_policy.get("defaults") or {})
    if host:
        defaults.update((host_policy.get("hosts") or {}).get(host) or {})
    return defaults


def display_path(path: str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def classify_candidate(
    *,
    url: str | None,
    title: str | None,
    material_kind: str,
    source_pack: str,
    source_id: str,
    access_basis: str | None,
    asset_kind: str | None,
    acquisition_hint: str | None,
    policy: dict[str, Any],
    host_policy: dict[str, Any],
) -> dict[str, Any]:
    host = host_for(url)
    access_basis = access_basis or "metadata_only"
    host_cfg = host_policy_for(host_policy, host)
    manual_hosts = set(policy.get("publisher_hosts_manual_only") or [])
    open_hosts = set(policy.get("open_pdf_host_hints") or [])
    is_pdf = looks_like_pdf(url, asset_kind)
    reason = ""

    if access_basis in {"operator_supplied", "licensed_local"}:
        action = "queue_operator_asset"
        state = "needs_operator_asset"
        reason = f"{access_basis} requires a local file manifest"
    elif access_basis == "mit_authenticated" or host in manual_hosts:
        action = "queue_mit_manual"
        state = "needs_mit_operator"
        reason = (
            "subscription or publisher access requires operator-assisted "
            "MIT Libraries workflow"
        )
    elif access_basis == "denied" or host_cfg.get("allowed") is False:
        action = "skip_denied"
        state = "blocked"
        reason = "host or access basis is disabled by policy"
    elif access_basis == "open" and url and is_pdf and host_cfg.get("allowed", True):
        action = "fetch_open"
        state = "planned_open_fetch"
        reason = "open PDF candidate allowed by host policy"
        if host and host not in open_hosts:
            reason = "open PDF candidate on non-listed host; downloader must verify before fetch"
    elif access_basis == "open" and url and material_kind == "textbook":
        action = "fetch_open"
        state = "planned_open_fetch"
        reason = "open long-form source; downloader should discover chapter/document files conservatively"
    elif url:
        action = "skip_metadata_only"
        state = "landing_only"
        reason = "candidate is not an approved full-text asset"
    else:
        action = "queue_operator_asset"
        state = "needs_locator"
        reason = acquisition_hint or "no candidate URL; needs operator locator or local file"

    return {
        "plan_id": stable_id(
            source_pack,
            material_kind,
            source_id,
            asset_kind,
            url,
        ),
        "source_pack": source_pack,
        "material_kind": material_kind,
        "source_id": source_id,
        "title": title,
        "candidate_url": url,
        "host": host,
        "access_basis": access_basis,
        "asset_kind": asset_kind,
        "acquisition_hint": acquisition_hint,
        "acquisition_action": action,
        "acquisition_state": state,
        "reason": reason,
        "host_policy": {
            "allowed": host_cfg.get("allowed", True),
            "concurrency": host_cfg.get("concurrency"),
            "min_delay_seconds": host_cfg.get("min_delay_seconds"),
            "cache_first": host_cfg.get("cache_first"),
            "honor_retry_after": host_cfg.get("honor_retry_after"),
        },
        "mit_library": mit_browser_links(url),
    }


def mit_browser_links(url: str | None) -> dict[str, str] | None:
    if not url:
        return None
    return {
        "libproxy_url": (
            "https://libproxy.mit.edu/login?url="
            + quote(url, safe=":/?&=%#")
        ),
    }


def plan_papers(
    paper_cut: dict[str, Any],
    *,
    policy: dict[str, Any],
    host_policy: dict[str, Any],
    limit: int | None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source_pack = paper_cut.get("pack_id") or "systems-db-2022-2026"
    for paper in paper_cut.get("papers") or []:
        paper_id = paper.get("paper_id")
        title = paper.get("title")
        for asset in paper.get("assets") or []:
            record = classify_candidate(
                url=asset.get("url"),
                title=title,
                material_kind="paper",
                source_pack=source_pack,
                source_id=paper_id,
                access_basis=asset.get("access_basis"),
                asset_kind=asset.get("asset_kind"),
                acquisition_hint=asset.get("source"),
                policy=policy,
                host_policy=host_policy,
            )
            record["paper_id"] = paper_id
            record["venue_id"] = paper.get("venue_id")
            record["year"] = paper.get("year")
            records.append(record)
            if limit is not None and len(records) >= limit:
                return records
    return records


def plan_textbooks(
    textbooks_doc: dict[str, Any],
    *,
    policy: dict[str, Any],
    host_policy: dict[str, Any],
    include_disabled: bool,
) -> list[dict[str, Any]]:
    defaults = textbooks_doc.get("defaults") or {}
    records: list[dict[str, Any]] = []
    for entry in textbooks_doc.get("textbooks") or []:
        enabled = bool(entry.get("enabled", defaults.get("enabled", False)))
        if not enabled and not include_disabled:
            continue
        source_pack = (
            entry.get("source_pack")
            or defaults.get("source_pack")
            or "operator-supplied-assets"
        )
        record = classify_candidate(
            url=entry.get("url"),
            title=entry.get("title"),
            material_kind="textbook",
            source_pack=source_pack,
            source_id=entry.get("id"),
            access_basis=entry.get("access_basis"),
            asset_kind="textbook_target",
            acquisition_hint=entry.get("acquisition_hint"),
            policy=policy,
            host_policy=host_policy,
        )
        record["authors"] = entry.get("authors") or []
        record["domain"] = entry.get("domain")
        record["enabled"] = enabled
        record["parser_bundle"] = (
            entry.get("parser_bundle") or defaults.get("parser_bundle")
        )
        record["notes"] = entry.get("notes")
        records.append(record)
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_action: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_host: dict[str, int] = {}
    for record in records:
        by_action[record["acquisition_action"]] = (
            by_action.get(record["acquisition_action"], 0) + 1
        )
        by_kind[record["material_kind"]] = (
            by_kind.get(record["material_kind"], 0) + 1
        )
        host = record.get("host") or "(none)"
        by_host[host] = by_host.get(host, 0) + 1
    return {
        "total_records": len(records),
        "by_action": dict(sorted(by_action.items())),
        "by_material_kind": dict(sorted(by_kind.items())),
        "top_hosts": dict(
            sorted(by_host.items(), key=lambda item: item[1], reverse=True)[:20]
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-cut", default=str(DEFAULT_PAPER_CUT))
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--host-policy", default=str(DEFAULT_HOST_POLICY))
    parser.add_argument("--textbooks", default=str(DEFAULT_TEXTBOOKS))
    parser.add_argument(
        "--out",
        default="-",
        help="Output JSON path, or '-' for stdout.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit paper asset records for smoke runs.",
    )
    parser.add_argument("--include-textbooks", action="store_true")
    parser.add_argument("--include-disabled-textbooks", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy = load_yaml(Path(args.policy))
    host_policy = load_yaml(Path(args.host_policy))
    paper_cut = load_json(Path(args.paper_cut))

    records = plan_papers(
        paper_cut,
        policy=policy,
        host_policy=host_policy,
        limit=args.limit,
    )
    if args.include_textbooks or args.include_disabled_textbooks:
        textbooks_doc = load_yaml(Path(args.textbooks))
        records.extend(
            plan_textbooks(
                textbooks_doc,
                policy=policy,
                host_policy=host_policy,
                include_disabled=args.include_disabled_textbooks,
            )
        )

    output = {
        "version": 1,
        "deployment": "memex-sr",
        "generated_at": dt.datetime.now(dt.UTC)
        .replace(microsecond=0)
        .isoformat(),
        "paper_cut": display_path(args.paper_cut),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
