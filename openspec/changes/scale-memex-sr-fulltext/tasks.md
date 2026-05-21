## 1. Full-Text Paper Acquisition

- [x] 1.1 Add a cache-first paper full-text acquisition script for open
  PDF assets from `paper_cut.json`. Verification: a dry run reports at
  least 500 eligible open PDF assets across USENIX/PVLDB without network
  access. Verified on 2026-05-20: dry run reported 2,926 eligible open
  PDF assets.
- [x] 1.2 Run a first local acquisition batch. Verification: the JSONL
  manifest records at least 100 available local paper PDFs with content
  hashes and byte counts, and failures are recorded explicitly. Verified
  on 2026-05-20: `paper_fulltext_assets.jsonl` contains 100 available
  local PDFs, 73 fetched, 27 cached, and 0 failures.

## 2. Full-Text Paper Projection

- [x] 2.1 Add a Memex-SR source adapter for cached paper full text.
  Verification: adapter unit smoke emits non-zero `document`,
  `document_chunk`, `contains`, and `member_of` facts from the acquired
  manifest without network access. Verified on 2026-05-20 through the
  generation-10 source run: 100 documents, 3,041 chunks, and 5,058
  source edges emitted from cached PDFs with no network I/O in the source.
- [x] 2.2 Register the source in `source_registry.yaml`. Verification:
  `okg ingest --include paper_fulltext_documents` can import the source.
  Verified on 2026-05-20 by a successful `okg ingest --include
  paper_fulltext_documents` publish.
- [x] 2.3 Publish a materially large full-text generation. Verification:
  a published OKG generation adds at least 100 `document` nodes and at
  least 1,000 `document_chunk` nodes, `okg doctor` reports clean, and
  lexical search retrieves paper-text chunks. Verified on 2026-05-20:
  generation 10 published with 2,691 nodes added, 5,058 edges added,
  100 source-pack documents, 3,041 source-pack chunks, clean doctor, and
  searchable RDMA/congestion-control paper chunks.
- [x] 2.4 Verify incrementality. Verification: a no-change rerun appends
  zero facts or skips publish with `no_source_work`. Verified on
  2026-05-20: a no-change rerun emitted zero new facts and skipped
  publishing with `reason=no_source_work`.

## 3. Distillation Preparation

- [x] 3.1 Record the published full-text coverage report. Verification:
  the report includes generation id, node/edge deltas, source counts,
  venue/year coverage, parse failures, and no-op rerun evidence. Verified
  in `deployments/memex-sr/reports/paper-fulltext/fulltext-publish-gen10.md`.
- [x] 3.2 Define the next extraction target for source-backed principles
  and mechanisms. Verification: tasks specify how extracted facts will
  cite paper chunks/documents as evidence. Verified in the follow-on
  OpenSpec change `extract-memex-sr-paper-facts`, which defines and
  implements source-backed paper distillation with chunk/document
  provenance.
