# Design: Memex-SR Deployment

## Context

The collaborator goal is no longer "general memex" but an autonomous
systems researcher. The graph should be small enough to rebuild and
query quickly, but complete enough to support research-grade answers
over recent systems and database papers.

The first deployment is intentionally narrow, but the document layer
must be designed for the longer-term corpus: all useful CS papers,
technical reports, standards/protocols, code-adjacent documents, and
research/engineering blog posts. The shared need across all of those is
not just metadata; it is lawful full text, stable provenance, structured
chunks, and incremental refresh.

The current date is 2026-05-14. This design interprets "past 5 years"
as 2022, 2023, 2024, 2025, and 2026 year-to-date. If the intended
window is "last five complete conference years" instead, the target
window should be changed to 2021-2025 before implementation.

## Goals

- Build a separate deployment named `memex-sr`.
- Cover all papers from the target venue matrix for 2022-2026.
- Prefer exact venue/year enumeration over broad search queries.
- Attach parsed full text for open/operator-supplied papers.
- Normalize PDF, HTML, Markdown, and plain-text documents into a common
  document/chunk evidence model.
- Define corpus-pack configuration so new paper venues, historical
  backfills, reports, standards/protocols, blogs, and code-adjacent
  documents can be added without changing graph identity.
- Reuse `af_pubs` PDF acquisition, extraction, and chunking patterns
  where they fit the paper corpus.
- Run acquisition from the MIT network under explicit host rate policy
  so source hosts are not hammered.
- Make the high-volume pipeline compatible with DBOS durable workflow
  semantics without forcing DBOS into the first implementation.
- Keep the ontology explicit, catalog-composed, and invariant-checked.
- Give collaborators stable extension seams for ontology modules, data
  sources, extraction methods, and distillation methods.
- Preserve provenance for every metadata, PDF, document, chunk, and
  derived claim.
- Keep refreshes incremental and measurable.
- Expose MCP instructions that steer agents toward evidence traversal,
  not unsupported summary.
- Expose a bounded subset of the regular OKG/MCP retrieval surface to
  Engram for literature-backed context, targeted search, and evidence
  traversal.
- Index archived Engram workspaces so memex-sr can remember agent
  experiments, failures, scores, and design hypotheses across runs.

## Non-Goals

- Do not copy the full memex methodology corpus into the first fork.
- Do not include HEP, PL, AI, CV, NLP, security, or theory venues in
  the first target matrix unless they are needed as citations.
- Do not ingest paywalled PDFs without explicit local access evidence.
- Do not bypass robots, terms, access controls, or host rate limits.
- Do not make DBOS a mandatory runtime dependency unless a later
  approved change chooses to move a specific workflow onto DBOS.
- Do not let collaborators add graph shapes by emitting arbitrary edges
  that bypass catalog narrowings.
- Do not bulk-crawl the open web in the first deployment; blogs and
  technical reports start from curated manifests and host policies.
- Do not turn every venue/domain label into a graph node; keep high-card
  labels as attrs unless they support useful traversal.
- Do not give Engram agents raw Postgres access or unbounded graph-scan
  tools by default.
- Do not write Engram tool-call results directly into live graph tables;
  Engram work must enter through source facts and a published
  generation.
- Do not create a second bespoke retrieval API for Engram when the
  regular OKG retrieval interface already provides the right semantics.
  Engram should receive a constrained adapter over the existing tools.

## Deployment Shape

Create `deployments/memex-sr/` at the Engram repository root with:

- `deployment.yaml`
- `source_registry.yaml`
- `venues.yaml`
- `corpus_packs.yaml`
- `corpus_policy.yaml`
- `full_text_policy.yaml`
- `download_host_policy.yaml`
- `asset_manifest.yaml` or equivalent generated manifest store
- `extractors.yaml`
- paper/full-text/evidence/distillation schema modules copied,
  composed, or split from memex
- bridge narrowings under `schemas/bridges/`
- invariants under `invariants/`
- paper sources and full-text sources adapted from memex
- reusable document acquisition/parsing helpers extracted from
  `deployments/af_pubs` when they are deployment-neutral
