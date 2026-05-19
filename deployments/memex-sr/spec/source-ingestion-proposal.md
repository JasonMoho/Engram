# Proposal: Memex-SR Source Ingestion And Reference Acquisition

## Why

Why is this broken?

The incomplete substrate stage is **source coverage**, followed by a
missing **projection-ready full-text acquisition path**. The current
Memex-SR graph has useful metadata and URL hints, but it does not yet
have a reliable way to enumerate the complete target paper universe,
decide which full text can lawfully be acquired, parse those assets into
stable chunks, and keep all of that fast under repeated local or server
runs.

This matters because the goal is not a search index. The goal is an
autonomous systems researcher: an agent should be able to ask for
principles, mechanisms, trade-offs, failure modes, related experiments,
and open problems, then trace every statement back to papers,
textbooks, reports, standards, or Engram run artifacts. That requires
full-text evidence with provenance, not just paper titles and DOIs.

## Current State

The deployment already has a first committed paper cut and control
scaffolding:

- 4,782 paper records in `deployments/memex-sr/manifests/paper_cut.json`.
- Metadata/source hints from USENIX, PVLDB, and OpenAlex.
- 7,310 `document_asset` hints in the verified generation-5 local cut.
- No parsed paper full text yet.
- No evidence slices or distilled textbook sections yet.
- `download_host_policy.yaml`, `corpus_packs.yaml`, and
  `corpus_policy.yaml` define the first host and expansion guardrails.
- `acquisition_policy.yaml`, `textbook_sources.yaml`, and
  `scripts/plan_acquisition.py` now provide a deterministic first-pass
  acquisition planning stage.

The current acquisition planner output over the committed cut is:

```text
total_records: 7,312
fetch_open: 2,969
queue_mit_manual: 185
skip_metadata_only: 4,158
```

That planner is not the downloader and not proof of full-text coverage.
It is a policy/access-basis gate that separates open automated
acquisition from MIT-authenticated manual work and metadata-only records.

## Goals

- Enumerate the complete 2022-2026 systems/database venue target set.
- Expand beyond papers through explicit source packs for textbooks,
  technical reports, standards, protocols, curated blogs, and
  operator-supplied local assets.
- Acquire full text only through lawful open, operator-supplied, or
  MIT-assisted manual lanes.
- Never bulk-script Touchstone, libproxy, publisher platforms, or ebook
  portals.
- Reuse `af_pubs` acquisition/parsing mechanics where they are generic:
  cache-first downloads, retry/backoff, parser fingerprints, PDF text
  extraction, page/line indexes, warnings, and section/chunk publication.
- Keep publish deterministic: publish reads local manifests and cached
  assets only; it does not perform live network requests.
- Make the pipeline DBOS-compatible through deterministic workflow ids,
  step ids, serializable outputs, checkpoints, scoped deltas, and
  visible DLQ/error states.
- Give collaborators clear extension seams for new venues, sources,
  parsers, ontology modules, and distillation methods.

## Non-Goals

- Do not do full all-CS ingestion in the first implementation slice.
- Do not perform unbounded web crawling.
- Do not scrape paywalled publisher PDFs or ebooks with scripts.
- Do not treat MIT access as blanket permission for bulk automated
  downloading.
- Do not parse or publish full text during provider metadata fetches.
- Do not add source-specific document subtypes unless the existing
  paper/document/evidence model cannot represent the data.
- Do not claim completion until a real substrate publish lands expected
  live rows and a no-op rerun appends zero facts.

## Proposed Pipeline

The ingestion system should be a staged pipeline:

1. **Target enumeration**
   - DBLP is the authoritative venue/year paper enumerator.
   - Venue-native sources such as USENIX and PVLDB can add direct
     proceeding pages and PDF hints.
   - Curated manifests enumerate textbooks, reports, standards, blogs,
     and operator-supplied local files.

2. **Target-set metadata enrichment**
   - Crossref, OpenAlex, Semantic Scholar, OpenReview, and arXiv enrich
     only selected target papers.
   - Enrichers must not broaden the corpus by importing unrelated search
     results as primary papers.

3. **Acquisition planning**
   - Candidate URLs and local-asset targets are classified before any
     network download.
   - Output actions are `fetch_open`, `queue_mit_manual`,
     `queue_operator_asset`, `skip_metadata_only`, and `skip_denied`.
   - MIT/publisher/ebook targets become operator tasks, not automated
     authenticated downloads.

