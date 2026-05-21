## Why

Why is this broken?

The Codex+OKG Cloudcast run proved that the Memex-SR MCP server can be
attached to a benchmark workspace, but it did not prove that OKG helps
research. The agent made only three OKG calls: one graph inspect and two
searches. It then solved mostly from the benchmark prompt and local
files. The OKG arm scored slightly worse than the no-OKG Codex baseline,
and the retrieved graph evidence was too sparse and generic to change a
strong agent's search behavior.

The root cause is not the transport layer. The incomplete stages are:

- **Source coverage:** the Cloudcast graph has paper metadata and a few
  planning chunks, but not enough full-text systems, networking,
  optimization, implementation, and cloud-economics material.
- **Projection and distillation:** the deployment has only a tiny
  first-pass fact pack, with generic principles and little
  algorithm-specific guidance.
- **Read-side surfacing:** the live MCP arm gave the agent optional
  search tools, but no context-first brief, evidence-backed research
  protocol, or compliance checks that force graph evidence into the
  coding plan.
- **Harvest feedback:** prior runs are not yet harvested into Memex-SR
  as reusable research evidence, so the graph does not learn from
  experiments.

Without fixing those stages, "OKG-assisted Cloudcast" is mostly an MCP
plumbing test.

## What Changes

- Build a real Cloudcast research corpus manifest and local acquisition
  workflow covering direct systems papers, algorithmic foundations,
  implementation/data-structure guidance, and cloud cost/measurement
  references.
- Parse and chunk acquired full text into Memex-SR through normal source
  publication, with explicit coverage reports and oracle exclusion.
- Distill Cloudcast-specific typed facts from the corpus into
  `DesignPrinciple`, `Mechanism`, `TradeOff`, `AntiPattern`, and
  `Evidence` nodes with source provenance and confidence/review state.
- Generate a context-first Cloudcast research brief from a pinned OKG
  generation and use that as the primary OKG treatment before relying on
  live MCP discovery.
- Add an optional structured MCP research protocol that requires
  evidence gathering, node-id citations, and plan synthesis before code
  edits or evaluator calls.
- Extend reports to measure OKG usage depth, not just MCP reachability:
  tool calls, evidence ids retrieved, facts cited in the plan, and
  whether usage happened before coding/evaluation.
- Harvest Cloudcast benchmark runs back into OKG as research-memory
  facts so later agents can reuse successful mechanisms, failures, and
  metric observations.

## Capabilities

### New Capabilities

- `memex-sr-actionable-research-context`: Defines the contract for
  turning Memex-SR Cloudcast from a thin graph/MCP attachment into an
  actionable research-context substrate.

### Modified Capabilities

- None directly. This change builds on the active
  `add-cloudcast-okg-benchmark-slice` work. If implementation requires
  OKG substrate behavior beyond Engram-owned deployment/source/report
  code, create a separate change in `external/okg/openspec`.

## Impact

- Affected deployment files:
  - `deployments/memex-sr/source_registry.yaml`
  - `deployments/memex-sr/fixtures/`
  - `deployments/memex-sr/sources/`
  - `deployments/memex-sr/scripts/`
  - `deployments/memex-sr/reports/`
  - `deployments/memex-sr/spec/`
- Affected benchmark harnesses:
  - `deployments/memex-sr/scripts/run_cloudcast_codex_baseline.py`
  - future Engram Cloudcast context-injection path
  - future Engram/Codex OKG usage-compliance reporting
- External dependency considerations:
  - Full-text acquisition should prefer open sources and
    operator-supplied local files. MIT-authenticated downloads must be
    explicit, rate-limited, and cache-backed.
  - No benchmark context may use `optimal.py`,
    `task_prompt_direction_with_optimal.txt`, or facts derived from
    those holdout artifacts.
- OKG substrate impact:
  - None intended for this Engram proposal. Needed reusable ontology,
    source-runner, MCP, or derived-artifact changes belong upstream in
    OKG.