- collaborator extension docs/templates
- `server.py`
- MCP instructions and skills
- `engram_integration.yaml` for agent-tool budgets and workspace
  indexing roots
- `docs/engram-integration.md`
- coverage report scripts

The deployment must use its own DSN, e.g.
`${MEMEX_SR_OKG_DSN}`, to avoid the memex graph's historical
rows and embed backlog.

The OKG substrate is provided by the `external/okg` submodule. Memex-SR
deployment-specific code, fixtures, ontology, policy, and Engram
integration should live in this repository. Substrate changes that need
to land upstream in OKG should be proposed separately in the OKG repo.

## Corpus Expansion Strategy

Memex-SR should start narrow, but it should not be architected as a
one-off five-year venue scrape. The corpus should expand through
declarative source packs. Each pack is a named unit of corpus scope with
its own authority, access policy, parser expectations, and coverage
metrics.

Initial source packs:

- `systems-db-2022-2026`: default pack for SOSP, OSDI, NSDI, SIGCOMM,
  HotNets, CoNEXT, EuroSys, USENIX ATC, SoCC, MLSys, SIGMOD,
  VLDB/PVLDB, PODS, CIDR, ICDE, and EDBT.
- `systems-db-historical`: disabled initially; extends the same venues
  backward by configured years.
- `adjacent-cs-venues`: disabled initially; future packs for PL,
  security, theory, AI/ML, HCI, and architecture when they are useful
  for systems research tasks.
- `technical-reports-and-standards`: curated reports, RFCs, IEEE/IETF
  documents, architecture notes, protocols, and implementation guides.
- `research-engineering-blogs`: curated lab, project, company, and
  author posts with explicit host policy and no open crawling.
- `operator-supplied-assets`: local PDFs, notes, textbooks, slides, and
  other licensed material supplied by collaborators.

Each corpus pack should declare:

- scope: venues, years, domains, source manifests, URL prefixes, or
  local directories;
- source authority: DBLP, Crossref, OpenAlex, Semantic Scholar,
  OpenReview, arXiv, curated manifest, local directory, or repository;
- access basis: open, operator-supplied, licensed-local, metadata-only,
  or denied;
- host policy: allowed hosts, concurrency, delay, backoff, contactful
  user-agent, and cache behavior;
- parser/chunker bundle: PDF, HTML, Markdown, plain text, code docs, or
  source-specific adapter;
- identity rules: canonical id, aliases, duplicate handling, and
  retraction semantics;
- source-sync rules: progress marker granularity, scoped execution keys,
  reconcile behavior, and dependent fanout;
- coverage metrics: expected records, acquired full text, parse
  success, warning counts, skipped/denied reasons, and stale records;
- default state: enabled for the first pack, disabled or manual for
  expansion packs until reviewed.

This means "all CS papers" becomes a sequence of approved source-pack
expansions, not a broad unbounded search. Adding a pack should require
fixture coverage, host policy, parser behavior, and a real publish
verification. The ontology should remain stable as the corpus expands:
new packs add source configuration and possibly bridge narrowings for
new document kinds, not one-off paper/document subtypes per source.

## DBOS Alignment

DBOS's useful constraints for this deployment are durable workflows,
durable steps, persistent queues, rate/concurrency controls, schedules,
recovery from the last completed step, and observable failure state. The
memex-sr implementation should align with those semantics even
if the first version runs on the substrate's existing Postgres job queue.

The mapping should be:

- Workflow identity: deployment + source/acquisition/distillation name +
  scoped venue/year/manifest key.
- Step identity: provider page, target paper, candidate asset URL,
  local asset hash, parser pass, chunk bundle, evidence slice, or
  distillation section.
- Step output: serializable manifest entry, parse result, fact batch
  descriptor, coverage record, or generated section record.
- Durable checkpoint: `ProgressMarker`, `okg.source_progress`,
  acquisition manifest state, parser fingerprint, and source-sync job
  payload.
