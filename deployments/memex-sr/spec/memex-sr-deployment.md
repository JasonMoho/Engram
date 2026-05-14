## ADDED Requirements

### Requirement: Memex-SR Deployment Manifest

The system SHALL ship a substrate deployment named `memex-sr`
that is forked from the memex paper/distillation stack but scoped to
recent systems and database research. The deployment SHALL use a
dedicated Postgres DSN, SHALL not read from the memex substrate DB as a
source, and SHALL not include broad memex methodology, HEP, or legacy
paper-cache sources in its default source registry.

#### Scenario: Deployment loads independently
- **WHEN** the memex-sr deployment manifest is loaded
- **THEN** every referenced path SHALL exist
- **AND** catalog composition SHALL succeed against a clean database
- **AND** no default source SHALL require the memex live graph.

#### Scenario: Separate publish state
- **WHEN** memex-sr publishes a generation
- **THEN** the generation SHALL be recorded under deployment name
  `memex-sr`
- **AND** the publish SHALL not alter `memex` generations, source
  progress, jobs, or live rows.

### Requirement: Proper Extensible Ontology

The deployment SHALL define literature, full-text, evidence, and
distillation graph shape through LinkML/catalog-composed ontology
modules, deployment bridge narrowings, and invariants. Sources and
extractors SHALL emit only node subtypes and edge routes accepted by the
active catalog. High-cardinality labels SHALL remain attributes unless a
traversal use case justifies a node subtype.

#### Scenario: Catalog composition accepts core ontology
- **WHEN** the memex-sr catalog is loaded against a clean
  database
- **THEN** corpus-governance, literature, full-text, evidence,
  distillation, Engram research-memory, person, concept, and extraction
  modules SHALL compose successfully
- **AND** required bridge narrowings for paper, document, chunk,
  evidence, claim, topic, section, corpus pack, and Engram artifact
  traversal SHALL be active.

#### Scenario: Invalid edge route is rejected
- **WHEN** a source emits an edge whose source subtype, edge archetype,
  and destination subtype are not declared in active narrowings
- **THEN** insertion SHALL fail with a narrowing violation
- **AND** the source SHALL not silently fall back to a weaker edge or
  attr-only representation.

#### Scenario: Ontology extension proves real output
- **WHEN** a collaborator adds a new ontology module or bridge narrowing
- **THEN** the extension SHALL include a fixture source or fixture
  extractor that emits the new shape
- **AND** verification SHALL run a real publish and confirm the expected
  nodes and edges land in `nodes_live` and `edges_live`.

### Requirement: DBOS-Compatible Fast Execution

High-volume memex-sr work SHALL follow DBOS-compatible durable
workflow semantics: deterministic workflow ids, deterministic step ids,
serializable step outputs, idempotent source output, durable progress
checkpoints, queue/rate-limit boundaries around nondeterministic work,
and observable retry/DLQ state. The first implementation SHALL use the
substrate's Postgres-native jobs, source-sync policies,
`okg.source_progress`, `ProgressMarker`, scoped sync, and generation
ledger unless a later approved change adds DBOS runtime execution for a
specific workflow.

#### Scenario: Unchanged rerun is fast
- **GIVEN** a target source, acquisition manifest, parser, or
  distillation section has already completed and committed progress
- **WHEN** the same scoped work runs again with unchanged inputs and
  unchanged parser/chunker versions
- **THEN** it SHALL append zero new node or edge facts
- **AND** it SHALL not trigger full-corpus parsing, embedding, or
  distillation work.

#### Scenario: One changed asset scopes downstream work
- **GIVEN** exactly one paper metadata record, PDF asset, web document,
  or evidence slice changes
- **WHEN** the source-sync job runs
- **THEN** only that record and its dependent parse/evidence/
  distillation outputs SHALL be rechecked or regenerated
- **AND** unrelated venue/year records SHALL remain untouched.

#### Scenario: External call is a durable step boundary
- **WHEN** acquisition, provider enrichment, parsing, embedding, or LLM
  distillation performs nondeterministic I/O or compute
- **THEN** the work SHALL have a deterministic step identity and
  serializable output
- **AND** failures SHALL be observable through retry state, DLQ, parser
  warnings, acquisition state, or coverage diagnostics.

