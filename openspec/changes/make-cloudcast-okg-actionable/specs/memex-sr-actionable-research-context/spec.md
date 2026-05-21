## ADDED Requirements

### Requirement: Cloudcast OKG Usefulness Diagnostics

The system SHALL distinguish OKG reachability from useful OKG
assistance for Cloudcast benchmark arms.

#### Scenario: Underused OKG run is classified
- **WHEN** an OKG-assisted Cloudcast run completes
- **THEN** the report SHALL include OKG generation id, MCP call count,
  tool names, retrieved node ids, first OKG call time, first code edit
  time, first evaluator call time, and a usage classification.
- **AND** if the run attaches OKG but does not retrieve and cite
  Cloudcast-specific evidence before coding or evaluation, the report
  SHALL classify it as `okg_attached_but_underused`.

#### Scenario: Graph coverage snapshot is recorded
- **WHEN** a Cloudcast OKG arm is prepared
- **THEN** the system SHALL record a pinned-generation coverage snapshot
  for Cloudcast-relevant documents, chunks, papers, design principles,
  mechanisms, trade-offs, anti-patterns, and evidence nodes.

### Requirement: Reviewed Cloudcast Source Corpus

Memex-SR SHALL maintain a reviewed Cloudcast source corpus that can
produce source-backed graph evidence.

#### Scenario: Source manifest is reviewable
- **WHEN** the Cloudcast source manifest is updated
- **THEN** each non-holdout source SHALL include tier, access basis,
  source URL or local path, transfer-to-Cloudcast label, extraction
  targets, and holdout/oracle status.

#### Scenario: First actionable corpus is broad enough
- **WHEN** the first actionable Cloudcast corpus is prepared
- **THEN** it SHALL include at least 20 non-holdout sources spanning
  direct systems comparators, algorithmic foundations, implementation or
  data-structure guidance, and cloud economics or measurement.

#### Scenario: Source publication creates document evidence
- **WHEN** the reviewed source slice is published into Memex-SR
- **THEN** the resulting OKG generation SHALL include non-zero
  `document` and `document_chunk` nodes for the source slice and SHALL
  exclude holdout-only artifacts.

#### Scenario: Source ingestion is incremental
- **WHEN** an unchanged reviewed source slice is ingested twice
- **THEN** the second source run SHALL append zero new live document or
  chunk facts for that source scope, or report a source no-op.

### Requirement: Source-Backed Cloudcast Fact Distillation

Memex-SR SHALL distill actionable Cloudcast research guidance into
typed systems-research facts with provenance.

#### Scenario: Typed facts are actionable
- **WHEN** Cloudcast facts are published
- **THEN** they SHALL represent algorithm families, objectives,
  constraints, decision variables, tractability knobs, implementation
  checks, failure modes, and transfer-to-Cloudcast relevance where
  applicable.

#### Scenario: Typed facts have provenance
- **WHEN** a Cloudcast `DesignPrinciple`, `Mechanism`, `TradeOff`,
  `AntiPattern`, or `Evidence` node is published
- **THEN** it SHALL carry evidence ids that resolve to non-holdout
  source-backed nodes in the pinned generation, plus confidence or
  review state.

#### Scenario: First fact pack is dense enough
- **WHEN** the first actionable fact pack is published
- **THEN** the pinned generation SHALL contain at least 15 Cloudcast
  mechanisms, 10 design principles, 10 trade-offs, 10 anti-patterns,
  and 20 evidence nodes.

#### Scenario: Fact graph supports traversal
- **WHEN** a sampled Cloudcast mechanism, trade-off, or anti-pattern is
  traversed
- **THEN** it SHALL connect to related principles, restrictions,
  mitigations, or source evidence through typed edges.

### Requirement: Context-First Cloudcast Treatment

The primary OKG-assisted Cloudcast treatment SHALL use a generated,
pinned research brief before live MCP tools are evaluated.

#### Scenario: Context brief has provenance and boundaries
- **WHEN** a Cloudcast research brief is generated
- **THEN** it SHALL include OKG generation id, packet hash, source
  hashes, evidence ids, generator version, and a statement excluding
  holdout/oracle artifacts.

#### Scenario: Context brief is actionable
- **WHEN** the brief is appended to a Cloudcast task
- **THEN** it SHALL include problem framing, mechanisms to try,
  tractability knobs, implementation checks, known anti-patterns,
  trade-offs, and an evidence index.

#### Scenario: Context-first run is reproducible
- **WHEN** a context-first Cloudcast arm is launched
- **THEN** run metadata SHALL record the brief path, brief hash, OKG
  generation id, prompt hash, evaluator hash, model, evaluation-call
  budget, result directory, and contamination audit.

### Requirement: Structured MCP Research Protocol

Live OKG MCP Cloudcast arms SHALL require evidence-backed planning
before implementation work.

#### Scenario: MCP protocol is explicit in task prompt
- **WHEN** a structured MCP Cloudcast arm is prepared
- **THEN** the generated task prompt SHALL require graph inspect,
  targeted searches, bounded evidence expansion or equivalent lookups,
  and a short plan citing node ids before code edits or evaluator calls.

#### Scenario: MCP compliance is measurable
- **WHEN** a structured MCP run completes
- **THEN** the report SHALL include tool-call counts, retrieved node ids,
  cited node ids, and whether required evidence use happened before the
  first code edit and first evaluator call.

#### Scenario: MCP treatment remains benchmark-fair
- **WHEN** live MCP tools are exposed to the agent
- **THEN** raw SQL, broad graph dumps, oracle-derived facts, and
  holdout artifacts SHALL be unavailable to the agent-facing treatment.

### Requirement: Cloudcast Research-Memory Harvest

Cloudcast benchmark attempts SHALL be harvestable back into Memex-SR as
research-memory evidence.

#### Scenario: Completed runs become graph facts
- **WHEN** a Cloudcast result directory is harvested
- **THEN** a published OKG generation SHALL include facts for the run,
  attempts, candidate implementation, metric observations, success or
  failure diagnosis, research notes, and workspace artifacts.

#### Scenario: Harvested runs link to evidence used
- **WHEN** a harvested run used a context brief or MCP-retrieved facts
- **THEN** the graph SHALL link the run or candidate implementation to
  the context packet and evidence ids used during the run.

#### Scenario: Harvest is incremental
- **WHEN** an unchanged Cloudcast result directory is harvested twice
- **THEN** the second publish SHALL append zero new live facts for that
  run scope.
