## ADDED Requirements

### Requirement: Paper Chunk Distillation Manifest

Memex-SR SHALL provide an offline extraction step that converts
published paper full-text chunks into a deterministic JSONL manifest of
systems-research facts.

#### Scenario: Extracted facts cite paper provenance

- **GIVEN** a published Memex-SR generation with paper `document_chunk`
  nodes
- **WHEN** the extraction step runs for a paper
- **THEN** the emitted manifest row includes the paper id, document id,
  source chunk ids, extractor metadata, and extracted fact arrays.

### Requirement: Paper Research Facts Source

Memex-SR SHALL provide an OKG source adapter that projects paper
distillation manifests into the systems-research ontology without
performing network or LLM calls during publish.

#### Scenario: Source projects typed research facts

- **GIVEN** a valid paper-distillation JSONL manifest
- **WHEN** `okg ingest --include paper_research_facts` runs
- **THEN** the source emits `generic_evidence`, `design_principle`,
  `mechanism`, `trade_off`, and/or `anti_pattern` facts with stable node
  ids and source revisions.

#### Scenario: Source preserves semantic links

- **GIVEN** a manifest row with local references from mechanisms to
  principles, trade-offs to mechanisms, or anti-patterns to mechanisms
- **WHEN** the source projects the row
- **THEN** it emits the corresponding `instantiates`, `restricts`, and
  `mitigated_by` edges using the systems-research ontology.

### Requirement: Distillation Publish Verification

Memex-SR SHALL verify paper-distillation changes with a real published
generation and no-op rerun.

#### Scenario: Published generation increases distilled fact counts

- **GIVEN** a non-empty paper-distillation manifest
- **WHEN** the source publishes successfully
- **THEN** live counts for systems-research fact subtypes increase and
  `okg doctor` remains clean.

#### Scenario: No-change rerun is incremental

- **GIVEN** the same paper-distillation manifest has already been
  published
- **WHEN** the source runs again with no manifest changes
- **THEN** it appends no new facts or skips publish with
  `no_source_work`.