4. **Open asset acquisition**
   - A downloader consumes only `fetch_open` records.
   - It enforces `download_host_policy.yaml`, cache-first behavior,
     contactful user-agent, Retry-After/backoff, and checkpointed output.
   - It writes `acquired_assets.jsonl` records with local path,
     content hash, byte count, access basis, provenance, and terminal
     state.

5. **Operator asset registration**
   - A local registrar hashes files placed under
     `deployments/memex-sr/operator_assets/` or another configured
     private cache.
   - It writes the same acquired-asset manifest contract as the open
     downloader.
   - It records access basis and provenance without redistributing
     licensed content.

6. **Parse and chunk**
   - Parsers consume acquired local assets only.
   - PDF parsing produces document text, page count, warnings, optional
     page/line bbox index, best-effort sections, figures/tables when
     useful, and parent-scoped chunks.
   - HTML/Markdown/plain-text parsing uses the generic document parser
     and heading-aware chunkers where possible.

7. **Publish graph facts**
   - Sources read parse manifests and emit `paper -> document ->
     document_section -> document_chunk` evidence.
   - Publish runs through normal OKG substrate projection, narrowings,
     invariants, and generation ledger.

8. **Distill and serve**
   - Evidence slices, claims, trade-offs, open problems, and
     textbook-style sections are derived from chunks.
   - Engram agents access them through bounded OKG tools and context
     packets.

## Data We Will Build

The target graph should contain these main data products:

- `CorpusPack` and `CorpusCoverageSnapshot` for source-pack scope and
  coverage.
- `Paper`, `Person`, `Venue`, `VenueEdition`, and `PublicationSeries`
  for literature identity.
- `DocumentAsset` for candidate/acquired asset provenance.
- `Document`, `DocumentSection`, and `DocumentChunk` for parsed full
  text.
- `EvidenceSlice`, `Claim`, `ResearchProblem`, and
  `DistillationSection` for textbook-style distillation.
- `ResearchRun`, `AgentAttempt`, `Experiment`,
  `CandidateImplementation`, `MetricObservation`, `FailureDiagnosis`,
  `ResearchNote`, and `WorkspaceArtifact` for Engram run memory.

High-cardinality labels such as provider, host, access state, parser
warning, and venue group should remain attrs unless they support useful
graph traversal.

## Source Lanes

| Lane | Examples | Automation | Output |
| --- | --- | --- | --- |
| Venue metadata | DBLP, USENIX, PVLDB | Yes | paper/person/venue facts |
| Metadata enrichment | Crossref, OpenAlex, Semantic Scholar, OpenReview, arXiv | Yes, target-set only | identifiers, abstracts, OA hints |
| Open direct full text | USENIX PDFs, PVLDB PDFs, arXiv, OpenReview, RFCs, OCW/course notes | Yes, host-policy governed | acquired asset manifest |
| Open author/project copy | author PDFs, lab reports, project docs | Yes after URL verification | acquired asset manifest |
| MIT manual | ACM, IEEE, Springer, Elsevier, Wiley, ebooks | No scripted auth | operator task, then local asset |
| Operator supplied | collaborator PDFs, licensed local chapters, notes | No network | acquired asset manifest |
| Curated web | reports, standards, blogs, protocols | Yes from curated manifests | acquired asset manifest |

## MIT Access Boundary

MIT access is useful, but it changes the **manual acquisition lane**, not
the automation boundary.

The planner may produce browser/helper links, DOI/title queues, or
ILLiad/library-request tasks. A human MIT user may retrieve materials
through approved browser or library workflows and place local files into
the private operator asset cache. The system may then hash, parse, and
index those local files for this research context.

The system must not:

- script Touchstone login;
- script libproxy bulk downloads;
- reuse browser cookies for publisher crawls;
- bulk-download ebooks or textbook chapters;
- redistribute licensed content.

## DBOS And Incremental Contract

Each high-volume step must map cleanly to DBOS-style durable execution,
even if the first implementation uses the OKG substrate job queue.

