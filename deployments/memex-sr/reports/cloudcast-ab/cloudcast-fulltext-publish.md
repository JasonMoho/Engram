# Cloudcast Full-Text Publish Check

Generated: `2026-05-20T16:25:49+00:00`

## Acquisition

- Acquisition manifest: `deployments/memex-sr/manifests/cloudcast_acquired_assets.jsonl`
- Reviewed non-holdout records: `29`
- Available local full-text/operator files: `16`
- Open fetches: `12` attempted, `12` available after URL repair
- Operator/local files: `4`
- MIT/manual or metadata-only records queued, not counted as ingested: `13`

## Published Generation

- DSN: `postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke`
- Published generation: `8`
- Source: `cloudcast_documents`
- Source facts appended: `203` nodes, `316` edges
- Source stats: `29` records, `16` documents, `158` chunks, `0` parse failures
- Generation status: `published`
- Generation delta: `203` nodes added, `316` edges added, `0` retractions
- `okg doctor`: `ok=true`, no errors, no RED findings

## Live Cloudcast Slice

Cloudcast-filtered live nodes at generation `8`:

| Subtype | Count |
|:--|--:|
| `document_asset` | 29 |
| `document` | 16 |
| `document_chunk` | 158 |
| `design_principle` | 4 |
| `mechanism` | 4 |
| `trade_off` | 3 |
| `anti_pattern` | 4 |
| `generic_evidence` | 5 |

Chunk counts by source:

| Source | Chunks |
|:--|--:|
| `cloud-economics:gcp-network-pricing` | 54 |
| `systems:bullet` | 32 |
| `algorithms:column-generation` | 10 |
| `implementation:or-tools-min-cost-flow` | 9 |
| `algorithms:benders-decomposition` | 7 |
| `cloudcast:evaluator` | 7 |
| `cloudcast:simulator` | 7 |
| `systems:bittorrent` | 6 |
| `implementation:networkx-shortest-paths` | 6 |
| `cloud-economics:azure-bandwidth` | 6 |
| `cloud-economics:aws-data-transfer` | 4 |
| `cloudcast:fair-task-prompt` | 4 |
| `cloudcast:initial-program` | 2 |
| `systems:skyplane` | 2 |
| `implementation:scipbook` | 1 |
| `implementation:pulp` | 1 |

## Incrementality

Immediate no-change rerun:

- `nodes_appended=0`
- `edges_appended=0`
- `retract_n=0`
- `retract_e=0`
- `source_stats.no_op=true`
- publish skipped with `reason=no_source_work`

This check means the current Cloudcast document source is cache-backed,
publish-safe, and delta-proportional for unchanged acquisition output.
