# Source Sampling

Memex-SR source sampling is a pre-publish check. It asks a small,
host-governed question of each candidate data source and records whether
the source can cover the ontology classes we expect it to cover.

Run from the Engram repo root:

```bash
external/okg/.venv/bin/python deployments/memex-sr/scripts/sample_data_sources.py \
  --config deployments/memex-sr/data_sources.yaml
```

Outputs:

- `deployments/memex-sr/samples/source_samples.json` records per-source
  status, sample items, observed ontology hits, and operational notes.
- `deployments/memex-sr/samples/ontology_coverage.md` summarizes which
  ontology classes are currently covered by successful samples and which
  are still gaps.

The sampler does not download PDFs and does not publish graph facts. It
is intentionally conservative: one request per enabled source, no
retries by default, a contactful user-agent, and per-host delay from
`download_host_policy.yaml`. Production acquisition will still need
fixture tests, host-policy state, progress markers, and a real OKG
publish verification.

Current sample scope:

- Corpus governance configs: venue matrix, corpus packs, corpus policy,
  source declarations, and host policy.
- Real provider samples: USENIX OSDI technical sessions, PVLDB volume
  pages, OpenAlex, Crossref, Semantic Scholar, OpenReview, RFC Editor,
  arXiv, and DBLP.
- Local fixtures: systems artifact manifest for `Dataset`/`Software`/
  `Benchmark` coverage and an Engram archive fixture for research-memory
  ontology coverage.

Current operational findings are intentionally recorded in
`samples/ontology_coverage.md`. In the first run, DBLP shell access was
unreliable, Crossref broad title search was noisy and marked
diagnostic-only, Semantic Scholar needed rate-limit handling,
OpenReview MLSys venue-id discovery returned no notes, and arXiv timed
out from the local workspace.