### Requirement: Five-Year Systems/Database Corpus

The deployment SHALL define a target corpus consisting of all papers
from configured systems, networking, ML systems, and database venues for
the years 2022, 2023, 2024, 2025, and 2026 year-to-date. The initial
venue matrix SHALL include SOSP, OSDI, NSDI, SIGCOMM, HotNets, CoNEXT,
EuroSys, USENIX ATC, SoCC, MLSys, SIGMOD, VLDB/PVLDB, PODS, CIDR, ICDE,
and EDBT.

#### Scenario: Venue/year matrix is explicit
- **WHEN** an operator opens `deployments/memex-sr/venues.yaml`
- **THEN** each target venue SHALL declare its slug, name, domain, target
  years, DBLP key prefixes, query aliases, and default providers
- **AND** the file SHALL make main-track/workshop inclusion policy
  explicit.

#### Scenario: Coverage report detects missing venue years
- **WHEN** the coverage report runs after a publish
- **THEN** it SHALL report paper counts by venue and year
- **AND** any configured venue/year with zero papers SHALL be visible as
  a coverage gap.

### Requirement: Corpus Pack Expansion Contract

The deployment SHALL support corpus growth through declarative
source-pack configuration rather than broad unbounded search. Each
corpus pack SHALL declare scope, source authority, access basis, host
policy, parser/chunker bundle, identity rules, source-sync rules,
coverage metrics, and default enabled/disabled state. The initial
systems/database 2022-2026 pack SHALL be enabled by default; historical
backfill, adjacent CS venues, technical reports/standards, curated
blogs, and operator-supplied assets SHALL be representable as disabled
or manual expansion packs.

#### Scenario: Expansion pack is configured but disabled
- **WHEN** an operator lists memex-sr corpus packs
- **THEN** the default systems/database pack SHALL be enabled
- **AND** expansion packs for historical systems/database backfill,
  adjacent CS venues, reports/standards, curated blogs, and
  operator-supplied assets SHALL declare their scope and policy without
  running by default.

#### Scenario: Adding a corpus pack requires policy and verification
- **WHEN** a collaborator adds or enables a corpus pack
- **THEN** the pack SHALL declare lawful access basis, host policy,
  parser/chunker behavior, source-sync keys, and coverage metrics
- **AND** verification SHALL include fixture ingest and a real published
  generation proving the pack emits accepted graph shape.

#### Scenario: Corpus expansion preserves graph identity
- **WHEN** a new corpus pack adds papers, reports, standards, blogs, or
  operator-supplied documents
- **THEN** records SHALL use the existing paper/document/evidence model
  where possible
- **AND** new subtypes or edge routes SHALL require catalog narrowings,
  invariants, and fixture publish verification.

### Requirement: Venue-Scoped Paper Enumeration

The deployment SHALL use DBLP as the authoritative enumerator for target
papers. The DBLP source SHALL fetch all configured target venue/year
records, filter out non-target records by key prefix and venue rules,
and emit canonical paper, person, conference, and conference-edition
facts with source progress markers.

#### Scenario: Paper identities are stable
- **WHEN** a DBLP target paper is ingested
- **THEN** the paper node id SHALL be derived from the DBLP key
- **AND** rerunning the source with unchanged provider data SHALL append
  zero node or edge facts after progress comparison.

#### Scenario: Non-target papers are excluded
- **WHEN** a provider result is outside the configured venue/year matrix
- **THEN** the source SHALL not emit a paper fact for that result
- **AND** the skipped result SHALL be observable in source stats or a
  coverage diagnostic.

### Requirement: Target-Set Metadata Enrichment

The deployment SHALL enrich only target-set papers with identifiers,
abstracts, citation/reference hints, PDF URL hints, open-access status,
and provider provenance from Crossref, OpenAlex, Semantic Scholar,
OpenReview, and arXiv. Enrichment sources SHALL be incremental and SHALL
not broaden the target corpus by importing unrelated papers as primary
records.

#### Scenario: Enrichment is bounded
- **WHEN** enrichment sources run
- **THEN** every emitted paper update SHALL correspond to an existing
  target paper identity or an accepted same-paper alias