- Queue/rate boundary: external provider calls, PDF/HTML downloads,
  parsing workers, embedding, and LLM distillation.
- Observability: queue depth, DLQ, source metrics, generation describe,
  acquisition outcomes, parser warning counts, and coverage reports.

Network and LLM calls are nondeterministic and should sit at explicit
step boundaries. Publish itself should remain a deterministic local
manifest-to-facts operation under the substrate generation ledger. If a
later change introduces the DBOS runtime, DBOS should wrap acquisition,
provider enrichment, parsing, and distillation workflows; it should not
replace the catalog, narrowing trigger, projection, gates, or generation
ledger without a separate architecture change.

Fast-path rules:

- Default source runs are scoped by venue/year, manifest path, provider
  page, or changed asset, not by full corpus scans.
- Repeated runs with unchanged provider responses/assets must emit zero
  new facts after progress comparison.
- External fetches are cache-first and host-policy governed.
- Parser/chunker version changes intentionally invalidate parse
  fingerprints; unrelated provider metadata changes must not force
  full-text reparse.
- Distillation regeneration is bounded to evidence whose watermark
  changed.

## Ontology Shape

Use LinkML/catalog composition as the contract. The deployment should
compose substrate modules where they already match the domain:

- `extraction` for `Document`, `DocumentChunk`, and mentions.
- `concepts` for operator-authored concept aggregators.
- `person` for author/person identity.
- `views` if generated context sections are exposed as views.

Deployment-owned modules should be split by concern:

- Corpus governance: `CorpusPack` and optional
  `CorpusCoverageSnapshot` records for approved source-pack scope,
  enablement state, access basis, parser bundle, and coverage outcomes.
  These are low-cardinality operational entities; per-host and
  per-provider details remain attrs/config unless traversal justifies
  nodes.
- Literature identity: `Paper`, `Venue`, `VenueEdition`,
  `PublicationSeries`, `Organization`, `Dataset`, `Software`,
  `Benchmark`, and external identifier attrs.
- Full-text assets: `DocumentAsset` or equivalent manifest-backed asset
  node when an acquired file needs provenance distinct from `Document`.
- Evidence/distillation: `EvidenceSlice`, `Claim`,
  `ResearchProblem`, `DistillationSection`, and typed attrs such as
  `distillation_kind` rather than one subtype per label.
- Engram research memory: `ResearchRun`, `AgentAttempt`, `Experiment`,
  `CandidateImplementation`, `MetricObservation`, `FailureDiagnosis`,
  `ResearchNote`, and `WorkspaceArtifact`. These subtypes model Engram
  work as evidence-bearing research artifacts, not as replacement
  literature.
- Extension bridges: deployment-owned narrowings connecting literature,
  documents, evidence, concepts, distillation, and Engram research
  artifacts.

Ontology rules:

- Every subtype has a stable required id attr, alias/search annotations,
  and a short description of identity semantics.
- Edge types use substrate edge archetypes. New edge archetypes require a
  separate justification; most deployment specificity belongs in
  narrowing names and edge attrs.
- High-cardinality labels such as provider names, venue groups, access
  status, and parser warnings stay as attrs unless traversal benefits
  justify a node.
- Bridge narrowings are mandatory for every emitted edge route. A source
  or extractor that needs a new route must add the narrowing and a
  fixture publish that proves the edge lands.
- Invariants cover evidence support, stale distillation sections,
  duplicate canonical paper ids, orphan documents/chunks, parser warning
  thresholds, and source coverage gaps.

## Collaborator Extension Contract

Collaborators should be able to extend the deployment by adding files in
well-defined places:

- New venues or years: edit `venues.yaml` and add fixture coverage.
- New metadata/full-text source: add a source adapter, declare it in
  `source_registry.yaml`, provide `sync:` policy, fixture mode,
  progress-marker granularity, and a coverage metric.
- New parser/chunker/extractor: register it in `extractors.yaml`, define
  parser/chunker versioning, parse warnings, and fixtures for no-op,
  changed, and failure paths.
