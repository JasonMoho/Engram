"""Manifest-backed paper source for the Memex-SR corpus cut."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from okg.substrate.errors import SubstrateError
from okg.substrate.library.sources.base import (
    EdgeFact,
    EdgeKey,
    NodeFact,
    RecordEmission,
    RecordNode,
    RecordSet,
    SourceHealth,
    SourceRun,
)


def _sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _node(
    node_id: str,
    subtype: str,
    attrs: dict[str, Any],
    revision: dict[str, Any],
) -> NodeFact:
    return NodeFact(
        node_id=node_id,
        subtype=subtype,
        attrs=attrs,
        source_record_id={"id": node_id},
        source_revision=revision,
    )


def _edge(
    src: str,
    edge_type: str,
    dst: str,
    revision: dict[str, Any],
    attrs: dict[str, Any] | None = None,
) -> EdgeFact:
    return EdgeFact(
        src=src,
        dst=dst,
        edge_type=edge_type,
        attrs=attrs or {},
        source_record_id={"edge": f"{src}|{edge_type}|{dst}"},
        source_revision=revision,
    )


@dataclass
class PaperCutSource:
    """Emit papers, authors, venues, editions, and asset hints."""

    name: str = "paper_cut"
    profile: str = "reference_catalog"
    manifest_path: Path | str = ""

    def run(self, run_id: str, *, mode: str = "cursor") -> SourceRun:
        path = Path(self.manifest_path)
        if not path.is_file():
            raise SubstrateError(
                f"paper cut manifest not found: {path}",
                data={"manifest_path": str(path)},
            )
        doc = json.loads(path.read_text(encoding="utf-8"))
        revision = {"content_hash": _sha(doc)}
        facts = list(self._facts(doc, revision))
        return SourceRun(
            facts=facts,
            completed_scope=True,
            run_mode=mode,
            record_set=self._record_set_from_facts(facts),
            health=SourceHealth(
                status="ok",
                mode="manifest",
                record_count=sum(1 for fact in facts if isinstance(fact, NodeFact)),
                content_hash=revision["content_hash"],
                cache_path=str(path),
                reason=f"paper_count={len(doc.get('papers') or [])}",
            ),
        )

    @staticmethod
    def _record_set_from_facts(
        facts: list[NodeFact | EdgeFact],
    ) -> RecordSet:
        records: dict[str, RecordEmission] = {}
        nodes: dict[str, NodeFact] = {
            fact.node_id: fact
            for fact in facts
            if isinstance(fact, NodeFact)
        }
        for node in nodes.values():
            records[node.node_id] = RecordEmission(
                primary=RecordNode(
                    node_id=node.node_id,
                    subtype=node.subtype,
                    source_record_id=node.source_record_id,
                    source_revision=node.source_revision,
                )
            )
        for edge in (fact for fact in facts if isinstance(fact, EdgeFact)):
            record_key = edge.src if edge.src in nodes else edge.dst
            records.setdefault(record_key, RecordEmission()).edges.append(
                EdgeKey(
                    src=edge.src,
                    dst=edge.dst,
                    edge_type=edge.edge_type,
                    attrs=edge.attrs,
                    provenance=edge.provenance,
                    confidence=edge.confidence,
                    source_record_id=edge.source_record_id,
                    source_revision=edge.source_revision,
                )
            )
        return RecordSet(records=records)

    def _facts(
        self,
        doc: dict[str, Any],
        revision: dict[str, Any],
    ) -> Iterable[NodeFact | EdgeFact]:
        pack_id = doc.get("pack_id", "systems-db-2022-2026")
        corpus_pack_id = f"corpus_pack:{pack_id}"
        yield _node(
            corpus_pack_id,
            "corpus_pack",
            {
                "pack_id": pack_id,
                "name": doc.get("pack_name", pack_id),
                "target_years": doc.get("target_years") or [],
                "source_count": len(doc.get("sources") or []),
                "paper_count": len(doc.get("papers") or []),
                "text": f"{pack_id} paper corpus cut with {len(doc.get('papers') or [])} papers.",
            },
            revision,
        )

        snapshot_id = f"corpus_coverage_snapshot:{pack_id}:latest"
        yield _node(
            snapshot_id,
            "corpus_coverage_snapshot",
            {
                "snapshot_id": snapshot_id,
                "pack_id": pack_id,
                "generated_at": doc.get("generated_at"),
                "paper_count": len(doc.get("papers") or []),
                "source_status": doc.get("source_status") or [],
                "text": f"Coverage snapshot for {pack_id}.",
            },
            revision,
        )
        yield _edge(snapshot_id, "references", corpus_pack_id, revision)

        for venue in doc.get("venues") or []:
            series_id = venue.get("publication_series_id") or f"publication_series:{venue['venue_id']}"
            venue_id = venue["venue_id"]
            yield _node(
                series_id,
                "publication_series",
                {
                    "series_id": series_id,
                    "name": venue.get("series") or venue.get("name"),
                    "short_name": venue.get("short_name"),
                    "venue_id": venue_id,
                    "text": venue.get("name") or venue_id,
                },
                revision,
            )
            yield _node(
                venue_id,
                "venue",
                {
                    "venue_id": venue_id,
                    "name": venue.get("name"),
                    "short_name": venue.get("short_name"),
                    "domain": venue.get("domain"),
                    "text": venue.get("name") or venue_id,
                },
                revision,
            )
            yield _edge(corpus_pack_id, "contains", venue_id, revision)
            yield _edge(venue_id, "member_of", series_id, revision)

        emitted_editions: set[str] = set()
        emitted_people: set[str] = set()
        emitted_assets: set[str] = set()
        for paper in doc.get("papers") or []:
            venue_id = paper.get("venue_id")
            year = paper.get("year")
            if venue_id and year:
                edition_id = f"venue_edition:{venue_id}:{year}"
                if edition_id not in emitted_editions:
                    emitted_editions.add(edition_id)
                    yield _node(
                        edition_id,
                        "venue_edition",
                        {
                            "edition_id": edition_id,
                            "venue_id": venue_id,
                            "year": year,
                            "name": f"{paper.get('venue_short_name') or venue_id} {year}",
                            "text": f"{paper.get('venue_short_name') or venue_id} {year}",
                        },
                        revision,
                    )
                    yield _edge(venue_id, "contains", edition_id, revision)

            paper_id = paper["paper_id"]
            attrs = {
                key: value
                for key, value in paper.items()
                if key not in {"authors", "assets", "source_records"}
            }
            attrs["text"] = " ".join(
                part
                for part in [
                    str(paper.get("title") or ""),
                    str(paper.get("abstract") or ""),
                    str(paper.get("venue_short_name") or ""),
                    str(paper.get("year") or ""),
                ]
                if part
            )
            attrs["source_records"] = paper.get("source_records") or []
            yield _node(paper_id, "paper", attrs, revision)
            if venue_id and year:
                yield _edge(paper_id, "published_in", f"venue_edition:{venue_id}:{year}", revision)

            for author in paper.get("authors") or []:
                person_id = author["person_id"]
                if person_id not in emitted_people:
                    emitted_people.add(person_id)
                    yield _node(
                        person_id,
                        "person",
                        {
                            "person_id": person_id,
                            "display_name": author.get("display_name"),
                            "text": author.get("display_name"),
                        },
                        revision,
                    )
                yield _edge(
                    paper_id,
                    "authored_by",
                    person_id,
                    revision,
                    attrs={"author_position": author.get("author_position")},
                )

            for asset in paper.get("assets") or []:
                asset_id = asset["asset_id"]
                if asset_id not in emitted_assets:
                    emitted_assets.add(asset_id)
                    yield _node(
                        asset_id,
                        "document_asset",
                        {
                            **asset,
                            "text": " ".join(
                                part
                                for part in [
                                    str(asset.get("asset_kind") or ""),
                                    str(asset.get("url") or ""),
                                    str(paper.get("title") or ""),
                                ]
                                if part
                            ),
                        },
                        revision,
                    )
                yield _edge(paper_id, "contains", asset_id, revision)