- **AND** unrelated provider search results SHALL be skipped.

#### Scenario: Source progress is durable
- **WHEN** an enrichment source succeeds for a paper
- **THEN** it SHALL write a progress marker containing the provider
  revision or response fingerprint
- **AND** a repeated run with unchanged data SHALL append zero facts.

### Requirement: Lawful Full-Text Acquisition

The deployment SHALL provide a venue-scoped full-text acquisition path
that downloads or references only lawful open-access or operator-supplied
paper full text, writes a checkpointed manifest, and emits parsed
`paper -> document -> document_chunk` evidence through the full-text
source. Paywalled publisher PDFs without explicit local access SHALL be
denied. Publish-time full-text sources SHALL read local manifest assets
and SHALL NOT perform live network downloads.

#### Scenario: Open PDF becomes evidence chunks
- **WHEN** a target paper has a lawful open PDF URL and acquisition
  succeeds
- **THEN** the manifest SHALL record paper id, source URL, access
  status, license/provenance, retrieved timestamp, local asset path, and
  content hash
- **AND** the next publish SHALL create one document and one or more
  chunks linked to the paper.

#### Scenario: Paywalled URL is not acquired
- **WHEN** a target paper has a paywalled publisher PDF URL and no
  operator-supplied license/access evidence
- **THEN** acquisition SHALL skip that URL
- **AND** the skip reason SHALL be visible in acquisition output or a
  coverage report.

### Requirement: Host-Governed Download Operation

The acquisition runner SHALL enforce an explicit host policy for
MIT-network downloads. The policy SHALL include per-host concurrency,
minimum delay, retry/backoff behavior, optional conditional request
validators, contact information for the user-agent, and terminal
skip/failure states. The runner SHALL cache-first, honor Retry-After
where present, and SHALL be able to pause/resume without duplicating
downloads or manifest records.

#### Scenario: Downloader obeys host policy
- **WHEN** acquisition runs for candidate PDF or web-document URLs
- **THEN** each live request SHALL be checked against
  `download_host_policy.yaml`
- **AND** requests to a host SHALL not exceed the configured concurrency
  or pacing limits
- **AND** cached assets SHALL be reused without a live request.

#### Scenario: Host throttles acquisition
- **WHEN** a host returns 429, 503, or a Retry-After response
- **THEN** the runner SHALL apply the configured backoff or pause
- **AND** the manifest or acquisition log SHALL record the retryable
  state if acquisition cannot complete in the current run.

#### Scenario: Host or access basis is disallowed
- **WHEN** a candidate URL is outside the allowed host/access policy
- **THEN** the runner SHALL not request the URL
- **AND** the skip reason SHALL distinguish policy denial from network
  failure and parse failure.

### Requirement: PDF Text Extraction And Structured Chunking

The deployment SHALL parse acquired PDFs into full text, parser metadata,
page/line text indexes when available, best-effort sections, and
parent-scoped document chunks. The PDF path SHALL reuse or adapt the
`af_pubs` patterns for cached assets, parser-version fingerprints,
PDF-to-text extraction, line-level bbox indexes, parse warnings, process
pool parsing, and section-window chunking. AF-specific cover-page and
section regexes SHALL not be treated as generic paper-parser behavior.

#### Scenario: Text-layer PDF becomes structured evidence
- **WHEN** an acquired target-paper PDF has an extractable text layer
- **THEN** publish SHALL create a `document` with parser version, page
  count, content hash, local asset reference, and parse warnings
- **AND** publish SHALL create one or more `document_chunk` facts with
  text, content hash, parser/chunker version, heading path if available,
  parent document id, and page/char offsets when available.

#### Scenario: Parser version changes
- **WHEN** the PDF parser or chunker version changes
- **THEN** the source SHALL treat affected cached assets as changed
- **AND** unchanged assets with matching parser/chunker fingerprints
  SHALL not reparse or append new facts.

#### Scenario: Scanned PDF is explicit
- **WHEN** a PDF has no extractable text layer
- **THEN** publish SHALL record an explicit parse warning or
  `ocr_needed` state
- **AND** it SHALL not silently publish an empty successful document as
  if full text were available.