- New ontology: add a LinkML module under `schemas/`, bridge narrowings
  under `schemas/bridges/`, invariants when correctness depends on the
  new shape, and a fixture publish proving accepted edges.
- New distillation method: emit graph data first (`EvidenceSlice`,
  `Claim`, `ResearchProblem`, `DistillationSection`) with evidence
  watermarks, then render views/context packets from those nodes.

The deployment should include contributor docs and one minimal example
for each extension class. Extension tests should run without network
access by default. Real-network tests should be explicit operator runs
against the MIT server and host-policy state.

## Engram Integration

Memex-SR should integrate with Engram in two directions:

1. Read path: Engram agents query memex-sr through a bounded subset of
   the regular OKG retrieval interface.
2. Write/index path: memex-sr indexes archived Engram run artifacts
   after Engram writes them to disk.

The read path should be a host-side DeepAgents tool, not shell access to
Postgres from inside the Engram sandbox. Engram's current agent builder
passes tools into `create_deep_agent`; the memex-sr integration should
add a small OKG client adapter next to `run_simulation`.

There is no architectural reason Engram cannot use a subset of the
regular OKG interface. It should. The only reason not to expose the full
interface is operational: full MCP includes tools that are too broad or
expensive for an autonomous optimization loop, such as unrestricted
`run_sql`, global `describe_graph`, or repeated high-limit searches.
The Engram adapter should preserve normal OKG semantics while enforcing
budgets, allowed methods, allowed routes, and pinned-generation reads.

Default Engram OKG tools:

- `okg_search(query, method="lexical", subtype_filter=None, limit=8)`
  maps to the regular OKG `search` tool with configured method,
  subtype, result, and token limits.
- `okg_get_node(node_id)` maps to regular `get_node`, with attrs
  redacted or summarized only when output budget requires it.
- `okg_list_neighbors(node_id, direction="out", edge_type=None,
  limit=25)` maps to regular `list_neighbors`, restricted to
  evidence-friendly routes by default.
- `okg_traverse_path(start_node, path, target_subtype=None, limit=25)`
  maps to regular `traverse_path`, with a small max-hop policy matching
  the MCP server contract.
- `okg_context_packet(problem_statement, topic_slugs, budget)` is the
  one deployment-specific helper. It composes regular OKG reads into a
  compact packet with principles, mechanisms, trade-offs, failure modes,
  experiment advice, and evidence ids.
- `okg_run_recipe(recipe_name, params)` may expose named, reviewed SQL
  recipes for coverage or audit checks. It is not arbitrary `run_sql`.

Tool responses must include the memex-sr generation id, evidence ids
when applicable, source provenance, and token/result counts. Raw
`run_sql` remains an MCP/operator capability for debugging, but the
Engram agent-facing adapter should expose only named recipes unless an
operator explicitly enables debug mode.

The read path should support two operating modes:

- Context-first mode: generate one context packet before each Engram
  agent starts and append it to the task prompt.
- Targeted lookup mode: allow the agent to call the bounded OKG subset
  when it needs additional literature or prior experiment context.

Context-first mode is the default because it keeps Engram runs fast and
reproducible. Targeted lookup mode is opt-in and budgeted because an
agent can otherwise spend its simulation budget wandering the graph.

The write/index path should be a normal substrate source named
`memex_sr_engram_workspace`. It reads configured Engram run roots after
Engram archives each agent workspace. The source should emit stable
records for:

- `research_journal.md` entries as `ResearchNote` nodes.
- `knowledgebase/agent_*/` directories as `AgentAttempt` nodes.
- `experiments/exp_*/score.txt` as `Experiment` plus
  `MetricObservation` nodes.
- `experiments/exp_*/snapshot.py`, `snapshot.cpp`, or equivalent files
  as `CandidateImplementation` nodes.
- `experiments/exp_*/results/*` files as metric or artifact nodes,
  capped and summarized when files are large.
- console logs and fallback summaries as `FailureDiagnosis` or
  `WorkspaceArtifact` nodes when they contain actionable evidence.
