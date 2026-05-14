# Tasks: add-memex-sr-deployment

## 0. Baseline And Scope

- [ ] 0.1 Record the target venue/year matrix and current memex baseline
      coverage for the same matrix.
      Verification: SQL/report output records paper counts, identifier
      coverage, PDF URL hints, parsed full-text count, and provider
      distribution for 2022-2026 target venues.

- [x] 0.2 Decide final scope for ambiguous venues and paper classes.
      Verification: `deployments/memex-sr/venues.yaml` records
      explicit target years, venue aliases, DBLP key prefixes, and
      inclusion/exclusion policy for main-track versus workshop papers.

- [x] 0.3 Define corpus-pack expansion policy.
      Verification: `deployments/memex-sr/corpus_packs.yaml` and
      `corpus_policy.yaml` define the default systems/database pack plus
      disabled expansion packs for historical backfill, adjacent CS
      venues, technical reports/standards, curated blogs, and
      operator-supplied assets; each pack declares scope, access basis,
      host policy, parser/chunker bundle, source-sync keys, and coverage
      metrics.

- [x] 0.4 Record the reusable `af_pubs` full-text components and the
      parts that must remain AF-specific.
      Verification: design notes identify the reusable cache/download,
      parser fingerprint, PDF text/index, structure audit, and section
      chunking patterns, plus the AF-only cover/section heuristics that
      will not be copied into the paper parser.

- [x] 0.5 Add bounded source samples and ontology coverage reporting.
      Verification: `deployments/memex-sr/scripts/sample_data_sources.py`
      runs against `data_sources.yaml`, writes
      `samples/source_samples.json` and `samples/ontology_coverage.md`,
      records provider failures without aborting, and reports ontology
      target coverage.

- [x] 0.6 Record the generation-5 local cut and pre-full-text gates.
      Verification: `deployments/memex-sr/docs/pre-full-text-readiness.md`
      records generation id, node/edge counts, venue/year coverage,
      source limitations, local test commands, no-op incremental check,
      pre-full-text audit gates, and repo-readiness criteria.

## 1. Deployment Fork

- [ ] 1.1 Create the `deployments/memex-sr/` deployment shell.
      Verification: `uv run okg doctor --deployment memex-sr
      --check manifest --json` succeeds and every referenced path exists.

- [ ] 1.2 Add a minimal paper/distillation ontology composition.
      Verification: catalog load/apply succeeds against a clean
      memex-sr DB and all required paper, document, chunk,
      evidence, claim, topic, and section narrowings are active.

- [ ] 1.3 Add ontology invariants for the core graph contract.
      Verification: fixture publishes prove invariants catch duplicate
      canonical paper ids, document/chunk orphans, unsupported
      distillation claims, stale sections, and missing required
      provenance while a clean fixture publishes successfully.

- [ ] 1.4 Add collaborator extension docs and templates.
      Verification: docs include working examples for adding a venue, a
      source, an ontology module/narrowing, a parser/chunker/extractor,
      and a distillation method; each example names the required fixture,
      progress, invariant, and publish verification.

- [ ] 1.5 Add MCP instructions, skills, audit questions, and context
      packet for the autonomous systems researcher.
      Verification: the MCP server starts and a smoke session can run
      `get_node`, `search`, `run_sql`, and one evidence traversal.

## 2. DBOS-Aligned Fast Execution

- [ ] 2.1 Define the durable workflow/step identity contract for
      source, acquisition, parser, and distillation work.
      Verification: design/config docs map each high-volume operation to
      deterministic workflow ids, step ids, checkpoints, queue/rate
      boundaries, and observable retry/DLQ state.

- [ ] 2.2 Add source-sync policy, compaction, and scoped execution for
      every high-volume source.
      Verification: `okg sync policy --deployment memex-sr
      --json` reports sync policy for each enabled source, including
      scoped support, reconcile behavior, compaction settings, and
      dependent fanout.

- [ ] 2.3 Add no-op and changed-record performance tests.
      Verification: two-run fixture tests show unchanged reruns append
      zero facts and one changed paper/asset scopes downstream work to
      only dependent records, with queue depth and DLQ within thresholds.

## 3. Target Paper Sources

- [ ] 3.1 Add the venue-scoped DBLP source as the authoritative
      paper enumerator.
      Verification: a publish against fixture venue/year data creates
      `paper`, `person`, `conference`, and `conference_edition` nodes
      plus `authored_by` and `published_in` edges with no narrowing
      violations.

- [ ] 3.2 Add target-set metadata enrichment from Crossref, OpenAlex,
      Semantic Scholar, OpenReview, and arXiv.
      Verification: focused tests prove these sources only enrich papers
      already selected by the memex-sr target matrix and do not
      scan unrelated memex papers.

- [ ] 3.3 Add source progress and source-sync coverage for every
      high-volume source.
      Verification: rerunning the same source after a completed publish
      appends zero facts, source progress rows exist per record, and
      `okg metrics --source-sync` reports no DLQ.