#### Scenario: Chunks are parent scoped
- **WHEN** two different papers contain identical boilerplate text
- **THEN** their chunk identities SHALL remain distinct by parent
  document or section
- **AND** evidence traversal SHALL not collapse the two papers into a
  single shared chunk.

### Requirement: Curated Web And Technical Documents

The deployment SHALL support future ingestion of curated HTML, Markdown,
plain-text, technical-report, standards/protocol, project-doc, lab-post,
author-post, and engineering-blog documents through the same document
and chunk evidence model. These sources SHALL start from explicit
manifests and host policy rather than unbounded web crawling.

#### Scenario: Curated blog post becomes chunks
- **WHEN** a curated manifest entry references an allowed HTML or
  Markdown document
- **THEN** acquisition SHALL record canonical URL, access basis,
  retrieved timestamp, content hash, local asset path, and host policy
  provenance
- **AND** publish SHALL create a `document` and `document_chunk` facts
  using the deployment parser/chunker bundle.

#### Scenario: Web source is not an open crawler
- **WHEN** a page links to additional pages not listed in the curated
  manifest
- **THEN** acquisition SHALL not follow those links as new primary
  documents unless a configured source explicitly authorizes that crawl
  scope.

### Requirement: Collaborator Extension Surface

The deployment SHALL provide documented extension seams for
collaborators to add venues, ontology modules, data sources,
parsers/chunkers, entity extractors, and distillation methods without
modifying substrate core code. Each extension class SHALL include a
minimal fixture, declared provenance, progress/checkpoint behavior when
high-volume, and verification that exercises a real publish.

#### Scenario: Collaborator adds a source
- **WHEN** a collaborator adds a new metadata, full-text, or web-document
  source
- **THEN** the source SHALL be declared in `source_registry.yaml`
- **AND** it SHALL document fixture mode, sync policy, scoped execution
  support, progress marker granularity, rate policy if it touches a
  network host, and coverage metrics.

#### Scenario: Collaborator adds an extraction method
- **WHEN** a collaborator adds a parser, chunker, NER backend, or
  distillation extractor
- **THEN** it SHALL be registered in deployment configuration
- **AND** it SHALL declare parser/extractor versioning, warning/failure
  states, output provenance, and fixture tests for success, no-op, and
  changed-input paths.

#### Scenario: Extension docs are runnable
- **WHEN** a new collaborator follows the extension guide examples
- **THEN** the example SHALL run without network access by default
- **AND** its verification SHALL include catalog composition, fixture
  ingest, a real published generation, and live row checks.

### Requirement: Evidence-Backed Research Distillation

The deployment SHALL produce agent-facing evidence slices, claims,
trade-offs, open problems, and textbook-style sections from parsed target
paper full text. Every generated claim or section SHALL carry freshness
metadata and SHALL link back to evidence through `supported_by` or
equivalent evidence edges.

#### Scenario: Claim has evidence trail
- **WHEN** a generated claim is published
- **THEN** it SHALL include source generation id, evidence watermark,
  input evidence ids, and freshness status
- **AND** traversing `supported_by` SHALL reach evidence slices,
  document chunks, documents, or papers from the target corpus.

#### Scenario: Section is not evidence by itself
- **WHEN** an MCP client retrieves a generated textbook section
- **THEN** the MCP guidance SHALL instruct the client to treat the
  section as a starting point
- **AND** the client SHOULD follow evidence edges before presenting
  scientific conclusions.

### Requirement: Fast Autonomous Researcher MCP Surface

The deployment SHALL provide MCP instructions, skills, and audit
questions for autonomous systems research workflows. The instructions
SHALL prefer targeted `get_node`, lexical `search`, named SQL recipes,
and evidence traversal over broad graph scans for normal usage.

#### Scenario: Claude can run a smoke query
- **WHEN** Claude connects to the memex-sr MCP server
- **THEN** the server SHALL expose retrieval tools
- **AND** a pinned-generation query SHALL retrieve one target paper and
  its full-text chunks.

#### Scenario: Agent asks research-grade questions
- **WHEN** an agent follows the context packet
- **THEN** it SHALL be able to ask coverage, literature-survey,
  principle-extraction, trade-off, and evidence-trail questions
