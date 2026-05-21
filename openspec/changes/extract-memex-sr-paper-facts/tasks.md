## 1. Extraction Manifest

- [x] 1.1 Add an offline extractor for full-text paper chunks.
  Verification: running the extractor against generation 10 writes a
  JSONL manifest with non-zero evidence, principles, mechanisms,
  trade-offs, or anti-patterns, and every row includes paper and chunk
  provenance. Verified on 2026-05-20: 10 papers produced 61 evidence,
  29 principles, 30 mechanisms, 24 trade-offs, and 19 anti-patterns.
- [x] 1.2 Cache extraction responses outside OKG publish. Verification:
  rerunning the extractor with the same inputs reuses cached responses or
  produces byte-identical manifest rows for unchanged papers. Verified on
  2026-05-20: two cached reruns produced manifest SHA-256
  `7a550dee6022134a28c565e837866a7e12c6be9b5356bbc312c2e4aedcb3cabb`.

## 2. OKG Source Projection

- [x] 2.1 Add a `paper_research_facts` Memex-SR source adapter.
  Verification: a source smoke run emits non-zero `generic_evidence`,
  `design_principle`, `mechanism`, `trade_off`, and/or `anti_pattern`
  node facts from the manifest. Verified on 2026-05-20 by the generation
  11/12 source runs: 163 paper-research nodes and 149 semantic edges
  emitted from the manifest.
- [x] 2.2 Register the source in `source_registry.yaml`. Verification:
  `okg ingest --include paper_research_facts` can import the source.
  Verified on 2026-05-20 by successful `okg ingest --include
  paper_research_facts` publishes.

## 3. Publish And Verify

- [x] 3.1 Publish the first paper-distillation generation.
  Verification: the published generation increases live counts for
  systems-research fact subtypes and connects principles/mechanisms back
  to paper provenance. Verified on 2026-05-20: generation 12 has 66
  evidence, 33 principles, 34 mechanisms, 27 trade-offs, 23
  anti-patterns, 29 `emerged_from` paper edges, and 30 `cited_in` paper
  edges.
- [x] 3.2 Verify incrementality. Verification: a no-change rerun appends
  zero facts or skips publish with `no_source_work`. Verified on
  2026-05-20: no-change rerun appended zero facts and skipped publish
  with `reason=no_source_work`.
- [x] 3.3 Record a paper-distillation coverage report. Verification: the
  report includes generation id, fact subtype counts, evidence coverage,
  model/extractor metadata, failures, and no-op rerun evidence. Verified
  in `deployments/memex-sr/reports/paper-fulltext/paper-distillation-gen12.md`.
