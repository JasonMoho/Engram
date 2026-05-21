#!/usr/bin/env python3
"""Fetch/cache open paper PDFs from the Memex-SR paper cut.

This is an operator acquisition command, not a publish-time source. It
does network I/O, writes deterministic local files, and produces a JSONL
manifest that the OKG source consumes without touching the network.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_DIR = REPO_ROOT / "deployments" / "memex-sr"
DEFAULT_PAPER_CUT = DEPLOYMENT_DIR / "manifests" / "paper_cut.json"
DEFAULT_HOST_POLICY = DEPLOYMENT_DIR / "download_host_policy.yaml"
DEFAULT_OUT = DEPLOYMENT_DIR / "manifests" / "paper_fulltext_assets.jsonl"
DEFAULT_REPORT = DEPLOYMENT_DIR / "reports" / "paper-fulltext" / "acquisition-status.md"
DEFAULT_CACHE = DEPLOYMENT_DIR / ".cache" / "paper_fulltext"

DEFAULT_ALLOWED_HOSTS = ("www.usenix.org", "www.vldb.org")
FRONT_MATTER_RE = re.compile(
    r"^(author index|copyright|front matter|message from|organizing committee|"
    r"program committee|table of contents|title page)$",
    re.IGNORECASE,
)


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


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-") or "unknown"


def _host_policy(host_policy: dict[str, Any], host: str) -> dict[str, Any]:
    out = dict(host_policy.get("defaults") or {})
    out.update((host_policy.get("hosts") or {}).get(host) or {})
    return out


def _candidate_records(
    paper_cut: dict[str, Any],
    *,
    allowed_hosts: set[str],
    venues: set[str] | None,
    years: set[int] | None,
    include_front_matter: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_papers: set[str] = set()
    for paper in paper_cut.get("papers") or []:
        paper_id = str(paper.get("paper_id") or "")
        title = str(paper.get("title") or "").strip()
        venue = str(paper.get("venue_id") or paper.get("venue") or "").lower()
        year = int(paper.get("year") or 0)
        if not paper_id or paper_id in seen_papers:
            continue
        if venues and venue not in venues:
            continue
        if years and year not in years:
            continue
        if not include_front_matter and FRONT_MATTER_RE.match(title):
            continue
        raw_assets = paper.get("assets") or []
        landing_urls = [
            str(asset.get("url") or "")
            for asset in raw_assets
            if asset.get("asset_kind") == "landing_page"
            and asset.get("access_basis") == "open"
            and urlparse(str(asset.get("url") or "")).netloc.lower() in allowed_hosts
        ]
        assets = sorted(
            raw_assets,
            key=lambda item: (
                0 if item.get("asset_kind") == "pdf_url_hint" else 1,
                str(item.get("url") or ""),
            ),
        )
        for asset in assets:
            url = str(asset.get("url") or "")
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            if host not in allowed_hosts:
                continue
            if asset.get("access_basis") != "open":
                continue
            if Path(parsed.path).suffix.lower() != ".pdf":
                continue
            seen_papers.add(paper_id)
            records.append(
                {
                    "paper_id": paper_id,
                    "title": title,
                    "venue_id": venue,
                    "year": year,
                    "doi": paper.get("doi"),
                    "abstract": paper.get("abstract"),
                    "asset_id": asset.get("asset_id"),
                    "asset_kind": asset.get("asset_kind"),
                    "access_basis": asset.get("access_basis"),
                    "source": asset.get("source"),
                    "source_url": url,
                    "landing_url": landing_urls[0] if landing_urls else None,
                    "host": host,
                    "acquisition_action": "fetch_open_pdf",
                    "acquisition_state": "planned_open_fetch",
                    "available": False,
                }
            )
            break
    return records


def _cache_path(record: dict[str, Any], cache_root: Path) -> Path:
    host = _safe(str(record.get("host") or "unknown"))
    venue = _safe(str(record.get("venue_id") or "unknown"))
    year = str(record.get("year") or "unknown")
    asset = _safe(str(record.get("asset_id") or record.get("paper_id")))
    return cache_root / host / venue / year / f"{asset}.pdf"


def _session(user_agent: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "application/pdf,*/*;q=0.5",
        }
    )
    return session


def _download_pdf(session: requests.Session, url: str, *, timeout: int) -> tuple[bytes, str]:
    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    data = response.content
    if "pdf" not in content_type and not data.startswith(b"%PDF"):
        raise ValueError(f"response is not a PDF: content-type={content_type!r}")
    return data, response.url


def _resolve_pdf_from_landing(
    session: requests.Session,
    landing_url: str,
    *,
    timeout: int,
) -> str | None:
    response = session.get(landing_url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    html = response.text
    hrefs = re.findall(r"""href=["']([^"']+\.pdf(?:\?[^"']*)?)["']""", html, flags=re.IGNORECASE)
    if not hrefs:
        return None
    absolute = [urljoin(response.url, href) for href in hrefs]
    preferred = [url for url in absolute if "/system/files/" in url]
    return (preferred or absolute)[0]


