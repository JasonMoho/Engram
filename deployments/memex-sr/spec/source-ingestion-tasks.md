# Tasks: Source Ingestion And Reference Acquisition

## 0. Proposal Review

- [ ] 0.1 Review and approve the source-ingestion proposal with
      collaborators.
      Verification: `source-ingestion-proposal.md` records accepted
      source lanes, MIT access boundary, target phases, and open
      questions with owners or decisions.

- [ ] 0.2 Decide the first full-text slice.
      Verification: a short note records whether the first slice is
      USENIX/PVLDB only, arXiv/OpenReview only, or a mixed venue/year
      slice, with expected paper and asset counts.

## 1. Corpus Coverage

- [ ] 1.1 Build a venue/year coverage report for the current committed
      paper cut.
      Verification: a report under `deployments/memex-sr/reports/`
      records expected venue-years, landed counts, provider
      distribution, missing venues, missing years, and suspicious
      over/under-counts.

- [ ] 1.2 Add paper quality checks.
      Verification: report output covers duplicate DOI, duplicate title
      within venue/year, missing title/year/venue, missing authors,
      missing source records, missing `published_in`, and likely
      non-main-track records.

## 2. Target Paper Sources

- [ ] 2.1 Implement DBLP as the authoritative venue/year enumerator.
      Verification: fixture publish creates `paper`, `person`, `venue`,
      and `venue_edition` rows plus `authored_by` and `published_in`
      edges with no narrowing violations.

- [ ] 2.2 Bound metadata enrichers to the selected target set.
      Verification: fixture/provider tests prove Crossref, OpenAlex,
      Semantic Scholar, OpenReview, and arXiv enrich only target papers
      or accepted same-paper aliases.

- [ ] 2.3 Add source progress for every high-volume metadata source.
      Verification: rerunning unchanged fixtures appends zero node/edge
      facts and `okg metrics --source-sync` reports no DLQ.

## 3. Acquisition Planning And Audit

- [x] 3.1 Define the access-basis policy and first-pass acquisition
      planner.
      Verification: `uv --project external/okg run python
      "$PWD/deployments/memex-sr/scripts/plan_acquisition.py"
      --include-textbooks --out /tmp/memex-sr-acquisition-plan.json`
      succeeds and reports 7,312 records on the committed cut.

- [ ] 3.2 Add verified asset URL audit.
      Verification: every candidate asset is classified as direct PDF,
      landing-only, inferred-needs-verification, publisher/manual,
      blocked, or operator-supplied; audit results are written to a
      stable manifest.

- [ ] 3.3 Add MIT/manual operator queue output.
      Verification: publisher/manual records include title, DOI or URL,
      source paper id, recommended library/browser action, access basis,
      and required local manifest fields.

## 4. Open Downloader And Operator Registrar

- [ ] 4.1 Implement a host-governed open downloader.
      Verification: fixture tests cover cache-first behavior,
      contactful user-agent, per-host concurrency/delay, Retry-After,
      backoff, conditional request validators, checkpointed manifest
      writes, and idempotent reruns.

- [ ] 4.2 Implement local operator asset registration.
      Verification: registrar hashes local files, validates required
      provenance fields, writes `acquired_assets.jsonl`, and performs no
      network access.

- [ ] 4.3 Prove downloader no-op behavior.
      Verification: running the same acquisition manifest twice produces
      no duplicate downloaded files or acquired manifest records.

## 5. Parsing And Chunk Publication

- [ ] 5.1 Adapt generic PDF parsing from `af_pubs` mechanics.
      Verification: parser tests cover text-layer PDFs, scanned/no-text
      PDFs, parser-version invalidation, page count, line/bbox indexes,
      parse warnings, and table/figure best-effort extraction.

- [ ] 5.2 Add HTML/Markdown/plain-text parsing for curated web assets.
      Verification: fixture manifests publish documents and chunks with
      canonical URL, title, fetch timestamp, content hash, parser
      bundle, and heading path.

- [ ] 5.3 Publish structured full-text facts from local manifests.
      Verification: fixture publish creates parent-scoped `paper ->
      document -> document_section -> document_chunk` facts with
      accepted narrowings and no live network access.

- [ ] 5.4 Prove parse no-op and changed-record behavior.
      Verification: unchanged acquired assets append zero facts; changing
      one asset or parser version scopes recompute to the affected asset
      and its dependent chunks.

## 6. Evidence, Distillation, And Engram Use

- [ ] 6.1 Emit evidence slices from document chunks.
      Verification: a real publish creates evidence slices with
      `extracted_from` paths back to chunks, documents, and papers.

- [ ] 6.2 Generate first-pass textbook-style distillation sections.
      Verification: claims, trade-offs, mechanisms, failure modes, and
      open problems carry evidence ids, source generation, and freshness
      watermarks.

- [ ] 6.3 Add Engram context-packet smoke task.
      Verification: an Engram/Codex smoke query retrieves a paper,
      chunks, evidence ids, and a compact context packet from a pinned
      Memex-SR generation.

## 7. Final Acceptance

- [ ] 7.1 Publish a first real full-text slice.
      Verification: `okg generation describe <g> --deployment
      memex-sr` reports `published`; live row counts match the acquired
      manifest and parser output counts.

- [ ] 7.2 Run integrity checks.
      Verification: `okg doctor`, source-sync metrics, acquisition
      coverage, parser warnings, and DLQ checks are clean or have
      documented non-blocking warnings.

- [ ] 7.3 Document collaborator extension workflow.
      Verification: docs show how to add a venue, source, corpus pack,
      parser/chunker, operator asset, and distillation method with the
      required fixture and publish checks.
