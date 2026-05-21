# Project Context

## Purpose

Engram is an autonomous systems-researcher architecture. It runs
agentic optimization loops over systems benchmarks, archives experiment
artifacts, and transfers compact research knowledge between agents.

The Memex-SR deployment under `deployments/memex-sr/` uses OKG as an
external knowledge substrate for systems-research context. Engram owns
the deployment configuration, benchmark integration, context-packet
contracts, run harvesting, and collaborator-facing docs. The OKG
substrate itself lives in the `external/okg` submodule.

## Key Directories

- `Architect/`: Engram optimization methods and DeepAgents runners.
- `SystemBench/`: benchmark problems, evaluators, prompts, and seed
  programs.
- `examples/`: runnable experiment entry points.
- `deployments/memex-sr/`: Engram-owned Memex-SR OKG deployment.
- `docs/`: architecture notes and OKG/Engram integration docs.
- `external/okg/`: OKG submodule with its own OpenSpec workspace.
- `openspec/`: Engram-level OpenSpec changes and specs.

## Spec Boundaries

Use Engram OpenSpec for:

- benchmark harness changes;
- OpenRouter/model-routing changes;
- Memex-SR deployment sources, manifests, context packets, and run
  harvesters;
- Engram-to-OKG tool contracts;
- collaborator-facing deployment workflows.

Use `external/okg/openspec` for:

- substrate source-runner behavior;
- catalog, narrowing, projection, enrichment, or generation-ledger
  behavior;
- MCP server tool-surface changes;
- reusable OKG ontology/library modules.

## Conventions

- Prefer small, verifiable changes.
- Keep benchmark controls explicit: prompt, model, budget, seed/run id,
  evaluator hash, and result parser version.
- Avoid oracle leakage in benchmark contexts. Files or prompts that
  reveal expert solutions must be marked holdout-only.
- Memex-SR graph facts must enter through source adapters and published
  OKG generations, not direct writes to live graph tables.
- Long-running experiments should be reproducible from committed config
  and should save run metadata beside results.

## Verification

OpenSpec tasks for Memex-SR OKG work should include both Engram and OKG
checks:

- Engram smoke run or fixture parser output for benchmark-harness work.
- OKG catalog load and real publish generation for graph-shape work.
- Published node/edge deltas for new sources.
- No-op rerun checks for incremental behavior.
- Context-packet metadata checks for generation id, evidence ids, source
  hashes, and holdout exclusion.

Substrate changes additionally follow `external/okg/AGENTS.md`.
