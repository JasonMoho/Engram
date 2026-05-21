# Memex-SR Paper Full-Text Publish: Generation 10

Generated: `2026-05-20T17:15:00Z`

## Scope

This report records the first materially large Memex-SR paper full-text
publish. It is intentionally separate from the earlier Cloudcast source
slice: this run uses the systems/database paper cut and cached PDFs as
the source of truth.

Database:
`postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke`

Deployment:
`deployments/memex-sr`

## Acquisition

- Input manifest: `deployments/memex-sr/manifests/paper_cut.json`
- Acquisition manifest:
  `deployments/memex-sr/manifests/paper_fulltext_assets.jsonl`
- PDF cache: `deployments/memex-sr/.cache/paper_fulltext`
- Cache size after this batch: `313M`
- Dry-run eligible open PDF assets from the paper cut: `2,926`
- Batch manifest records: `100`
- Available local PDFs: `100`
- Fetch failures in this batch: `0`
- Acquisition states: `73` fetched, `27` reused from cache
- Total bytes in the 100-paper manifest: `289,357,942`

Venue/year coverage in this batch:

| Venue | Year | Papers |
|:--|--:|--:|
| nsdi | 2022 | 78 |
| nsdi | 2023 | 22 |

This is still a first batch, not the full target corpus. The acquisition
script now has the right mechanics for the broader run: cache-first
downloads, host allow-listing, USENIX landing-page PDF resolution,
content hashes, byte counts, and explicit failure records. The next
batch should stratify by venue and year instead of walking the manifest
in order, because the current first 100 papers are NSDI-heavy.

## Publish

Command shape:

```bash
OKG_DEPLOYMENTS_DIR=/Users/jason/projects/mit/Engram/deployments \
uv --directory external/okg run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke \
  --include paper_fulltext_documents \
  --inline \
  --mode scope_complete \
  --progress \
  --json
```

Published generation:

| Generation | Status | Nodes added | Edges added | Nodes retracted | Edges retracted |
|--:|:--|--:|--:|--:|--:|
| 10 | published | 2,691 | 5,058 | 791 | 1,369 |

Source stats for `paper_fulltext_documents`:

| Metric | Value |
|:--|--:|
| manifest records | 100 |
| available records | 100 |
| documents emitted | 100 |
| chunks emitted | 3,041 |
| parse failures | 0 |
| source nodes appended | 2,691 |
| source edges appended | 5,058 |

## Live Graph Counts

Live graph totals at generation 10:

| Metric | Count |
|:--|--:|
| live nodes | 29,344 |
| live edges | 46,242 |

Top live node subtypes:

| Subtype | Count |
|:--|--:|
| person | 13,499 |
| document_asset | 7,324 |
| paper | 4,782 |
| document_chunk | 3,430 |
| document | 138 |
| entity_mention | 93 |
| venue_edition | 24 |
| venue | 16 |
| publication_series | 16 |
| generic_evidence | 5 |
| mechanism | 4 |
| design_principle | 4 |
| anti_pattern | 4 |
| trade_off | 3 |

Live source-pack counts for `systems-db-2022-2026`:

| Subtype | Count |
|:--|--:|
| document_asset | 100 |
| document | 100 |
| document_chunk | 3,041 |

Top live edge types:

| Edge type | Count |
|:--|--:|
| authored_by | 27,120 |
| contains | 10,765 |
| published_in | 4,782 |
| member_of | 3,539 |
| references | 22 |
| instantiates | 5 |
| restricts | 5 |
| mitigated_by | 4 |

## Retrieval Check

The generation contains searchable full-text paper chunks. A direct
chunk-text check for RDMA/congestion-control terms returns paper-backed
chunks such as:

- `chunk:paper-fulltext:0b9dbe1dc6db3910f551`
  from
  `paper:nsdi:2023:a-high-speed-stateful-packet-processing-approach-for-tbps-programmable-switches`
- `chunk:paper-fulltext:1a025b2351e863de178e`
  from
  `paper:nsdi:2023:bolt-sub-rtt-congestion-control-for-ultra-low-latency`

This verifies that the graph contains extracted PDF text, not only paper
metadata.

## Health And Incrementality

`okg doctor` against the generation-10 DSN reports:

- `ok: true`
- no errors
- profile diagnostics clean
- expected `systems-research` modules present, with `engram_runs` as a
  custom addition
- expected profile sources present, with Memex-SR custom sources

`okg metrics --source-sync` reports:

- `dlq_count: 0`
- no queued source-sync backlog

A no-change rerun of `paper_fulltext_documents` completed with no new
facts and skipped publish with `reason=no_source_work`.

## Remaining Gap

This generation fixes the document-layer problem: the graph now has
thousands of live paper chunks from full PDFs. It does not yet fix the
distillation-layer problem. The design-knowledge layer is still thin:
`design_principle`, `mechanism`, `trade_off`, and `anti_pattern` are
still mostly Cloudcast seed facts.

The next source should be a paper-distillation source over the full-text
chunks that emits:

- `generic_evidence` nodes pointing at paper/chunk provenance;
- `design_principle` nodes with `domain`, `topic_slugs`, `statement`,
  `why_it_matters`, and `evidence_ids`;
- `mechanism` nodes with `mechanism_kind` values including `algorithm`,
  `data_structure`, `protocol`, `architecture`, and `design_pattern`;
- `trade_off` nodes tied to mechanisms through `restricts`;
- `anti_pattern` nodes tied to mechanisms through `mitigated_by`.

The first production target should be the 100-paper batch above, then a
stratified multi-venue batch across NSDI, SIGCOMM, SOSP, OSDI, EuroSys,
VLDB, SIGMOD, CIDR, and related systems/database venues.
