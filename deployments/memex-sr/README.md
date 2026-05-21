# Memex-SR

Memex-SR is the Engram-owned OKG deployment for autonomous systems
research. It is now scaffolded from OKG's upstream
`systems-research` profile: this repository owns the deployment
configuration, paper-cut manifest, Engram integration, and run-artifact
indexing, while reusable ontology modules and source adapters live in
the `external/okg` substrate submodule.

The deployment starts with systems and database papers from 2022 through
2026 year-to-date, then expands through declarative corpus packs for
historical papers, adjacent CS venues, technical reports, standards,
curated research/engineering blogs, and operator-supplied assets.

Planning artifacts live under [`spec/`](spec/):

The formal OpenSpec change for the first Cloudcast benchmark slice is
[`openspec/changes/add-cloudcast-okg-benchmark-slice/`](../../openspec/changes/add-cloudcast-okg-benchmark-slice/).
The follow-on proposal for making that slice source-backed and
actionable is
[`openspec/changes/make-cloudcast-okg-actionable/`](../../openspec/changes/make-cloudcast-okg-actionable/).

- [`proposal.md`](spec/proposal.md) explains why this deployment exists
  and what changes.
- [`source-ingestion-proposal.md`](spec/source-ingestion-proposal.md)
  is the focused proposal for paper/textbook/report/blog ingestion,
  acquisition, parsing, and incremental execution.
- [`source-ingestion-tasks.md`](spec/source-ingestion-tasks.md) tracks
  the implementation checklist for that ingestion proposal.
- [`cloudcast-okg-ab-proposal.md`](spec/cloudcast-okg-ab-proposal.md)
  defines the first benchmark slice: build a Cloudcast-specific OKG
  evidence graph, feed it to Engram, and A/B test against vanilla
  Engram.
- [`cloudcast-okg-ab-tasks.md`](spec/cloudcast-okg-ab-tasks.md)
  tracks that Cloudcast graph, context-packet, Engram integration,
  harvest, and reporting work.
- [`cloudcast-literature-plan.md`](spec/cloudcast-literature-plan.md)
  defines the Cloudcast literature, algorithm, data-structure, and
  OpenRouter/Codex baseline reproduction plan for the first benchmark
  slice.
- [`design.md`](spec/design.md) defines the corpus, ontology,
  DBOS-aligned execution model, Engram tool contract, and Engram
  workspace indexer.
- [`tasks.md`](spec/tasks.md) is the implementation checklist.
- [`memex-sr-deployment.md`](spec/memex-sr-deployment.md) is the
  requirement/spec text.

If you are new to OKG, start with
[`docs/okg-newcomer-guide.md`](docs/okg-newcomer-guide.md). It explains
what OKG is, what is currently in the Memex-SR graph, and how to extend
the deployment without touching substrate internals.

For handoff, use [`HANDOFF.md`](HANDOFF.md). It gives the clean-clone
bootstrap path, smoke checks, MCP setup, and the exact next work before
full-text acquisition.

Runtime artifacts live beside the spec:

- [`deployment.yaml`](deployment.yaml) declares the profile-driven OKG
  deployment and loads the Engram-specific `engram_runs` module.
- [`HANDOFF.md`](HANDOFF.md) is the collaborator handoff runbook.
- [`source_registry.yaml`](source_registry.yaml) indexes the paper cut,
  local Memex-SR design corpus, and Engram run artifacts.
- [`venues.yaml`](venues.yaml), [`corpus_packs.yaml`](corpus_packs.yaml),
  [`corpus_policy.yaml`](corpus_policy.yaml), and
  [`download_host_policy.yaml`](download_host_policy.yaml) define the
  target venue matrix, expansion packs, incremental policy, and host
  governance.
- [`acquisition_policy.yaml`](acquisition_policy.yaml),
  [`textbook_sources.yaml`](textbook_sources.yaml), and
  [`docs/source-acquisition.md`](docs/source-acquisition.md) define the
  paper/textbook acquisition lanes, including open automated fetches
  versus MIT-authenticated operator queues.
- [`data_sources.yaml`](data_sources.yaml) declares bounded source
  samples for provider and ontology coverage checks.
- [`extractors.yaml`](extractors.yaml) parses and chunks Markdown/text.
- [`PHASE0.md`](PHASE0.md) gives the local build and Codex CLI MCP
  smoke-test commands.
- [`scripts/bootstrap_local.sh`](scripts/bootstrap_local.sh) performs
  the clean local bootstrap against the OKG Postgres compose stack.
- [`scripts/run_cloudcast_codex_baseline.py`](scripts/run_cloudcast_codex_baseline.py)
  runs the fair out-of-box Codex CLI Cloudcast baseline and archives
  run metadata, Codex JSONL events, the candidate, and final evaluator
  metrics under `results/codex_baseline_cloudcast/`.
- [`fixtures/cloudcast_sources.yaml`](fixtures/cloudcast_sources.yaml)
  is the reviewed seed manifest for the actionable Cloudcast corpus.
- [`scripts/plan_cloudcast_acquisition.py`](scripts/plan_cloudcast_acquisition.py)
  dry-runs acquisition/cache actions for that Cloudcast source slice.
- [`scripts/diagnose_cloudcast_okg_usage.py`](scripts/diagnose_cloudcast_okg_usage.py)
  classifies OKG-assisted Cloudcast runs by usage depth, including
  whether evidence was retrieved and cited before coding/evaluation.
- [`docs/okg-newcomer-guide.md`](docs/okg-newcomer-guide.md) gives a
  first-reader explanation of OKG, the current graph, and extension
  workflow.
- [`docs/source-sampling.md`](docs/source-sampling.md) explains the
  source sampler and coverage outputs.
- [`docs/chunky-deployment.md`](docs/chunky-deployment.md) gives the
  one-command CSAIL chunky workflow, including checkout relocation,
  branch update, Kerberos/AFS refresh, bootstrap, publish, and
  Cloudcast packet generation.
- [`docs/pre-full-text-readiness.md`](docs/pre-full-text-readiness.md)
  records the current generation-5 local cut, local test loop,
  pre-full-text gates, and repo-readiness checklist.

Current local cut:

- Published generation: `5`
- Live graph: 25,827 nodes and 39,561 edges
- Papers: 4,782
- Sources in the current cut: USENIX, PVLDB, and OpenAlex
- Status: metadata and asset URL hints are published; parsed full text
  has not been ingested yet
- Current acquisition-plan shape over the committed cut: 7,312 asset
  plan records, 2,969 open fetch candidates, 185 MIT/manual candidates,
  and 4,158 metadata-only records.

If implementation requires a substrate change in OKG itself, that
should be proposed separately in the OKG repository. Memex-SR-specific
deployment behavior belongs here.
