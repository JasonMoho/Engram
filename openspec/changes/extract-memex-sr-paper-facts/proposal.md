# Extract Memex-SR Paper Facts

## Why This Is Broken

Memex-SR now has a real document layer: paper metadata, cached PDFs,
parsed full text, and thousands of `document_chunk` nodes. But the layer
that Engram needs for scientific discovery is still thin. The graph has
only a handful of `design_principle`, `mechanism`, `trade_off`, and
`anti_pattern` nodes, mostly from the Cloudcast seed pack. Agents can
retrieve text, but they do not yet receive the textbook-like distilled
principles and mechanisms the deployment is supposed to provide.

The incomplete substrate stage is projection from full-text paper chunks
into the systems-research ontology. Source coverage exists; distillation
projection does not.

## What Changes

Add an extraction-output manifest and source adapter for paper-derived
systems-research facts:

- an offline extraction script reads published full-text paper chunks,
  builds evidence-bounded prompts, calls an LLM or cache, and writes a
  JSONL fact manifest;
- the publish path consumes that manifest through a deterministic OKG
  source adapter, with no network calls inside OKG publish;
- extracted facts populate `generic_evidence`, `design_principle`,
  `mechanism`, `trade_off`, and `anti_pattern`;
- every extracted fact carries paper/chunk provenance in attributes, and
  mechanisms/principles link back to papers through existing
  systems-research edge narrowings where possible.

## What Stays Out

- No direct writes to OKG live tables.
- No opaque facts without evidence provenance.
- No benchmark oracle files.
- No attempt to solve canonical deduplication across the whole literature
  in this change. This change establishes the source-backed extraction
  path and a first published batch.

## Verification

Verification must use a real OKG publish generation:

- extraction manifest contains non-zero facts with source paper and chunk
  ids;
- `okg ingest --include paper_research_facts` publishes a generation;
- live graph counts for the four systems-research fact subtypes increase;
- source-run no-op behavior works on a rerun;
- `okg doctor` remains clean.
