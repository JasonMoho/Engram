#!/usr/bin/env python3
"""Sample candidate Memex-SR data sources without publishing graph facts."""

from __future__ import annotations

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
import yaml


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = {key: value for key, value in attrs}
        href = attrs_dict.get("href")
        if href:
            self._current_href = href
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return
        text = normalize_ws(" ".join(self._parts))
        self.anchors.append({"href": self._current_href, "text": text})
        self._current_href = None
        self._parts = []


def normalize_ws(value: str) -> str:
    return repair_mojibake(re.sub(r"\s+", " ", html.unescape(value)).strip())


def repair_mojibake(value: str) -> str:
    if "Ã" not in value and "Â" not in value:
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def host_policy_for(policy: dict[str, Any], url: str) -> dict[str, Any]:
    host = urlparse(url).netloc
    defaults = policy.get("defaults", {})
    host_policy = policy.get("hosts", {}).get(host, {})
    merged = dict(defaults)
    merged.update(host_policy)
    return merged


def polite_get(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None,
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    timeout_seconds: int,
) -> requests.Response:
    host = urlparse(url).netloc
    host_policy = host_policy_for(policy, url)
    if host_policy.get("allowed") is False:
        raise RuntimeError(f"Host {host} is disabled by download_host_policy.yaml")

    delay = float(host_policy.get("min_delay_seconds", 0) or 0)
    previous = last_request_by_host.get(host)
    if previous is not None:
        elapsed = time.monotonic() - previous
        if elapsed < delay:
            time.sleep(delay - elapsed)

    timeout = int(host_policy.get("timeout_seconds", timeout_seconds) or timeout_seconds)
    response = session.get(url, params=params, timeout=timeout)
    last_request_by_host[host] = time.monotonic()
    return response


