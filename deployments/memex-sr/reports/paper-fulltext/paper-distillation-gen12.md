# Memex-SR Paper Distillation Publish: Generation 12

Generated: `2026-05-20T17:25:00Z`

## Scope

This report records the first source-backed distillation pass over
Memex-SR full-text paper chunks. The goal is to move beyond paper text
retrieval into textbook-like systems research facts: principles,
mechanisms, trade-offs, anti-patterns, and evidence.

Database:
`postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke`

## Extraction Manifest

- Extraction script:
  `deployments/memex-sr/scripts/extract_paper_research_facts.py`
- Extraction output:
  `deployments/memex-sr/manifests/paper_research_facts.jsonl`
- Cache:
  `deployments/memex-sr/.cache/paper_fact_extraction`
- Backend: `openrouter`
- Model: `openai/gpt-5-mini`
- Source generation read for chunks: `10`
- Papers extracted: `10`
- Stable manifest SHA-256:
  `7a550dee6022134a28c565e837866a7e12c6be9b5356bbc312c2e4aedcb3cabb`

Manifest fact counts:

| Fact kind | Count |
|:--|--:|
| evidence | 61 |
| design_principles | 29 |
| mechanisms | 30 |
| trade_offs | 24 |
| anti_patterns | 19 |

The extractor was rerun from cache after fixing timestamp stability; two
cached reruns produced the same manifest hash above.

## Publish

Command shape:

```bash
OKG_DEPLOYMENTS_DIR=/Users/jason/projects/mit/Engram/deployments \
uv --directory external/okg run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke \
  --include paper_research_facts \
  --inline \
  --mode scope_complete \
  --progress \
  --json
```

Generation 11 published the first extraction manifest. Generation 12
republished the same logical facts after the extractor-cache timestamp
fix, retracting and re-adding the 163 nodes with stable manifest
provenance. A no-change rerun after generation 12 appended zero facts and
skipped publish with `reason=no_source_work`.

Recent generation ledger:

| Generation | Status | Nodes added | Edges added | Nodes retracted | Edges retracted |
|--:|:--|--:|--:|--:|--:|
| 12 | published | 163 | 0 | 163 | 0 |
| 11 | published | 163 | 149 | 0 | 0 |
| 10 | published | 2,691 | 5,058 | 791 | 1,369 |

## Live Distilled Fact Counts

Live distilled fact counts at generation 12:

| Subtype | Count |
|:--|--:|
| generic_evidence | 66 |
| design_principle | 33 |
| mechanism | 34 |
| trade_off | 27 |
| anti_pattern | 23 |

The counts include the earlier Cloudcast seed facts plus the 10-paper
distillation batch.

## Literature Provenance Edges

The paper-distillation source emitted ontology-native semantic links:

| Source subtype | Edge | Target subtype | Count |
|:--|:--|:--|--:|
| design_principle | emerged_from | paper | 29 |
| mechanism | cited_in | paper | 30 |
| mechanism | instantiates | design_principle | 38 |
| trade_off | restricts | mechanism | 34 |
| anti_pattern | mitigated_by | mechanism | 32 |

This verifies that extracted principles and mechanisms are connected back
to paper provenance, not just stored as detached summaries.

## Health And Incrementality

`okg doctor` against the generation-12 DSN reports:

- `ok: true`
- no errors
- profile diagnostics clean
- `paper_research_facts` present as a custom Memex-SR source

`okg metrics --source-sync` reports:

- `dlq_count: 0`
- no queued source-sync backlog

A no-change rerun of `paper_research_facts` completed with:

- `nodes_appended: 0`
- `edges_appended: 0`
- publish skipped with `reason=no_source_work`

## Remaining Scale Work

This is the first real extraction pass, not the final corpus. It proves
the complete path:

1. full PDFs are cached and parsed into chunks;
2. chunks are distilled into evidence-backed systems-research facts;
3. facts publish through OKG source adapters;
4. facts link back to papers through ontology-native edges;
5. no-change reruns are incremental.

The next batch should scale extraction across the 100 full-text papers
already cached, then across the broader 2,926 eligible open PDFs with a
venue/year-stratified acquisition schedule.
