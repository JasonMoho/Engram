# Proposal: Cloudcast OKG A/B Evaluation Slice

## Why

Why is this broken?

The incomplete substrate stages are **source coverage**, **projection**,
**read-side surfacing**, and **write-side indexing**.

Memex-SR has a useful phase-0 graph for deployment planning and paper
metadata, but it does not yet contain the Cloudcast problem, the
Cloudcast-relevant literature, or the evidence-backed principles that
would help an Engram agent design a better multi-cloud multicast
algorithm. Engram also cannot yet receive an OKG context packet or
bounded OKG tools in the Cloudcast run path, and Memex-SR cannot yet
harvest the resulting Engram experiments back into the graph.

Without those pieces, an "OKG-assisted Cloudcast" run would mostly be
prompt decoration. The graph must contain relevant evidence, expose it
through a pinned and budgeted interface, and record whether it changed
the agent's search behavior.

## Purpose

Build a focused Memex-SR slice for Cloudcast and use it to A/B test
Engram with and without OKG assistance.

The companion literature and reproduction plan is
`deployments/memex-sr/spec/cloudcast-literature-plan.md`.

Cloudcast is the right first target because it is cheap, local, and
systems-native:

- It is already included in Engram under
  `SystemBench/ADRS/cloudcast/`.
- It is a real networking/systems optimization task: constrained
  multi-cloud broadcast routing with cost, throughput, ingress, egress,
  partitioning, and path-selection constraints.
- It has clear failure modes where literature-backed context should
  help: overusing shortest paths, treating the problem as a pure
  Steiner tree, ignoring partition-level capacity, or optimizing cost
  without respecting bottleneck throughput.
- It produces a scalar metric that can be compared across runs. The
  evaluator returns `combined_score = 1 / (1 + total_cost)`, so higher
  score means lower cost.

The first hypothesis is narrow:

> A Cloudcast-specific OKG context packet should help Engram converge
> faster toward optimization-first designs, especially min-cost flow,
> MILP, decomposition, relaxation, and capacity-aware routing families,
> while avoiding known dead ends.

## Current State

Engram already has:

- `examples/handoff_example_usage.py --problem_name cloudcast`.
- A default fair Cloudcast prompt at
  `SystemBench/ADRS/cloudcast/deepagents_files/task_prompt_direction.txt`.
- A cheating/with-oracle path when `--give_files` is used; this includes
  `optimal.py` and must not be used in the fair A/B.
- A local evaluator, simulator, initial program, cost profiles,
  throughput profiles, and baseline implementations.
- Run archives with code snapshots, score files, result CSVs, console
  logs, and final JSON results.

Memex-SR already has:

- A phase-0 deployment scaffold under `deployments/memex-sr/`.
- A current paper metadata cut and design-document corpus.
- A proposed Engram integration contract: context-first mode, bounded
  OKG tools, and post-run workspace indexing.
- A checked-in ontology overlay for corpus packs, venues, papers, and
  document assets.

Memex-SR does not yet have:

- Cloudcast benchmark facts in the graph.
- Cloudcast-specific evidence chunks, claims, principles, trade-offs,
  mechanisms, or anti-patterns.
- The richer Engram research-memory ontology implemented in the local
  overlay, even though it is described in the design.
- A context packet generator wired to a pinned OKG generation.
- An Engram command-line flag that appends an OKG context packet.
- A harvester that turns Cloudcast run artifacts into graph facts.

## Goals

- Build a Cloudcast evidence slice in Memex-SR before running expensive
  experiments.
- Keep the first run reproducible: every context packet records the OKG
  generation id, evidence ids, topic inputs, prompt hash, and source
  manifests.
- Preserve the fair benchmark boundary: no `optimal.py`, no
  `task_prompt_direction_with_optimal.txt`, and no oracle solution text
  enters the treatment arm.
- Add a minimal Engram integration that can run in three modes:
  baseline, OKG context-packet-only, and later OKG context plus bounded
  live lookup tools.
- Add a separate Codex CLI baseline using `gpt-5.5` with high reasoning
  effort, scored by the same Cloudcast evaluator.
