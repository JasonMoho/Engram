# Memex-SR

Memex-SR is the Engram-owned OKG deployment for autonomous systems
research. It is planned as an external OKG deployment: this repository
owns the deployment configuration, source adapters, ontology modules,
Engram integration, and run-artifact indexing, while `external/okg`
provides the OKG substrate.

The deployment starts with systems and database papers from 2022 through
2026 year-to-date, then expands through declarative corpus packs for
historical papers, adjacent CS venues, technical reports, standards,
curated research/engineering blogs, and operator-supplied assets.

Planning artifacts live under [`spec/`](spec/):

- [`proposal.md`](spec/proposal.md) explains why this deployment exists
  and what changes.
- [`source-ingestion-proposal.md`](spec/source-ingestion-proposal.md)
  is the focused proposal for paper/textbook/report/blog ingestion,
  acquisition, parsing, and incremental execution.
- [`source-ingestion-tasks.md`](spec/source-ingestion-tasks.md) tracks
  the implementation checklist for that ingestion proposal.
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

- [`deployment.yaml`](deployment.yaml) declares the external OKG
  deployment.
- [`HANDOFF.md`](HANDOFF.md) is the collaborator handoff runbook.
- [`source_registry.yaml`](source_registry.yaml) indexes the local
  Memex-SR design corpus.
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
- [`docs/okg-newcomer-guide.md`](docs/okg-newcomer-guide.md) gives a
  first-reader explanation of OKG, the current graph, and extension
  workflow.
- [`docs/source-sampling.md`](docs/source-sampling.md) explains the
  source sampler and coverage outputs.
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