- final result JSON/config/task prompts as `ResearchRun` metadata.

Stable identity should be:

```text
engram:<run_id>:agent:<agent_number>:experiment:<exp_id>:<artifact_kind>
```

with content hashes for mutable artifacts. A full reconcile run should
return a `record_set` so disappeared artifacts can retract
deterministically. Normal incremental runs should scope by run id,
agent number, experiment id, or changed artifact path.

The Engram workspace source should link artifacts back into the
literature graph only when there is evidence:

- Candidate implementations may be `informed_by` memex-sr context
  packet ids or evidence ids recorded in the Engram run config.
- Experiments may `support` or `refute` a `DesignHypothesis` or
  `Claim` when the agent summary names the relationship.
- Failure diagnoses may `mentions` papers, mechanisms, metrics, or
  benchmark concepts through identifier/entity extraction.

The source should not infer strong scientific support merely because an
agent read a paper before running an experiment. Read provenance is
useful, but support/refutation edges require explicit summary text or a
structured handoff artifact.

## Source Plan

Primary source:

- `memex_sr_dblp`: authoritative target venue/year enumerator.
  It emits `paper`, `person`, `conference`, `conference_edition`, and
  edges for `authored_by`, `published_in`, and `contains`.

Secondary metadata enrichers:

- Crossref: DOI and publication metadata for target papers.
- OpenAlex: concepts, citation hints, OA status, alternate identifiers.
- Semantic Scholar: citations/references/abstracts where available.
- OpenReview: metadata and PDF URLs for target OpenReview-hosted papers.
- arXiv OAI: preprint PDF/source hints for matched target papers.

Full text:

- `memex_sr_paper_full_text_manifest`: local manifest of
  acquired PDFs/text.
- Acquisition script: venue-scoped, checkpointed, rate-limited, and
  idempotent. It must only add manifest records for lawful open or
  operator-supplied full text.
- PDF asset source: converts manifest assets into `document`,
  `document_section`, `figure`, `table`, and `document_chunk` facts when
  supported by the parser. It must not require a live download during
  publish.
- Web document source: later curated manifests for technical reports,
  standards, protocols, project docs, lab posts, author posts, and
  engineering blog posts. It should reuse the generic `DocCorpusSource`
  parser/chunker bundle for HTML/Markdown/plain text.

Derived sources:

- Evidence slices from document chunks.
- Distillation claims/open problems/trade-offs from evidence slices.
- Topic/textbook sections for agent context packs.
- Engram workspace artifacts from archived Engram runs.

## Reuse From af_pubs

The `af_pubs` deployment already solved several pieces we need:

- PDF cache naming by URL hash plus filename tail.
- Shared HTTP session/cached fetcher patterns for hosts that dislike
  bursty automation.
- Bounded PDF downloads with jitter, retryable status handling,
  exponential backoff, cooldown after sustained 403s, and outcome
  counters.
- Parse separation: download cache misses first, then parse cached PDFs
  through a process pool.
- `ProgressMarker` fingerprints that combine asset identity
  (`size:mtime_ns`) with parser version, so parser changes force
  incremental reparse without rescanning everything blindly.
- PDF text extraction with pypdfium2/PDFium for body text, PyMuPDF
  (`fitz`) for line-level text+bbox indexes, and pdfplumber only where
  layout-aware table extraction still wins.
- Section extraction and a follow-up section chunker that emits
  `document_chunk` nodes from section-bounded windows with overlap.
- Extraction audit scripts that can check body-text/page/index quality.

The memex-sr fork should extract or adapt those mechanics into
deployment-neutral helpers. AF-specific cover-page actor parsing and AF
section regexes should stay AF-specific; paper PDFs need a more general
parser with fallbacks for arXiv/USENIX/ACM/IEEE/OpenReview/VLDB styles.

## Full-Text Architecture

Use a two-stage document pipeline:

1. Acquisition writes an asset manifest. It records canonical paper id,
   candidate URL, access basis, license/provenance, retrieved timestamp,
   local path, byte count, content hash, HTTP validators if present,
   host policy used, and terminal state (`fetched`, `skipped`,
   `blocked`, `failed_retryable`, `failed_permanent`).