- Harvest Cloudcast results back into OKG as research-memory facts so
  the graph learns from both successes and failures.
- Produce a small report comparing vanilla Engram and OKG-assisted
  Engram, plus the Codex CLI baseline, on best cost, score,
  simulations-to-threshold, time, and design family.

## Non-Goals

- Do not build the complete full-text systems literature corpus before
  this experiment.
- Do not bulk-download publisher content or use scripted MIT-auth
  downloads.
- Do not expose raw SQL or unbounded graph scans to Engram agents.
- Do not treat the OKG packet as ground truth. It is research guidance
  with evidence links.
- Do not use the oracle/optimal Cloudcast implementation in either
  benchmark arm unless the run is explicitly labeled as an oracle
  ablation and excluded from fair comparisons.

## Data We Will Build

### Benchmark Artifact Layer

Represent Cloudcast itself as graph data so the OKG can reason about the
task and later link runs back to the exact benchmark version.

Required artifacts:

- Benchmark problem: `cloudcast`.
- Fair task prompt:
  `SystemBench/ADRS/cloudcast/deepagents_files/task_prompt_direction.txt`.
- Evaluator and simulator files:
  `evaluator.py`, `simulator.py`, `broadcast.py`, `utils.py`.
- Initial program:
  `initial_program.py`.
- Input data:
  `profiles/cost.csv` and `profiles/throughput.csv`.
- Configuration:
  `config_direction.yaml`.
- Public baseline implementations:
  `baselines.py` and `cloudcast_opt.py`, if they are already part of
  the benchmark context available to both arms.
- Holdout/oracle artifacts:
  `optimal.py` and `task_prompt_direction_with_optimal.txt`, recorded
  only as excluded evaluation artifacts. They must not be reachable by
  agent-facing context tools in the fair treatment arm.

### Literature And Reference Layer

Seed the graph with a small, high-quality Cloudcast-relevant corpus
before scaling up.

Initial topics:

- multi-cloud multicast and overlay routing;
- inter-datacenter traffic engineering;
- min-cost flow and multi-commodity flow formulations;
- directed Steiner tree and multicast tree approximations;
- capacity-constrained path selection;
- decomposition of mixed-integer routing problems;
- cloud egress pricing and cost-aware routing;
- bandwidth bottleneck and straggler-aware transfer scheduling.

Initial venue/source scope:

- systems/networking venues already in the Memex-SR target set:
  SIGCOMM, NSDI, CoNEXT, HotNets, OSDI, SOSP, EuroSys, USENIX ATC, and
  SoCC;
- database/systems-adjacent optimization papers when directly relevant;
- open technical reports, RFC-style documents, and engineering posts
  only from curated manifests;
- MIT/manual assets only when a human operator supplies the local file.

The first slice should be small enough to review manually. A target of
20-50 papers/documents is enough for the first A/B if the evidence is
well chunked and the packet is concise.

### Evidence And Distillation Layer

The context packet should be generated from structured graph facts, not
from one hand-written blob.

Represent:

- problem classes such as constrained broadcast routing, min-cost
  multicast, and multi-commodity flow;
- mechanisms such as shortest-path baselines, directed tree heuristics,
  min-cost flow, MILP, LP relaxation, rounding, decomposition, and
  partition-aware routing;
- design principles such as "model capacity before optimizing price" or
  "separate topology selection from per-partition assignment when the
  full integer problem is too large";
- trade-offs such as cost versus transfer time, shared tree reuse versus
  path diversity, exact MILP quality versus solve time, and egress price
  versus bottleneck capacity;
- anti-patterns such as single-path routing for all partitions,
  ignoring provider egress limits, or optimizing only edge cost.

Each item needs provenance: source document id, chunk id, extraction or
distillation method, confidence or review state, and the OKG generation
that published it.

### Engram Research-Memory Layer

Harvest Cloudcast runs into graph facts after the experiment.

Represent:

- `ResearchRun`: one benchmark run arm and seed.
- `AgentAttempt`: each Engram agent in the handoff chain.
- `Experiment`: each `run_simulation` call.
- `CandidateImplementation`: code snapshots.
- `MetricObservation`: score, inferred total cost, success flag, time,
  and threshold crossings.