| Stage | Workflow id | Step id | Checkpoint |
| --- | --- | --- | --- |
| DBLP enumeration | `memex-sr:dblp:<venue>:<year>` | DBLP page/key | source progress fingerprint |
| Metadata enrichment | `memex-sr:<provider>:<paper_id>` | provider request | provider response hash |
| Acquisition plan | `memex-sr:plan:<manifest_hash>` | candidate asset id | plan record hash |
| Open download | `memex-sr:fetch:<host>:<asset_id>` | URL + validators | acquired asset record |
| Operator registration | `memex-sr:operator-asset:<path>` | local file hash | acquired asset record |
| Parse/chunk | `memex-sr:parse:<content_hash>` | parser/chunker version | parse manifest |
| Publish | `memex-sr:publish:<source_scope>` | fact batch | generation id |
| Distillation | `memex-sr:distill:<evidence_watermark>` | section/claim id | distillation record |

Required incremental behavior:

- An unchanged provider response emits zero new facts.
- An unchanged acquired file with unchanged parser/chunker versions does
  not reparse.
- A parser version bump reparses only assets whose parser fingerprint
  changed.
- A changed paper or asset scopes downstream work to that record and its
  dependents.
- A no-op rerun of a completed source appends zero nodes and edges.

## Implementation Phases

### Phase 1: Proposal And Coverage Grounding

- Finalize this proposal and review it with collaborators.
- Produce a coverage report for every target venue/year.
- Record which providers are authoritative for each venue.
- Identify missing/weak venues before full-text work begins.

### Phase 2: Source Enumeration And Metadata Quality

- Implement DBLP as authoritative enumerator.
- Keep USENIX/PVLDB/OpenReview venue-native sources as direct metadata
  and PDF-hint sources.
- Bound Crossref/OpenAlex/Semantic Scholar/arXiv enrichment to target
  papers.
- Add duplicate DOI/title, missing author, missing venue, and
  main-track/noise reports.

### Phase 3: Acquisition Manifest

- Promote the planner output into a committed manifest contract.
- Add the verified URL audit: direct PDF, landing-only, inferred-needs
  verification, publisher/manual, blocked, operator-supplied.
- Implement open downloader consuming only verified `fetch_open` rows.
- Implement operator asset registrar for local files.

### Phase 4: Parsing And Chunk Publication

- Adapt `af_pubs` PDF mechanics into a general paper/textbook parser.
- Preserve page counts, warnings, line indexes, headings, offsets,
  parser/chunker versions, and content hashes.
- Publish document/section/chunk rows from local manifests only.
- Verify chunks are parent-scoped and do not collapse shared boilerplate
  across papers.

### Phase 5: Evidence And Distillation

- Create evidence slices from chunks.
- Generate first-pass claims, trade-offs, open problems, and
  textbook-style sections.
- Add context-packet recipes for Engram agents.

### Phase 6: Expansion Packs

- Add curated technical reports/standards manifests.
- Add curated blog/project-doc manifests.
- Add disabled historical and adjacent-CS venue packs.
- Add new packs only with host policy, parser behavior, source-sync
  policy, fixtures, and real publish verification.

## Acceptance Criteria

The proposal is accepted when:

- Collaborators agree on the MIT access boundary and source lanes.
- The target venue/year matrix has an explicit coverage report.
- Every high-volume source has a sync/progress policy.
- The acquisition planner and URL audit produce deterministic manifest
  records with clear action/state values.
- The downloader consumes only approved open records and records skipped
  or retryable states.
- Operator-supplied licensed material can be registered from local files
  without network access.
- A first real target slice publishes `paper -> document ->
  document_chunk` rows from acquired local assets.
- A no-op rerun appends zero facts.
- `okg generation describe <g>` reports a published generation, not a
  blocked one.
- `okg metrics --source-sync` reports sane queue/DLQ state.
- The MCP smoke query can retrieve a paper, its chunks, and provenance.

## Open Questions

- Should the first full-text slice target USENIX/PVLDB only, or also
  arXiv/OpenReview matches?
- Which server owns scheduled acquisition state after local tests:
  `chunky` or another CSAIL machine?
- Should OCR be part of the first parser milestone or deferred as
  `ocr_needed` warnings?
- Which textbooks should be enabled first beyond OSTEP and MIT course
  notes?
- What is the first Engram benchmark task that should consume a
  Memex-SR context packet?