def _fetch_record(
    record: dict[str, Any],
    *,
    cache_root: Path,
    session: requests.Session,
    force: bool,
    timeout: int,
) -> dict[str, Any]:
    target = _cache_path(record, cache_root)
    if target.is_file() and not force:
        return {
            **record,
            "available": True,
            "acquisition_state": "cached",
            "local_path": _repo_relative(target),
            "content_sha256": _sha256_file(target),
            "byte_count": target.stat().st_size,
            "mime_type": "application/pdf",
            "fetched_at": None,
        }

    source_url = str(record["source_url"])
    final_url = source_url
    try:
        data, final_url = _download_pdf(session, source_url, timeout=timeout)
    except (requests.RequestException, ValueError):
        landing_url = record.get("landing_url")
        if not landing_url:
            raise
        resolved = _resolve_pdf_from_landing(session, str(landing_url), timeout=timeout)
        if not resolved:
            raise
        data, final_url = _download_pdf(session, resolved, timeout=timeout)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        **record,
        "available": True,
        "acquisition_state": "fetched",
        "local_path": _repo_relative(target),
        "content_sha256": _sha256_bytes(data),
        "byte_count": len(data),
        "mime_type": "application/pdf",
        "final_url": final_url,
        "fetched_at": _utc_now(),
    }


