## Why

Why is this broken?

The current Cloudcast plan is useful as deployment notes, but it is not
yet an executable Engram change contract. Engram has no formal
OpenSpec capability for the Cloudcast OKG benchmark slice, no
OpenRouter reproduction path, no graph-backed Cloudcast context packet,
and no run harvester that can publish Engram experiment evidence back
into Memex-SR.

The root cause is a boundary mismatch: Cloudcast work spans Engram,
SystemBench, and the external OKG deployment, but until now it was
captured as ad hoc Memex-SR docs. This change makes the work spec
driven and pins the benchmark controls before implementation.

## What Changes

- Add a formal Cloudcast OKG benchmark-slice capability for Memex-SR.
- Build a Cloudcast literature and benchmark artifact source plan that
  covers systems papers, algorithms, data structures, cloud economics,
  and implementation patterns.
- Add an OpenRouter-compatible reproduction path for the paper's
  headline Cloudcast setting: `o3`, Direction prompt, 10 runs, and 100
  evaluation calls per run.
- Add a Codex CLI baseline arm that invokes `codex exec` with
  `gpt-5.5` and `model_reasoning_effort="high"` under the same
  Cloudcast evaluator and contamination controls.
- Add a Codex CLI + OKG MCP treatment arm that keeps the same Codex
  controls but exposes bounded Memex-SR graph tools through MCP.
- Require reconciliation of the local prompt's `$419` expert-solution
  target with the Engram paper's `$626` Cloudcast human-SOTA reference
  before using either as a benchmark claim.
- Add context-packet requirements for pinned OKG generation ids,
  evidence ids, source hashes, and oracle/holdout exclusion.
- Add Engram result-harvesting requirements so Cloudcast run artifacts
  become graph evidence through normal Memex-SR source publication.
- No breaking changes to the current baseline Engram run path: when OKG
  and OpenRouter flags are absent, Cloudcast runs as it does today.

## Capabilities

### New Capabilities

- `memex-sr-cloudcast-benchmark`: Defines the Cloudcast-specific OKG
  corpus slice, benchmark controls, context-packet contract,
  OpenRouter reproduction path, and Engram run harvesting.

### Modified Capabilities

- None. Engram OpenSpec was initialized in this change, so there are no
  existing Engram specs to modify.

## Impact

- Affected docs:
  - `deployments/memex-sr/spec/cloudcast-okg-ab-proposal.md`
  - `deployments/memex-sr/spec/cloudcast-okg-ab-tasks.md`
  - `deployments/memex-sr/spec/cloudcast-literature-plan.md`
  - `deployments/memex-sr/README.md`
  - `deployments/memex-sr/source_registry.yaml`
- Affected future code:
  - `examples/handoff_example_usage.py`
  - `deployments/memex-sr/scripts/run_cloudcast_codex_baseline.sh`
  - `Architect/methods/agentic_handoff.py`
  - Memex-SR source adapters, manifests, context-packet generator, and
    harvester modules.
- External dependency consideration:
  - OpenRouter via OpenAI-compatible API base URL and model slugs.
  - Codex CLI with authenticated OpenAI access for
    `codex_cli_gpt55_high`.
- OKG substrate impact:
  - None intended for the first slice. If implementation requires new
    substrate behavior, create a separate change in
    `external/okg/openspec`.