- **AND** answers SHALL distinguish graph evidence from inference.

### Requirement: Bounded Engram Tool Surface

The deployment SHALL expose an Engram-facing retrieval contract that
wraps a bounded subset of the regular OKG/MCP retrieval interface as
host-side DeepAgents tools. The default Engram subset SHALL preserve the
semantics of `search`, `get_node`, `list_neighbors`, and
`traverse_path`, and MAY add deployment-specific context-packet and
named-query-recipe helpers. Tool responses SHALL be bounded by explicit
token/result budgets and SHALL include generation id, provenance, and
evidence ids when applicable. Raw SQL, global graph statistics, and
unbounded graph scans SHALL NOT be part of the default Engram agent tool
surface.

#### Scenario: Engram receives a context packet
- **WHEN** an Engram run starts with memex-sr integration enabled
- **THEN** the integration SHALL retrieve or generate a context packet
  from a pinned memex-sr generation
- **AND** the packet SHALL include evidence ids and source provenance
- **AND** the run SHALL remain usable when memex-sr integration is
  disabled.

#### Scenario: Engram targeted lookup is budgeted
- **WHEN** an Engram agent calls the bounded OKG subset for search,
  node lookup, neighbor listing, or path traversal
- **THEN** the tool SHALL enforce configured result and token budgets
- **AND** the response SHALL include the pinned generation id
- **AND** the response SHALL not expose raw SQL unless an operator
  explicitly enables a debug mode outside the default agent path.

#### Scenario: Engram uses regular OKG semantics
- **WHEN** an Engram tool wraps `search`, `get_node`, `list_neighbors`,
  or `traverse_path`
- **THEN** its inputs and outputs SHALL remain compatible with the
  regular OKG/MCP contract except for documented budget, route, and
  projection limits
- **AND** the wrapper SHALL not introduce a second incompatible query
  language for Engram.

#### Scenario: Literature evidence is distinguishable
- **WHEN** Engram uses a memex-sr result to guide an experiment
- **THEN** the result SHALL distinguish paper-backed evidence, generated
  distillation, and inference-only guidance
- **AND** returned claims or textbook sections SHALL provide traversable
  evidence ids.

### Requirement: Engram Workspace Indexing

The deployment SHALL index archived Engram workspaces as research
artifacts through a normal substrate source and publish cycle. The
source SHALL parse configured Engram run roots into research-run,
agent-attempt, experiment, candidate-implementation,
metric-observation, failure-diagnosis, research-note, and
workspace-artifact nodes. The source SHALL use stable identities,
content hashes, progress markers, scoped sync, and full-reconcile
record sets for deterministic incremental indexing.

#### Scenario: Archived Engram run becomes graph evidence
- **WHEN** a configured Engram run archive contains `research_journal.md`,
  `knowledgebase/agent_*`, experiment snapshots, scores, result files,
  and final result metadata
- **THEN** a memex-sr publish SHALL create research artifact nodes and
  accepted edges linking the run, agents, experiments, implementations,
  observations, notes, and artifacts
- **AND** every emitted node SHALL carry run id, artifact path or logical
  record id, content hash where applicable, and source provenance.

#### Scenario: Engram indexing is incremental
- **GIVEN** an Engram archive has already been indexed
- **WHEN** the same archive is indexed again without content changes
- **THEN** the source SHALL append zero new node or edge facts
- **AND** it SHALL not rescan unrelated run roots beyond the configured
  sync scope.

#### Scenario: One changed experiment scopes downstream work
- **GIVEN** exactly one Engram experiment score, snapshot, or result file
  changes
- **WHEN** the Engram workspace source runs with the changed artifact
  scope
- **THEN** only that experiment and dependent artifact records SHALL be
  re-emitted or retracted
- **AND** unrelated agents, experiments, and literature records SHALL
  remain untouched.

#### Scenario: Evidence links require explicit provenance
- **WHEN** an archived Engram artifact records memex-sr evidence ids from
  prior tool calls or context packets
- **THEN** the source MAY link the run artifact back to those evidence
  ids as `informed_by`
- **AND** it SHALL only emit support or refutation edges when the agent
  summary or structured artifact explicitly states that relationship.