- `FailureDiagnosis`: invalid paths, missing constraints, timeouts,
  solver failures, and repeated dead ends.
- `ResearchNote`: journal entries and final summaries.
- `WorkspaceArtifact`: logs, CSVs, prompts, configs, and result JSON.

The current Memex-SR design already names these subtypes, but the local
overlay must still be extended and verified before the harvester can
publish them.

## Ontology Plan

Use existing substrate modules wherever possible:

- `git_graph` for source files and repo provenance.
- `extraction` for `Document`, `DocumentSection`, `DocumentChunk`,
  `EvidenceSlice`, and `Claim` where available.
- `reasoning` for evidence and hypothesis-like records where the
  substrate already provides the vocabulary.
- `methodology` only if it is composed into this deployment for
  `Principle`, `Mechanism`, `Tradeoff`, `AntiPattern`, or equivalent
  vocabulary; otherwise keep those labels as attrs on `Claim` or
  deployment-local distillation records for the first slice.
- `agent_memory` where it already models agent observations,
  experiments, or claims.
- Memex-SR deployment-local overlay for benchmark-specific and Engram
  run-specific nodes that do not belong in the substrate.

Expected deployment-owned additions:

- `BenchmarkProblem`
- `BenchmarkArtifact`
- `BenchmarkRunConfig`
- `ContextPacket`
- `ResearchRun`
- `AgentAttempt`
- `Experiment`
- `CandidateImplementation`
- `MetricObservation`
- `FailureDiagnosis`
- `ResearchNote`
- `WorkspaceArtifact`

Expected bridge narrowings:

- benchmark contains benchmark artifact;
- benchmark artifact derived from source file;
- context packet references evidence slice;
- context packet references claim or principle;
- research run used context packet;
- research run evaluates benchmark problem;
- agent attempt member of research run;
- experiment member of agent attempt;
- candidate implementation produced by experiment;
- metric observation measures experiment;
- failure diagnosis describes experiment;
- workspace artifact derived from source file;
- candidate implementation informed by evidence or context packet.

Every new emitted edge route needs a narrowing before projection. A
fixture publish must prove that each route lands in a published
generation.

## OKG To Engram Integration

### Context-First Mode

Add an Engram CLI option such as:

```bash
python examples/handoff_example_usage.py \
  --problem_name cloudcast \
  --model o3 \
  --num_runs 1 \
  --max_agents 1 \
  --agent_timeout 10 \
  --okg_context_file deployments/memex-sr/context_packets/cloudcast.md
```

The implementation should append the packet to the task prompt and save
packet metadata into the run directory:

- context packet path;
- packet content hash;
- OKG generation id;
- evidence ids;
- topic list;
- packet generator version.

When the flag is absent, Engram must behave exactly as it does now.

### Targeted Lookup Mode

After context-first mode works, add bounded tools next to
`run_simulation`:

- `okg_search`
- `okg_get_node`
- `okg_list_neighbors`
- `okg_traverse_path`
- `okg_context_packet`

These tools should wrap the regular OKG MCP surface with strict limits:
pinned generation, max result count, max output tokens, allowed routes,
and no raw SQL. The first A/B should not depend on live lookup mode; it
is a second treatment arm.

### Codex CLI Baseline

Add a non-Engram baseline arm named `codex_cli_gpt55_high`. This arm
tests how a strong general coding agent performs when given the fair
Cloudcast task directly.

This is a fair out-of-box baseline, not a strict Engram architecture
ablation. The goal is to see how Codex CLI performs with normal
shell/edit/search affordances when the benchmark setup is clean:
same fair task, no oracle files, no OKG help, explicit budget, and
external scoring.

Suggested command shape:

```bash
.venv/bin/python deployments/memex-sr/scripts/run_cloudcast_codex_baseline.py \
  --max-evals 2 \
  --codex-timeout-seconds 900
```

Controls:

- use the same fair prompt and initial program as Engram control;
- give Codex an isolated benchmark workspace with `task.md`,
  `initial_program.py`, candidate output instructions, and an
  `evaluate_candidate` command;
- allow normal Codex CLI behavior inside that workspace: shell, file
  editing, search, and command execution;
- enforce a configured evaluation-call cap in the evaluator wrapper and
  record every attempt;
- exclude `optimal.py`, `task_prompt_direction_with_optimal.txt`, OKG
  context packets, and live OKG tools from this baseline;
- capture Codex CLI version, command, model, reasoning effort, prompt
  hash, evaluator hash, allowed-file manifest hash, JSONL event log,
  final message, generated candidate hash, elapsed time, and normalized
  Cloudcast metrics;
- score only with the Cloudcast evaluator, not with Codex's self-report.

### Workspace Indexing

After each run, the harvester should read the Engram run directory and
publish it through normal OKG source mechanics. It should not write
directly to live graph tables.

The harvester input should include:

- run directory;
- problem name;
- benchmark arm;
- model;
- seed/run index;
- OKG context packet id, if used;
- OKG generation id, if used.

The output must be deterministic and content-addressed so a no-op
harvest appends zero new facts.

## Run Protocol

### Phase 1: Graph Slice

1. Publish the Cloudcast benchmark artifact source.
2. Publish the curated Cloudcast literature/reference manifest.
3. Publish parsed chunks for open or operator-supplied local assets.
4. Publish evidence/distillation facts.
5. Generate one Cloudcast context packet from a pinned generation.

Required checks:

- generation publishes, not blocked;
- expected benchmark, artifact, document, chunk, evidence, and claim
  counts appear in the published graph;
- context packet contains generation id and evidence ids;
- no-op rerun of the sources appends zero facts.

### Phase 2: Cheap A/B Smoke

Run one short control and one short treatment to verify wiring:

```bash
python examples/handoff_example_usage.py \
  --problem_name cloudcast \
  --model o3 \
  --num_runs 1 \
  --max_agents 1 \
  --agent_timeout 5 \
  --results_dir cloudcast_control_smoke
```

```bash
python examples/handoff_example_usage.py \
  --problem_name cloudcast \
  --model o3 \
  --num_runs 1 \
  --max_agents 1 \
  --agent_timeout 5 \
  --results_dir cloudcast_okg_context_smoke \
  --okg_context_file deployments/memex-sr/context_packets/cloudcast.md
```

This phase is only a wiring test. Do not overinterpret the score.

Run one Codex baseline smoke with the same fair benchmark inputs:

```bash
.venv/bin/python deployments/memex-sr/scripts/run_cloudcast_codex_baseline.py \
  --max-evals 2 \
  --codex-timeout-seconds 900
```

The harness should then evaluate the produced candidate with the local
Cloudcast evaluator and save normalized metrics in the same report
shape as the Engram arms.

The report should label this as `fair_out_of_box_baseline`. A later
matched-control Codex arm can be added if we want a stricter architecture
ablation, but that is not the main purpose of this baseline.

### Phase 3: Pilot A/B

Run a small pilot:

- Arms: Engram control, Engram OKG context-packet-only, and Codex CLI
  baseline.
- Seeds/runs: 3 per arm.
- Budget: same model, same timeout, same `max_agents`, same prompt
  except for the OKG packet. The Codex CLI arm records comparable wall
  time and evaluator calls instead of Engram agent count, and is labeled
  as a fair out-of-box baseline.
- Suggested first budget: `max_agents=1`, `agent_timeout=10`.

Report:

- best score;
- inferred total cost: `1 / score - 1`;
- total simulations;
- time to first valid solution;
- time or simulations to beat published thresholds;
- dominant design family;
- evidence ids cited or reflected in the solution summary;
- repeated dead ends and failures.

### Phase 4: Serious A/B

Only after the pilot shows the harness is stable:

- Arms: control, OKG context-packet-only, and optionally OKG targeted
  lookup, plus Codex CLI baseline if the smoke run is stable.
- Seeds/runs: 10 per arm.
- Budget: paper-like enough to be credible, likely `max_agents=5`,
  `agent_timeout=30`, or an agreed simulation cap.