- [ ] 3.4 Add corpus coverage and paper quality reports before full
      text.
      Verification: reports under `deployments/memex-sr/reports/`
      cover venue/year completeness, source provider distribution,
      duplicate DOI/title checks, missing authors/source records,
      missing `published_in`, suspicious 2026 records, and
      main-track filtering warnings.

- [ ] 3.5 Add document asset URL audit before download.
      Verification: every `document_asset` is classified as verified
      direct PDF, landing-only, inferred-needs-verification,
      publisher/DOI-only, blocked, or needs operator-supplied copy;
      the downloader consumes only verified or explicitly allowed
      asset records.

## 4. Full Text Acquisition

- [ ] 4.1 Add a host-governed acquisition manifest and downloader scoped
      by venue/year.
      Verification: fixture tests cover `download_host_policy.yaml`,
      cache-first behavior, contactful user-agent, per-host concurrency
      and delay, Retry-After/backoff, conditional request validators,
      checkpointed manifest writes, DLQ/skipped reasons, and idempotent
      reruns.

- [ ] 4.2 Add PDF-to-text parsing adapted from `af_pubs`.
      Verification: parser tests cover text-layer PDFs, scanned/no-text
      PDFs, parser-version fingerprint invalidation, page count, line
      text+bbox index, parse warnings, table/figure best-effort outputs,
      and no live network access during publish.

- [ ] 4.3 Add structured document/section/chunk publication for acquired
      assets.
      Verification: a fixture publish creates parent-scoped
      `paper -> document -> document_section -> document_chunk` evidence
      with content hashes, parser/chunker versions, heading paths,
      page/char offsets, and no chunk collapse across two papers sharing
      boilerplate text.

- [ ] 4.4 Add curated web/blog/technical-report ingestion path.
      Verification: fixture manifests for HTML, Markdown, and plain text
      publish `document` and `document_chunk` facts through the generic
      parser/chunker bundle with canonical URL, fetch timestamp, title,
      content hash, and host-policy provenance.

- [ ] 4.5 Publish parsed full text for a first real target slice.
      Verification: a real publish creates `paper -> document ->
      document_chunk` rows for at least one target venue/year, and live
      row checks match the manifest count, parser warning counts, and
      chunk count.

## 5. Distillation And Agent Views

- [ ] 5.1 Wire evidence slicing from paper chunks.
      Verification: a real publish creates evidence slices from target
      paper chunks with `extracted_from` paths back to document chunks
      and papers.

- [ ] 5.2 Wire first-pass claims, trade-offs, open problems, and
      textbook sections.
      Verification: generated claims/sections carry source generation,
      evidence watermark, input evidence IDs, freshness status, and
      `supported_by` edges to evidence.

- [ ] 5.3 Add audit questions for autonomous systems researcher tasks.
      Verification: audit replay includes lookup, coverage, evidence
      trail, survey, and context-pack questions; failures identify
      concrete graph coverage gaps.

## 6. Engram Integration

- [ ] 6.1 Add the bounded regular-OKG subset contract and setup docs.
      Verification: docs/config define Engram wrappers for regular OKG
      `search`, `get_node`, `list_neighbors`, and `traverse_path`, plus
      `okg_context_packet` and named `okg_run_recipe`; the contract
      covers pinned generation handling, token/result budgets, allowed
      routes, provenance fields, and disabled-by-default arbitrary
      `run_sql`.

- [ ] 6.2 Add the Engram workspace ontology and source.
      Verification: a fixture Engram archive publishes `ResearchRun`,
      `AgentAttempt`, `Experiment`, `CandidateImplementation`,
      `MetricObservation`, `FailureDiagnosis`, `ResearchNote`, and
      `WorkspaceArtifact` nodes with accepted narrowings and provenance.

- [ ] 6.3 Add incremental Engram workspace indexing checks.
      Verification: indexing the same fixture archive twice appends zero
      facts on the second run; changing one `score.txt` or snapshot
      scopes downstream work to that experiment; full reconcile emits
      deterministic retractions for removed artifacts.

- [ ] 6.4 Smoke-test Engram read/write loop against memex-sr.
      Verification: an Engram fixture run can call the bounded regular
      OKG subset, record returned evidence ids in its archive, and a
      later memex-sr publish links the archived run artifact back to
      those evidence ids without direct database writes from Engram.

## 7. Acceptance

- [ ] 7.1 Run focused tests and spec consistency checks.
      Verification: ruff and focused pytest pass; deployment docs,
      source registry, ontology modules, invariants, and task/spec files
      agree on the `memex-sr` name, repo-root paths, source ids, and
      accepted edge routes.

- [ ] 7.2 Run a clean real publish for the target deployment.
      Verification: `okg generation describe <g> --deployment
      memex-sr` reports `published`, Phase B is unblocked,
      node/edge row deltas match the target source scope, source doctor
      returns `ok=true`, queue/DLQ are sane, and coverage report records
      venue/year completeness plus full-text acquisition and parser
      coverage by host/access basis.

- [ ] 7.3 Register and smoke-test the memex-sr MCP server for
      Claude.
      Verification: Claude reports the MCP server connected, tool list is
      non-empty, and a pinned-generation smoke query retrieves one target
      paper plus its document chunks.
