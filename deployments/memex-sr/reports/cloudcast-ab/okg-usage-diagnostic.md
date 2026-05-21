# Cloudcast OKG Usage Diagnostic

Generated: `2026-05-20T16:04:31+00:00`

Result dir: `/Users/jason/projects/mit/Engram/results/codex_okg_mcp_cloudcast/20260520T123410Z`
Classification: `okg_attached_but_underused`
OKG generation: `7`

## Score

- Success: `True`
- Score: `0.0016020933233331096`
- Inferred total cost: `623.183364`
- Evaluation calls: `2`

## OKG Usage

- MCP calls: `3`
- Tools: `{"inspect": 1, "search": 2}`
- Retrieved Cloudcast node ids: `5`
- Cited Cloudcast node ids in agent messages: `0`
- Event indexes: `{"first_candidate_edit": 59, "first_evaluator_call": 66, "first_mcp_call": 3}`
- Usage checks: `{"cited_cloudcast_evidence": false, "evidence_before_first_edit": true, "evidence_before_first_evaluation": true, "retrieved_cloudcast_evidence": true}`

### Retrieved Cloudcast Nodes

- `anti_pattern:cloudcast:edge-price-only-objective`
- `design_principle:cloudcast:model-capacity-before-price`
- `design_principle:cloudcast:optimize-shared-structure-first`
- `generic_evidence:cloudcast:benchmark-objective`
- `generic_evidence:cloudcast:evaluator-shared-edge-charge`

## Coverage Snapshot

| Subtype | Cloudcast-relevant count |
|:--|--:|
| `document` | 4 |
| `document_chunk` | 57 |
| `paper` | 1 |
| `design_principle` | 4 |
| `mechanism` | 4 |
| `trade_off` | 3 |
| `anti_pattern` | 4 |
| `generic_evidence` | 5 |

## Interpretation

This diagnostic treats attached-but-optional MCP access as insufficient. A useful OKG-assisted run should retrieve Cloudcast-specific evidence, cite it in a plan or final reasoning, and do so before coding or evaluator calls.