2. Publish reads only local manifest assets and emits graph facts. This
   keeps publish deterministic and avoids live network calls inside a
   generation transaction path.

PDF parsing should produce:

- Full extracted text when a text layer exists.
- Page count and parser version.
- Page/line text index with bboxes where available.
- Best-effort sections/headings, including heading path and page/char
  offsets.
- Tables/figures when the parser can recover useful captions or rows.
- Explicit warnings for scanned/image-only PDFs, parse failures,
  truncated indexes, and OCR-needed assets.

Chunk organization should be stable and evidence-friendly:

- `paper` owns bibliographic identity.
- `document` represents one acquired/rendered full-text asset.
- `document_section` represents heading-bounded logical regions when
  recovered.
- `document_chunk` represents embeddable/retrievable windows with
  content hash, parser/chunker version, heading path, page/char offsets,
  and parent document/section ids.
- Chunk ids should be parent-scoped for papers so identical boilerplate
  across PDFs does not collapse evidence from two different papers.

For HTML/Markdown/blog posts, prefer the substrate `DocCorpusSource`
parser/chunker bundle and heading-aware chunkers. The acquisition layer
should preserve canonical URL, fetch timestamp, content hash, title,
author/date if recoverable, and cleaned readable text.

## Download Governance

Downloads should run from the approved MIT network/server, not from
random developer laptops. The acquisition runner must enforce a
`download_host_policy.yaml` with:

- Per-host concurrency, minimum delay, and retry/backoff settings.
- A contactful user-agent string.
- Conditional GET with ETag/Last-Modified where supported.
- Honor for `Retry-After`.
- Per-host pause/resume state and DLQ/skipped reasons.
- Cache-first behavior before any live request.
- No speculative publisher PDF fetching unless policy marks the host and
  access basis as allowed.

The default policy should be conservative for ACM, IEEE, Springer,
Elsevier, publisher CDNs, author pages, lab sites, and blogs. Open hosts
such as arXiv, OpenReview, USENIX, VLDB/PVLDB, and author-hosted PDFs
still need per-host throttles and provenance. Operator-supplied local
PDF directories bypass HTTP download but still enter the same manifest
and parse path.

## Fast/Proper Constraints

- Use `ProgressMarker` for every high-volume source record.
- Fingerprint full-text records by asset hash plus parser/chunker
  version so unchanged PDFs do not reparse and parser changes reparse
  exactly the affected assets.
- Run source sync in scoped mode whenever the changed input is a
  venue/year or manifest path.
- Avoid broad `describe_graph`-style scans in default MCP guidance.
- Disable or defer expensive embedding until lexical/SQL retrieval is
  verified. The embed worker backlog must not block publish.
- Add coverage reports that can be run by target venue/year without
  full graph scans.
- Add parse/download coverage reports by host, venue/year, access basis,
  parser warning, and full-text availability.
- Acceptance requires a real publish and live row deltas, not only tests.

## Target Venue Matrix

Systems/networking/ML systems:

- SOSP, OSDI, NSDI, SIGCOMM, HotNets, CoNEXT, EuroSys, USENIX ATC, SoCC,
  MLSys.

Databases:

- SIGMOD, VLDB/PVLDB, PODS, CIDR, ICDE, EDBT.

Target years:

- 2022, 2023, 2024, 2025, 2026 year-to-date.

## Open Questions

- Should PL venues (PLDI, POPL, OOPSLA) remain out of scope for the
  first autonomous systems researcher fork?
- Should "all papers" include workshops colocated with the target
  conferences, or only main conference/proceedings papers?
- Should the first full-text acquisition target OpenReview/arXiv only,
  or also conference-hosted PDFs such as USENIX and VLDB where access is
  public?
- Which MIT server should own scheduled acquisition and host-policy
  state for the initial run?
- Should OCR for scanned PDFs be included in the first deployment, or
  recorded as `ocr_needed` for a later parser stage?