def _write_report(path: Path, records: list[dict[str, Any]], *, generated_at: str) -> None:
    counts: dict[str, int] = {}
    by_venue: dict[str, int] = {}
    for record in records:
        state = str(record.get("acquisition_state") or "unknown")
        counts[state] = counts.get(state, 0) + 1
        if record.get("available"):
            venue = str(record.get("venue_id") or "unknown")
            by_venue[venue] = by_venue.get(venue, 0) + 1
    lines = [
        "# Paper Full-Text Acquisition Status",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Summary",
        "",
        f"- Records in manifest: `{len(records)}`",
        f"- Available local PDFs: `{sum(1 for r in records if r.get('available'))}`",
        f"- States: `{json.dumps(dict(sorted(counts.items())), sort_keys=True)}`",
        f"- Available by venue: `{json.dumps(dict(sorted(by_venue.items())), sort_keys=True)}`",
        "",
        "## Records",
        "",
        "| Paper | Venue | Year | State | Bytes | Local path |",
        "|:--|:--|--:|:--|--:|:--|",
    ]
    for record in records:
        lines.append(
            "| `{paper}` | {venue} | {year} | {state} | {bytes} | `{local}` |".format(
                paper=record.get("paper_id"),
                venue=record.get("venue_id"),
                year=record.get("year"),
                state=record.get("acquisition_state"),
                bytes=record.get("byte_count") or 0,
                local=record.get("local_path") or "",
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-cut", default=str(DEFAULT_PAPER_CUT))
    parser.add_argument("--host-policy", default=str(DEFAULT_HOST_POLICY))
    parser.add_argument("--cache-root", default=str(DEFAULT_CACHE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    parser.add_argument("--allowed-host", action="append", default=None)
    parser.add_argument("--venue", action="append", default=None)
    parser.add_argument("--year", action="append", type=int, default=None)
    parser.add_argument("--max-papers", type=int, default=150)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--from-cache-only",
        action="store_true",
        help="Build the manifest only from already cached files; perform no network I/O.",
    )
    parser.add_argument("--include-front-matter", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paper_cut = json.loads(Path(args.paper_cut).read_text(encoding="utf-8"))
    host_policy = _load_yaml(Path(args.host_policy))
    host_defaults = host_policy.get("defaults") or {}
    allowed_hosts = set(args.allowed_host or DEFAULT_ALLOWED_HOSTS)
    venues = {v.lower() for v in args.venue} if args.venue else None
    years = set(args.year or []) or None
    timeout = int(args.timeout or host_defaults.get("timeout_seconds") or 20)
    records = _candidate_records(
        paper_cut,
        allowed_hosts=allowed_hosts,
        venues=venues,
        years=years,
        include_front_matter=args.include_front_matter,
    )
    selected = records[args.offset :]
    if args.from_cache_only:
        selected = [
            record
            for record in selected
            if _cache_path(record, Path(args.cache_root).resolve()).is_file()
        ]
    if args.max_papers is not None:
        selected = selected[: args.max_papers]

    generated_at = _utc_now()
    session = _session(str(host_defaults.get("user_agent") or "memex-sr-paper-fetcher/0.1"))
    cache_root = Path(args.cache_root).resolve()
    last_fetch_by_host: dict[str, float] = {}
    out: list[dict[str, Any]] = []
    for record in selected:
        host = str(record.get("host") or "")
        cfg = _host_policy(host_policy, host)
        if not cfg.get("allowed", True):
            out.append(
                {
                    **record,
                    "acquisition_state": "blocked_by_host_policy",
                    "available": False,
                    "error": f"host not allowed: {host}",
                    "acquisition_manifest_generated_at": generated_at,
                }
            )
            continue
        target = _cache_path(record, cache_root)
        cache_hit = target.is_file() and not args.force
        if not cache_hit:
            min_delay = float(cfg.get("min_delay_seconds") or 0)
            elapsed = time.monotonic() - last_fetch_by_host.get(host, 0.0)
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
        if args.dry_run:
            acquired = {
                **record,
                "acquisition_state": "dry_run_open_fetch",
                "available": False,
                "target_cache_path": _repo_relative(target),
            }
        elif args.from_cache_only:
            acquired = _fetch_record(
                record,
                cache_root=cache_root,
                session=session,
                force=False,
                timeout=timeout,
            )
        else:
            try:
                acquired = _fetch_record(
                    record,
                    cache_root=cache_root,
                    session=session,
                    force=args.force,
                    timeout=timeout,
                )
            except (requests.RequestException, ValueError, OSError) as exc:
                acquired = {
                    **record,
                    "acquisition_state": "fetch_failed",
                    "available": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            if not cache_hit:
                last_fetch_by_host[host] = time.monotonic()
        acquired["acquisition_manifest_generated_at"] = generated_at
        out.append(acquired)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in out),
        encoding="utf-8",
    )
    _write_report(Path(args.report_out), out, generated_at=generated_at)
    print(f"eligible_open_pdf_assets={len(records)}")
    print(f"manifest_records={len(out)}")
    print(f"available={sum(1 for record in out if record.get('available'))}")
    print(f"fetched={sum(1 for record in out if record.get('acquisition_state') == 'fetched')}")
    print(f"cached={sum(1 for record in out if record.get('acquisition_state') == 'cached')}")
    print(f"failed={sum(1 for record in out if record.get('acquisition_state') == 'fetch_failed')}")
    print(f"out={_repo_relative(out_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
