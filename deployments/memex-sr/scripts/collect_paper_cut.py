#!/usr/bin/env python3
"""Collect a first real Memex-SR paper cut from reachable metadata sources."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html as html_lib
import json
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import urljoin

from lxml import html
import requests
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = REPO_ROOT / "deployments/memex-sr/manifests/paper_cut.json"
USER_AGENT = "memex-sr-paper-cut/0.1 (mailto:pkarimib@mit.edu)"


USENIX_TARGETS = [
    ("osdi", "OSDI", "Operating Systems Design and Implementation", "osdi"),
    ("nsdi", "NSDI", "Networked Systems Design and Implementation", "nsdi"),
    ("usenix_atc", "USENIX ATC", "USENIX Annual Technical Conference", "atc"),
]


OPENALEX_SOURCES = [
    ("sigmod", "SIGMOD", "Proceedings of the ACM on Management of Data", "S4387289859"),
    ("pvldb", "PVLDB", "Proceedings of the VLDB Endowment", "S4210226185"),
    ("usenix_atc", "USENIX ATC", "USENIX Annual Technical Conference", "S4306421113"),
    ("cidr", "CIDR", "Conference on Innovative Data Systems Research", "S4306418070"),
    ("pods", "PODS", "Symposium on Principles of Database Systems", "S4306420993"),
    ("icde", "ICDE", "Proceedings - International Conference on Data Engineering", "S4210210321"),
    ("icde", "ICDE", "International Conference on Data Engineering", "S4306419321"),
    ("icde", "ICDE", "IEEE 38th International Conference on Data Engineering", "S4363607857"),
    ("edbt", "EDBT", "Extending Database Technology", "S4306418406"),
    ("eurosys", "EuroSys", "European Conference on Computer Systems", "S4306418317"),
    ("hotnets", "HotNets", "Hot Topics in Networks", "S4306418542"),
]


def norm_ws(value: str | None) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(value or "")).strip()


def slugify(value: str, *, max_len: int = 80) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_len].strip("-") or hashlib.sha1(value.encode()).hexdigest()[:12]


def person_id(name: str) -> str:
    return f"person:author:{slugify(name, max_len=96)}"


def doi_id(doi: str) -> str:
    doi = doi.lower().removeprefix("https://doi.org/").removeprefix("doi:")
    return "paper:doi:" + re.sub(r"[^a-z0-9._/-]+", "-", doi).strip("-")


def paper_fallback_id(venue_id: str, year: int, title: str) -> str:
    return f"paper:{venue_id}:{year}:{slugify(title)}"


def asset_id(paper_id: str, url: str, kind: str) -> str:
    digest = hashlib.sha1(f"{paper_id}|{kind}|{url}".encode()).hexdigest()[:16]
    return f"document_asset:{digest}"


def load_venues() -> list[dict[str, Any]]:
    data = yaml.safe_load((REPO_ROOT / "deployments/memex-sr/venues.yaml").read_text()) or {}
    out: list[dict[str, Any]] = []
    for group_id, group in (data.get("venue_groups") or {}).items():
        for venue in group.get("venues") or []:
            out.append(
                {
                    "venue_id": venue["id"],
                    "name": venue["name"],
                    "short_name": venue["short_name"],
                    "series": venue.get("series"),
                    "domain": group_id,
                    "publication_series_id": f"publication_series:{venue['id']}",
                }
            )
    return out


class PaperAccumulator:
    def __init__(self) -> None:
        self.records: dict[tuple[str, int, str], dict[str, Any]] = {}

    def add(self, record: dict[str, Any]) -> None:
        title = norm_ws(record.get("title"))
        if not title:
            return
        year = int(record.get("year") or 0)
        venue_id = str(record.get("venue_id") or "unknown")
        key = (venue_id, year, slugify(title, max_len=120))
        existing = self.records.get(key)
        if existing is None:
            record["title"] = title
            record["authors"] = normalize_authors(record.get("authors") or [])
            record["assets"] = record.get("assets") or []
            record["source_records"] = record.get("source_records") or []
            self.records[key] = record
            return
        merge_record(existing, record)

    def papers(self) -> list[dict[str, Any]]:
        papers = []
        for record in self.records.values():
            doi = record.get("doi")
            if doi:
                record["paper_id"] = doi_id(str(doi))
            elif record.get("openalex_id"):
                record["paper_id"] = "paper:openalex:" + str(record["openalex_id"]).rsplit("/", 1)[-1].lower()
            else:
                record["paper_id"] = paper_fallback_id(record["venue_id"], int(record["year"]), record["title"])
            assets = []
            seen_assets = set()
            for asset in record.get("assets") or []:
                url = asset.get("url")
                kind = asset.get("asset_kind") or "landing_page"
                if not url or (kind, url) in seen_assets:
                    continue
                seen_assets.add((kind, url))
                assets.append(
                    {
                        "asset_id": asset_id(record["paper_id"], url, kind),
                        "asset_kind": kind,
                        "url": url,
                        "access_basis": asset.get("access_basis", "metadata_only"),
                        "source": asset.get("source"),
                        "downloaded": False,
                    }
                )
            record["assets"] = assets
            papers.append(record)
        return sorted(papers, key=lambda p: (p.get("venue_id") or "", int(p.get("year") or 0), p.get("title") or ""))


def normalize_authors(authors: list[Any]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for idx, author in enumerate(authors, start=1):
        name = norm_ws(author.get("display_name") if isinstance(author, dict) else str(author))
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        out.append({"person_id": person_id(name), "display_name": name, "author_position": idx})
    return out


def merge_record(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
    for field in ["doi", "openalex_id", "publication_date", "abstract"]:
        if not existing.get(field) and incoming.get(field):
            existing[field] = incoming[field]
    existing_sources = {(r.get("source"), r.get("source_id")) for r in existing.get("source_records", [])}
    for source in incoming.get("source_records") or []:
        key = (source.get("source"), source.get("source_id"))
        if key not in existing_sources:
            existing.setdefault("source_records", []).append(source)
            existing_sources.add(key)
    existing_author_names = {a["display_name"].lower() for a in existing.get("authors", [])}
    for author in normalize_authors(incoming.get("authors") or []):
        if author["display_name"].lower() not in existing_author_names:
            author["author_position"] = len(existing.get("authors", [])) + 1
            existing.setdefault("authors", []).append(author)
            existing_author_names.add(author["display_name"].lower())
    existing.setdefault("assets", []).extend(incoming.get("assets") or [])


def split_author_text(value: str) -> list[str]:
    value = re.sub(r"\bAwarded .*", "", value, flags=re.I).strip()
    value = value.strip(" ,;")
    if not value:
        return []
    value = value.replace(", and ", ", ")
    value = re.sub(r"\s+and\s+", ", ", value)
    return [part.strip() for part in value.split(",") if part.strip()]


def collect_usenix(session: requests.Session, acc: PaperAccumulator, status: list[dict[str, Any]]) -> None:
    for venue_id, short_name, venue_name, slug in USENIX_TARGETS:
        for year in range(2022, 2027):
            suffix = str(year)[-2:]
            conf = f"{slug}{suffix}"
            url = f"https://www.usenix.org/conference/{conf}/technical-sessions"
            try:
                resp = session.get(url, timeout=25)
            except requests.RequestException as exc:
                status.append({"source": "usenix", "venue_id": venue_id, "year": year, "status": "error", "error": str(exc)})
                continue
            if resp.status_code != 200:
                status.append({"source": "usenix", "venue_id": venue_id, "year": year, "status": f"http_{resp.status_code}"})
                continue
            tree = html.fromstring(resp.text)
            count = 0
            for article in tree.xpath('//article[contains(concat(" ", normalize-space(@class), " "), " node-paper ")]'):
                link = article.xpath('.//h2//a[1]')
                if not link:
                    continue
                title = norm_ws(" ".join(link[0].xpath(".//text()")))
                href = link[0].get("href")
                if not title or not href or f"/conference/{conf}/presentation/" not in href:
                    continue
                people = []
                for p in article.xpath('.//*[contains(@class, "field-name-field-paper-people-text")]//p'):
                    direct = norm_ws(" ".join(p.xpath("./text()")))
                    if direct:
                        people.extend(split_author_text(direct))
                        break
                abstract = norm_ws(" ".join(article.xpath('.//*[contains(@class, "field-name-field-paper-description-long")]//text()')))
                landing = urljoin(url, href)
                source_id = href.rsplit("/", 1)[-1]
                acc.add(
                    {
                        "venue_id": venue_id,
                        "venue_short_name": short_name,
                        "venue_name": venue_name,
                        "year": year,
                        "title": title,
                        "abstract": abstract,
                        "authors": people,
                        "assets": [
                            {
                                "asset_kind": "landing_page",
                                "url": landing,
                                "access_basis": "open",
                                "source": "usenix",
                            },
                            {
                                "asset_kind": "pdf_url_hint",
                                "url": f"https://www.usenix.org/system/files/{conf}-{source_id}.pdf",
                                "access_basis": "open",
                                "source": "usenix_inferred",
                            },
                        ],
                        "source_records": [{"source": "usenix", "source_id": source_id, "url": landing}],
                    }
                )
                count += 1
            status.append({"source": "usenix", "venue_id": venue_id, "year": year, "status": "ok", "record_count": count, "url": url})
            time.sleep(1.0)


def collect_vldb(session: requests.Session, acc: PaperAccumulator, status: list[dict[str, Any]]) -> None:
    volume_years = {15: 2022, 16: 2023, 17: 2024, 18: 2025, 19: 2026}
    for volume, year in volume_years.items():
        url = f"https://www.vldb.org/pvldb/volumes/{volume}/"
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as exc:
            status.append({"source": "pvldb", "year": year, "status": "error", "error": str(exc)})
            continue
        if resp.status_code != 200:
            status.append({"source": "pvldb", "year": year, "status": f"http_{resp.status_code}", "url": url})
            continue
        papers: list[dict[str, Any]] = []
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, flags=re.S)
        if match:
            data = json.loads(html_lib.unescape(match.group(1)))
            collect_vldb_records(data, papers)
        for row in papers:
            title = norm_ws(row.get("Paper Title"))
            paper_id = row.get("Paper ID")
            authors = split_author_text(norm_ws(row.get("Author Names")))
            pdf_url = f"https://www.vldb.org/pvldb/{paper_id}.pdf" if paper_id else None
            assets = []
            if pdf_url:
                assets.append({"asset_kind": "pdf_url_hint", "url": pdf_url, "access_basis": "open", "source": "pvldb"})
            acc.add(
                {
                    "venue_id": "pvldb",
                    "venue_short_name": "PVLDB",
                    "venue_name": "Proceedings of the VLDB Endowment",
                    "year": year,
                    "title": title,
                    "abstract": norm_ws(row.get("Abstract")),
                    "authors": authors,
                    "assets": assets,
                    "source_records": [{"source": "pvldb", "source_id": paper_id, "url": url}],
                }
            )
        status.append({"source": "pvldb", "venue_id": "pvldb", "year": year, "status": "ok", "record_count": len(papers), "url": url})
        time.sleep(1.0)


def collect_vldb_records(value: Any, papers: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if "Paper Title" in value and "Paper ID" in value:
            papers.append(value)
            return
        for child in value.values():
            collect_vldb_records(child, papers)
    elif isinstance(value, list):
        for child in value:
            collect_vldb_records(child, papers)


def collect_openalex(session: requests.Session, acc: PaperAccumulator, status: list[dict[str, Any]]) -> None:
    for venue_id, short_name, source_name, source_id in OPENALEX_SOURCES:
        cursor = "*"
        total = 0
        while cursor:
            params = {
                "filter": f"primary_location.source.id:{source_id},from_publication_date:2022-01-01,to_publication_date:2026-12-31",
                "per-page": 200,
                "cursor": cursor,
            }
            try:
                resp = session.get("https://api.openalex.org/works", params=params, timeout=30)
            except requests.RequestException as exc:
                status.append({"source": "openalex", "venue_id": venue_id, "source_id": source_id, "status": "error", "error": str(exc)})
                break
            if resp.status_code != 200:
                status.append({"source": "openalex", "venue_id": venue_id, "source_id": source_id, "status": f"http_{resp.status_code}"})
                break
            payload = resp.json()
            results = payload.get("results") or []
            for work in results:
                title = norm_ws(work.get("title") or work.get("display_name"))
                year = work.get("publication_year")
                if not title or not year or int(year) < 2022 or int(year) > 2026:
                    continue
                authors = [
                    (auth.get("author") or {}).get("display_name")
                    for auth in work.get("authorships") or []
                    if (auth.get("author") or {}).get("display_name")
                ]
                primary = work.get("primary_location") or {}
                assets = []
                if primary.get("landing_page_url"):
                    assets.append({"asset_kind": "landing_page", "url": primary["landing_page_url"], "access_basis": "metadata_only", "source": "openalex"})
                if primary.get("pdf_url"):
                    assets.append({"asset_kind": "pdf_url_hint", "url": primary["pdf_url"], "access_basis": "open", "source": "openalex"})
                acc.add(
                    {
                        "venue_id": venue_id,
                        "venue_short_name": short_name,
                        "venue_name": source_name,
                        "year": int(year),
                        "publication_date": work.get("publication_date"),
                        "title": title,
                        "abstract": openalex_abstract(work.get("abstract_inverted_index")),
                        "doi": work.get("doi"),
                        "openalex_id": work.get("id"),
                        "authors": authors,
                        "assets": assets,
                        "source_records": [{"source": "openalex", "source_id": work.get("id"), "url": work.get("id")}],
                    }
                )
                total += 1
            cursor = (payload.get("meta") or {}).get("next_cursor")
            if not results or not cursor:
                break
            time.sleep(1.0)
        status.append({"source": "openalex", "venue_id": venue_id, "source_id": source_id, "status": "ok", "record_count": total})
        time.sleep(1.0)


def openalex_abstract(index: dict[str, list[int]] | None) -> str | None:
    if not isinstance(index, dict):
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            positioned.append((int(pos), word))
    return " ".join(word for _, word in sorted(positioned)) if positioned else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--no-openalex", action="store_true")
    parser.add_argument("--no-usenix", action="store_true")
    parser.add_argument("--no-vldb", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_path = Path(args.out)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/html,*/*"})
    acc = PaperAccumulator()
    source_status: list[dict[str, Any]] = []
    if not args.no_usenix:
        collect_usenix(session, acc, source_status)
    if not args.no_vldb:
        collect_vldb(session, acc, source_status)
    if not args.no_openalex:
        collect_openalex(session, acc, source_status)

    doc = {
        "version": 1,
        "pack_id": "systems-db-2022-2026",
        "pack_name": "Systems and databases papers, 2022-2026",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "target_years": [2022, 2023, 2024, 2025, 2026],
        "venues": load_venues(),
        "sources": ["usenix", "pvldb", "openalex"],
        "source_status": source_status,
        "papers": acc.papers(),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"papers={len(doc['papers'])}")
    for source in sorted({entry["source"] for entry in source_status}):
        count = sum(int(entry.get("record_count") or 0) for entry in source_status if entry["source"] == source)
        print(f"{source}_records={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