def result(
    source: dict[str, Any],
    *,
    status: str,
    http_status: int | None = None,
    content_type: str | None = None,
    item_count: int = 0,
    sample_items: list[dict[str, Any]] | None = None,
    error: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    declared = source.get("ontology_hits", [])
    diagnostic_only = source.get("coverage_mode") == "diagnostic_only"
    observed = declared if status == "ok" and item_count > 0 and not diagnostic_only else []
    coverage_notes = ["diagnostic_only_source_not_counted_for_coverage"] if diagnostic_only else []
    return {
        "source_id": source["id"],
        "kind": source["kind"],
        "pack": source.get("pack"),
        "venue_id": source.get("venue_id"),
        "year": source.get("year"),
        "url": source.get("url"),
        "status": status,
        "http_status": http_status,
        "content_type": content_type,
        "item_count": item_count,
        "sample_items": sample_items or [],
        "declared_ontology_hits": declared,
        "observed_ontology_hits": observed,
        "validates": source.get("validates", []),
        "notes": [value for value in [source.get("notes")] if value] + coverage_notes + (notes or []),
        "error": error,
    }


def parse_anchors(base_url: str, text: str) -> list[dict[str, str]]:
    parser = AnchorParser()
    parser.feed(text)
    return [
        {"url": urljoin(base_url, anchor["href"]), "text": anchor["text"]}
        for anchor in parser.anchors
        if anchor["href"]
    ]


def sample_local_glob(repo_root: Path, source: dict[str, Any], limit: int) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for pattern in source.get("globs", []):
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            title = next(
                (line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")),
                path.name,
            )
            items.append(
                {
                    "path": str(path.relative_to(repo_root)),
                    "title": title,
                    "byte_count": path.stat().st_size,
                }
            )
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    status = "ok" if items else "empty"
    return result(source, status=status, item_count=len(items), sample_items=items)


def sample_yaml_config(repo_root: Path, source: dict[str, Any], limit: int) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for value in source.get("paths", []):
        path = resolve_path(repo_root, value)
        if not path.exists():
            items.append({"path": value, "status": "missing"})
            continue
        data = load_yaml(path)
        summary: dict[str, Any] = {
            "path": str(path.relative_to(repo_root)),
            "status": "ok",
            "top_level_keys": sorted(data.keys()),
        }
        if "packs" in data:
            summary["pack_count"] = len(data.get("packs") or [])
            summary["enabled_pack_count"] = len([pack for pack in data.get("packs") or [] if pack.get("enabled")])
        if "venue_groups" in data:
            groups = data.get("venue_groups") or {}
            summary["venue_group_count"] = len(groups)
            summary["venue_count"] = sum(len(group.get("venues") or []) for group in groups.values())
        if "sources" in data:
            summary["source_count"] = len(data.get("sources") or [])
        items.append(summary)
        if len(items) >= limit:
            break
    status = "ok" if items and all(item.get("status") == "ok" for item in items) else "empty"
    return result(source, status=status, item_count=len(items), sample_items=items)


def sample_engram_workspace_fixture(repo_root: Path, source: dict[str, Any], limit: int) -> dict[str, Any]:
    root = resolve_path(repo_root, source["root"])
    if not root.exists():
        return result(source, status="empty", error=f"Fixture root does not exist: {root}")
    patterns = [
        ("research_note", "research_journal.md"),
        ("agent_attempt", "knowledgebase/agent_*/*.md"),
        ("experiment_score", "experiments/exp_*/score.txt"),
        ("candidate_implementation", "experiments/exp_*/snapshot.*"),
        ("metric_observation", "experiments/exp_*/results/*.json"),
        ("failure_diagnosis", "experiments/exp_*/failure.*"),
    ]
    items: list[dict[str, Any]] = []
    for artifact_kind, pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            items.append(
                {
                    "artifact_kind": artifact_kind,
                    "path": str(path.relative_to(repo_root)),
                    "byte_count": path.stat().st_size,
                }
            )
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    status = "ok" if items else "empty"
    return result(source, status=status, item_count=len(items), sample_items=items)


def sample_dblp_toc(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    titles = [
        normalize_ws(match)
        for match in re.findall(r'<span[^>]+class="title"[^>]*>(.*?)</span>', response.text, flags=re.I | re.S)
    ]
    if not titles:
        anchors = parse_anchors(source["url"], response.text)
        titles = [
            anchor["text"]
            for anchor in anchors
            if anchor["text"] and "/rec/" in anchor["url"]
        ]
    items = [{"title": title} for title in titles[:limit] if title]
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


def sample_usenix(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    anchors = parse_anchors(source["url"], response.text)
    presentation_items = []
    pdf_hints = []
    for anchor in anchors:
        url = anchor["url"]
        text = anchor["text"]
        source_path_parts = urlparse(source["url"]).path.strip("/").split("/")
        conference_prefix = "/".join(source_path_parts[:2])
        same_conference_presentation = f"/{conference_prefix}/presentation/" in urlparse(url).path
        if same_conference_presentation and text:
            presentation_items.append({"title": text, "url": url})
        if ".pdf" in url.lower():
            pdf_hints.append(url)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in presentation_items:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)
        if len(deduped) >= limit:
            break
    status = "ok" if deduped else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(deduped),
        sample_items=deduped,
        notes=[f"pdf_hint_count={len(pdf_hints)}", "PDF links are counted but not downloaded by the sampler."],
    )


def sample_vldb(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    items: list[dict[str, Any]] = []
    script_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        response.text,
        flags=re.S,
    )
    if script_match:
        try:
            data = json.loads(html.unescape(script_match.group(1)))
            collect_vldb_papers(data, items, limit)
        except json.JSONDecodeError as exc:
            return result(
                source,
                status="error",
                http_status=response.status_code,
                content_type=content_type,
                error=f"Could not parse PVLDB __NEXT_DATA__: {exc}",
            )
    if not items:
        for title in re.findall(r'"Paper Title":"(.*?)"', response.text):
            items.append({"title": normalize_ws(title)})
            if len(items) >= limit:
                break

    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


def collect_vldb_papers(value: Any, items: list[dict[str, Any]], limit: int) -> None:
    if len(items) >= limit:
        return
    if isinstance(value, dict):
        title = value.get("Paper Title")
        if title:
            items.append(
                {
                    "title": normalize_ws(str(title)),
                    "authors": normalize_ws(str(value.get("Author Names", ""))),
                    "paper_id": value.get("Paper ID"),
                }
            )
            return
        for child in value.values():
            collect_vldb_papers(child, items, limit)
            if len(items) >= limit:
                return
    elif isinstance(value, list):
        for child in value:
            collect_vldb_papers(child, items, limit)
            if len(items) >= limit:
                return


def sample_openalex(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    data = response.json()
    items = []
    for work in data.get("results", [])[:limit]:
        primary_location = work.get("primary_location") or {}
        source_info = primary_location.get("source") or {}
        items.append(
            {
                "title": work.get("title"),
                "year": work.get("publication_year"),
                "doi": work.get("doi"),
                "openalex_id": work.get("id"),
                "source": source_info.get("display_name"),
                "is_oa": (work.get("open_access") or {}).get("is_oa"),
            }
        )
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


def sample_crossref(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    data = response.json()
    items = []
    for work in (data.get("message") or {}).get("items", [])[:limit]:
        title = " ".join(work.get("title") or [])
        container = " ".join(work.get("container-title") or [])
        items.append(
            {
                "title": normalize_ws(title),
                "doi": work.get("DOI"),
                "container": normalize_ws(container),
                "published_year": ((work.get("published-print") or work.get("published-online") or {}).get("date-parts") or [[None]])[0][0],
                "score": work.get("score"),
            }
        )
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


def sample_semantic_scholar(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(
            source,
            status=status,
            http_status=response.status_code,
            content_type=content_type,
            notes=["Semantic Scholar should be used with API-key-aware rate handling in production."],
        )

    data = response.json()
    items = []
    for paper in data.get("data", [])[:limit]:
        items.append(
            {
                "title": paper.get("title"),
                "year": paper.get("year"),
                "venue": paper.get("venue"),
                "paper_id": paper.get("paperId"),
                "external_ids": paper.get("externalIds"),
                "open_access_pdf": paper.get("openAccessPdf"),
            }
        )
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


def sample_openreview(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    data = response.json()
    items = []
    for note in data.get("notes", [])[:limit]:
        content = note.get("content") or {}
        title_value = content.get("title")
        if isinstance(title_value, dict):
            title_value = title_value.get("value")
        pdf_value = content.get("pdf")
        if isinstance(pdf_value, dict):
            pdf_value = pdf_value.get("value")
        items.append(
            {
                "title": title_value,
                "note_id": note.get("id"),
                "venue": content.get("venueid") or content.get("venue"),
                "pdf_hint": pdf_value,
            }
        )
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
        notes=["OpenReview source may need invitation/venue-id discovery before production."] if not items else [],
    )


def sample_rfc_text(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    del limit
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    lines = [normalize_ws(line) for line in response.text.splitlines()[:80]]
    title = next((line for line in lines if "QUIC:" in line or "RFC " in line), lines[0] if lines else "RFC text")
    item = {
        "title_or_header": title,
        "byte_count": len(response.content),
        "line_sample_count": min(len(lines), 80),
    }
    return result(
        source,
        status="ok",
        http_status=response.status_code,
        content_type=content_type,
        item_count=1,
        sample_items=[item],
        notes=["Sampler stores metadata only; production parser should chunk local fetched text."],
    )


def sample_arxiv(
    session: requests.Session,
    source: dict[str, Any],
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = polite_get(
        session,
        source["url"],
        params=source.get("params"),
        policy=policy,
        last_request_by_host=last_request_by_host,
        timeout_seconds=timeout_seconds,
    )
    content_type = response.headers.get("content-type")
    if response.status_code != 200:
        status = "rate_limited" if response.status_code == 429 else "http_error"
        return result(source, status=status, http_status=response.status_code, content_type=content_type)

    entries = re.findall(r"<entry>(.*?)</entry>", response.text, flags=re.S)
    items = []
    for entry in entries[:limit]:
        title_match = re.search(r"<title>(.*?)</title>", entry, flags=re.S)
        id_match = re.search(r"<id>(.*?)</id>", entry, flags=re.S)
        pdf_match = re.search(r'<link[^>]+title="pdf"[^>]+href="([^"]+)"', entry, flags=re.S)
        items.append(
            {
                "title": normalize_ws(title_match.group(1)) if title_match else None,
                "arxiv_url": normalize_ws(id_match.group(1)) if id_match else None,
                "pdf_hint": pdf_match.group(1) if pdf_match else None,
            }
        )
    status = "ok" if items else "empty"
    return result(
        source,
        status=status,
        http_status=response.status_code,
        content_type=content_type,
        item_count=len(items),
        sample_items=items,
    )


HANDLERS = {
    "local_glob": sample_local_glob,
    "yaml_config": sample_yaml_config,
    "engram_workspace_fixture": sample_engram_workspace_fixture,
    "dblp_toc_html": sample_dblp_toc,
    "usenix_technical_sessions": sample_usenix,
    "vldb_volume": sample_vldb,
    "openalex_search": sample_openalex,
    "crossref_query_title": sample_crossref,
    "semantic_scholar_search": sample_semantic_scholar,
    "openreview_notes": sample_openreview,
    "rfc_text": sample_rfc_text,
    "arxiv_query": sample_arxiv,
}


def sample_source(
    repo_root: Path,
    source: dict[str, Any],
    session: requests.Session,
    policy: dict[str, Any],
    last_request_by_host: dict[str, float],
    limit: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    handler = HANDLERS.get(source.get("kind"))
    if handler is None:
        return result(source, status="error", error=f"Unsupported kind: {source.get('kind')}")
    try:
        if source["kind"] in {"local_glob", "yaml_config", "engram_workspace_fixture"}:
            return handler(repo_root, source, limit)
        return handler(session, source, policy, last_request_by_host, limit, timeout_seconds)
    except requests.Timeout as exc:
        return result(source, status="timeout", error=str(exc))
    except requests.RequestException as exc:
        return result(source, status="network_error", error=str(exc))
    except Exception as exc:  # noqa: BLE001 - sampler should record failures and continue.
        return result(source, status="error", error=f"{type(exc).__name__}: {exc}")


def write_coverage_markdown(
    path: Path,
    *,
    generated_at: str,
    config_path: Path,
    ontology_targets: dict[str, Any],
    samples: list[dict[str, Any]],
) -> None:
    observed_by_type: dict[str, list[str]] = {target: [] for target in ontology_targets}
    for sample in samples:
        for hit in sample.get("observed_ontology_hits", []):
            observed_by_type.setdefault(hit, []).append(sample["source_id"])

    lines = [
        "# Memex-SR Source Sample Coverage",
        "",
        f"Generated: `{generated_at}`",
        f"Config: `{config_path}`",
        "",
        "## Source Status",
        "",
        "| Source | Kind | Status | Items | Ontology Hits | Notes |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for sample in samples:
        hits = ", ".join(sample.get("observed_ontology_hits", [])) or "-"
        notes = "; ".join(sample.get("notes", [])) or "-"
        lines.append(
            f"| `{sample['source_id']}` | `{sample['kind']}` | `{sample['status']}` | {sample['item_count']} | {hits} | {notes} |"
        )

    lines.extend(
        [
            "",
            "## Ontology Coverage",
            "",
            "| Ontology Target | Covered By Successful Samples |",
            "| --- | --- |",
        ]
    )
    for target in sorted(ontology_targets):
        covered_by = ", ".join(f"`{source_id}`" for source_id in observed_by_type.get(target, [])) or "-"
        lines.append(f"| `{target}` | {covered_by} |")

    gaps = [target for target in sorted(ontology_targets) if not observed_by_type.get(target)]
    lines.extend(["", "## Current Gaps", ""])
    if gaps:
        for gap in gaps:
            lines.append(f"- `{gap}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Operational Findings", ""])
    for sample in samples:
        if sample["status"] != "ok":
            detail = sample.get("error") or "; ".join(sample.get("notes", [])) or "no sample items"
            lines.append(f"- `{sample['source_id']}` returned `{sample['status']}`: {detail}")
    if all(sample["status"] == "ok" for sample in samples):
        lines.append("- All enabled samples returned at least one item.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="deployments/memex-sr/data_sources.yaml")
    parser.add_argument("--out", default=None)
    parser.add_argument("--coverage", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    config_path = resolve_path(repo_root, args.config)
    config = load_yaml(config_path)
    defaults = config.get("sample_defaults", {})
    limit = args.limit or int(defaults.get("limit_per_source", 5))
    timeout_seconds = args.timeout or int(defaults.get("timeout_seconds", 20))
    out_path = resolve_path(repo_root, args.out or defaults["output_path"])
    coverage_path = resolve_path(repo_root, args.coverage or defaults["coverage_path"])
    policy_path = resolve_path(repo_root, defaults["host_policy_path"])
    policy = load_yaml(policy_path)

    session = requests.Session()
    user_agent = (policy.get("defaults") or {}).get("user_agent", "memex-sr-source-sampler/0.1")
    session.headers.update({"User-Agent": user_agent, "Accept": "application/json,text/html,text/plain,*/*"})
    last_request_by_host: dict[str, float] = {}

    samples = []
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        samples.append(
            sample_source(
                repo_root,
                source,
                session,
                policy,
                last_request_by_host,
                limit,
                timeout_seconds,
            )
        )

    generated_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    output = {
        "generated_at": generated_at,
        "deployment": config.get("deployment"),
        "config_path": str(config_path.relative_to(repo_root)),
        "host_policy_path": str(policy_path.relative_to(repo_root)),
        "limit_per_source": limit,
        "samples": samples,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_coverage_markdown(
        coverage_path,
        generated_at=generated_at,
        config_path=config_path.relative_to(repo_root),
        ontology_targets=config.get("ontology_targets", {}),
        samples=samples,
    )

    ok_count = sum(1 for sample in samples if sample["status"] == "ok")
    print(f"sampled {len(samples)} sources; {ok_count} ok")
    print(f"wrote {out_path}")
    print(f"wrote {coverage_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
