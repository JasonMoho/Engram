# Design

## Source Boundary

The paper-distillation pipeline has two stages:

1. `extract_paper_research_facts.py` runs outside OKG publish. It reads
   a published generation through the read-side database, selects
   evidence chunks for each paper, and writes a JSONL manifest under
   `deployments/memex-sr/manifests/`.
2. `PaperResearchFactsSource` runs inside OKG publish. It reads the JSONL
   manifest and emits deterministic node/edge facts. It does not call the
   network or an LLM.

This keeps LLM latency, retries, and cost outside the substrate publish
critical path while still making the graph state reproducible from a
checked manifest.

## Manifest Shape

Each JSONL row is one paper extraction:

- `paper_id`, `document_id`, `title`, `venue_id`, `year`
- `source_chunk_ids`
- `extractor`, `model`, `extracted_at`, `content_hash`
- `evidence`
- `design_principles`
- `mechanisms`
- `trade_offs`
- `anti_patterns`

Local ids inside one paper row are stable and are namespaced by the
source adapter into graph node ids.

## Graph Projection

The source emits:

- `generic_evidence` nodes for grounded evidence summaries;
- `design_principle` nodes with `domain`, `topic_slugs`, `statement`,
  `why_it_matters`, `strength`, `evidence_ids`, and source provenance;
- `mechanism` nodes with `mechanism_kind`, `applicability`,
  `known_limits`, `topic_slugs`, `evidence_ids`, and source provenance;
- `trade_off` nodes with objective/tension/failure-mode fields;
- `anti_pattern` nodes with failure explanation fields.

The source also emits existing systems-research semantic edges when the
manifest supplies local references:

- `mechanism -instantiates-> design_principle`
- `trade_off -restricts-> mechanism`
- `anti_pattern -mitigated_by-> mechanism`
- `mechanism -cited_in-> paper`
- `design_principle -emerged_from-> paper`

## Incrementality

The source uses the manifest content hash as the source revision and a
record set keyed by emitted node ids. A no-change rerun should append no
new facts and either skip publish or produce zero deltas.

## Risk

LLM extraction quality is the main risk. The source adapter must preserve
provenance and confidence so weak or noisy extraction batches can be
replaced by better manifests without changing the OKG substrate.