- Same benchmark prompt and same access to files across arms.

Compare against published paper thresholds where useful:

- Engram paper Cloudcast average cost: `662.2`.
- Glia: `705.8`.
- OpenEvolve: `728.0`.
- FunSearch: `718.5`.
- EoH: `782.2`.
- Human SOTA reference: about `626`.

The exact target for this proposal is not to beat every published
number immediately. The first target is to show whether graph-backed
context improves search quality or speed at a fixed budget.

## Reporting

Create a run report under:

```text
deployments/memex-sr/reports/cloudcast-ab/
```

The report should include:

- graph generation and count snapshot used for each treatment;
- context packet file and evidence index;
- exact commands and environment variables;
- run directories;
- per-run metrics;
- aggregate mean, median, best, and variance;
- qualitative design-family labels;
- contamination audit confirming oracle files were excluded;
- follow-up changes for the next benchmark.

## Resource Needs

### Compute

- Chunky or equivalent CPU server is enough.
- No GPU is required.
- Minimum practical local setup: 16 CPU cores, 64 GB RAM, 100 GB free
  disk.
- Recommended working directory on chunky: `/data1/$USER/Engram`, not
  AFS, because long runs should not depend on AFS token lifetime.

### Services

- Docker access for OKG Postgres and Engram shell-tool containers.
- A local OKG Postgres database for Memex-SR.
- OpenAI API credentials for the selected model.
- Codex CLI installed and authenticated for `gpt-5.5`.
- Optional: persistent tmux session for long chunky runs.

### Data

- No external full-text corpus is needed for the first smoke run.
- For the first useful A/B, we need a curated Cloudcast literature
  manifest and open/operator-supplied PDFs or HTML assets for the
  selected seed set.
- MIT access can help retrieve licensed materials manually, but the
  pipeline should index only local operator-supplied files and should
  not automate authenticated publisher downloads.

### Decisions Needed

- Which model to use for the first pilot: `o3`, `gpt-5.2`, or another
  available model.
- Pilot budget: number of runs, `max_agents`, and `agent_timeout`.
- Whether the first treatment is context-packet-only, or whether to add
  bounded live OKG tools before the pilot.
- Whether the Codex baseline should stay no-OKG only, or whether a later
  Codex-plus-OKG-context treatment is worth adding.
- Which Cloudcast-relevant papers/documents should be in the first
  manually reviewed evidence slice.
- Whether published baseline costs should be shown to both arms as
  benchmark context or held out as report-only thresholds.

## Risks And Controls

- **Oracle leakage.** Exclude `optimal.py` and
  `task_prompt_direction_with_optimal.txt` from agent-facing OKG
  context and tools in fair runs.
- **Prompt-only confound.** The packet must carry evidence ids and be
  generated from a pinned graph, not hand-written per run.
- **Small-sample noise.** Use pilot results only for harness validation;
  use at least 10 runs per arm for claims.
- **Graph incompleteness.** Label each packet section by evidence
  quality: full-text supported, metadata-only, or operator-written
  hypothesis.
- **Slow runs.** Start with context-first mode and avoid live lookup in
  the simulation loop.
- **Incremental correctness.** Require no-op source reruns and harvest
  reruns to append zero facts.

## Acceptance Criteria

- A published Memex-SR generation contains Cloudcast benchmark artifact
  nodes and the selected literature/evidence nodes.
- The context packet generator emits a Cloudcast packet with generation
  id, source hashes, evidence ids, and token budget metadata.
- Engram runs unchanged when no OKG flag is supplied.
- Engram can run Cloudcast with the OKG context packet and records the
  packet id/hash in the result directory.
- The Codex CLI baseline can run with `gpt-5.5` high reasoning effort,
  stores run artifacts, and is scored by the same Cloudcast evaluator.
- The harvester publishes at least one fixture Cloudcast run into OKG as
  research-memory facts.
- A no-op rerun of Cloudcast sources and the run harvester appends zero
  new facts.
- The A/B report lists graph counts, run commands, per-run metrics,
  aggregate metrics, and contamination controls.
