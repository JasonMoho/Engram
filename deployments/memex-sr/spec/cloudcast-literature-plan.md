# Cloudcast Literature And Reproduction Plan

## Purpose

This plan defines the Cloudcast literature slice for Memex-SR. The goal
is not just to retrieve papers that mention Cloudcast. The goal is to
give an autonomous systems researcher a complete-enough map of the
problem family: cloud multicast, overlay routing, cost-aware transfer,
multicast tree algorithms, network-flow formulations, solver
engineering, graph algorithms, and the data structures needed to turn
those ideas into working code.

The first OKG context packet for Cloudcast should help an Engram agent
answer:

- What problem family is this benchmark really testing?
- Which algorithms are plausible and which are known traps?
- What constraints make the naive formulations intractable?
- Which approximations preserve most of the value?
- What data structures and solver patterns are worth implementing under
  the benchmark's time budget?

## Reproduction Target

The headline Engram paper Cloudcast result used:

- Model: OpenAI `o3`.
- Prompt: Cloudcast "Direction" prompt.
- Runs: 10.
- Budget: 100 evaluation calls per run.
- Metric: best cost per run, lower is better.
- Reported result: Engram average best cost about `$662`.
- Best reported single run: `$625`, slightly below the Cloudcast human
  SOTA reference of `$626`.

The paper also reports sensitivity runs with `gpt-5.2`. The important
qualitative result is that stronger reasoning models shift more
reliably into explicit optimization and MILP-like formulations, while
`o3` plus the direction prompt is the headline reproduction target.

Local repository state:

- The default example uses `--model o3`.
- `SystemBench/ADRS/cloudcast/config_direction.yaml` also names `o3`.
- The paper prompt aligns with
  `SystemBench/ADRS/cloudcast/deepagents_files/task_prompt_direction.txt`.
- The fair run must not use `--give_files`, because that path includes
  `optimal.py` and `task_prompt_direction_with_optimal.txt`.

OpenRouter state:

- `/Users/jason/projects/mit/okg/.env` contains `OPENROUTER_API_KEY`.
- The OpenRouter model catalog exposed `openai/o3` and
  `openai/gpt-5.2` during the May 2026 check.
- OpenRouter is OpenAI-compatible at
  `https://openrouter.ai/api/v1`.

Reproduction needs one small Engram compatibility patch before long
runs:

- Either teach Engram a provider/model alias such as
  `--model openrouter:openai/o3`, or
- normalize `--model o3` to `openai/o3` when `OPENAI_BASE_URL` points at
  OpenRouter.

Without that patch, passing `--model openai/o3` may create awkward
result paths containing `/`, while passing `--model o3` may not be a
valid OpenRouter model slug.

Suggested environment:

```bash
set -a
. /Users/jason/projects/mit/okg/.env
set +a

export OPENAI_API_KEY="$OPENROUTER_API_KEY"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

Suggested smoke target after the compatibility patch:

```bash
python examples/handoff_example_usage.py \
  --problem_name cloudcast \
  --model openrouter:openai/o3 \
  --num_runs 1 \
  --max_agents 1 \
  --agent_timeout 5 \
  --results_dir cloudcast_o3_openrouter_smoke
```

Suggested paper-like reproduction target:

```bash
python examples/handoff_example_usage.py \
  --problem_name cloudcast \
  --model openrouter:openai/o3 \
  --num_runs 10 \
  --max_agents 5 \
  --agent_timeout 30 \
  --results_dir cloudcast_o3_direction_repro
```

The paper budgets by evaluation calls rather than only wall time, so
the reproduction harness should also cap or record total
`run_simulation` calls per run and compare against the 100-evaluation
budget.

## Codex CLI Baseline Target

Add a separate no-OKG baseline named `codex_cli_gpt55_high`. This is
not an Engram reproduction arm. It measures how a strong general coding
agent performs when given the same fair Cloudcast task and allowed
files.

This is apples-to-apples with Engram only when Engram is run under the
same model/reasoning-effort class, workspace visibility, and
evaluation-call budget. If the Engram reproduction arm uses `o3` while
Codex uses `gpt-5.5`, label Codex as a strong external baseline.

The baseline we actually want first is a fair out-of-box Codex run:
normal Codex CLI shell/edit/search behavior, but in a clean benchmark
workspace with no oracle files, no OKG context, a fixed budget, and
external scoring.

Suggested runner command:

```bash
.venv/bin/python deployments/memex-sr/scripts/run_cloudcast_codex_baseline.py \
  --max-evals 2 \
  --codex-timeout-seconds 900
```

The harness should isolate the workspace, exclude OKG context and
oracle files, provide `task.md`, `initial_program.py`, candidate output
instructions, and an `evaluate_candidate` command with a configured call
cap, archive the JSONL event log and final message, extract the
candidate implementation, and score it with the same Cloudcast
evaluator used by the Engram arms. The report should keep this as a
separate `fair_out_of_box_baseline` family rather than merging it with
Engram control.

## Consistency Review

This plan is now tracked formally by the Engram OpenSpec change:

```text
openspec/changes/add-cloudcast-okg-benchmark-slice/
```

Engram OpenSpec owns the benchmark harness, OpenRouter runner path,
context-packet contract, Memex-SR deployment sources, and run
harvesting. The OKG submodule's OpenSpec workspace owns only substrate
changes, such as new reusable source-runner behavior, catalog behavior,
MCP server features, or shared ontology modules.

Known inconsistency to resolve before claiming reproduction:

- The Engram paper reports Cloudcast human SOTA around `$626` and an
  Engram best single run around `$625`.
- The local `task_prompt_direction.txt`/`config_direction.yaml` text
  mentions an expert target around `$419`.

Until we reconcile the evaluator/config difference, use the paper
numbers as published reproduction references and treat the `$419` value
as an unresolved local-prompt target, not as a verified fair benchmark
threshold.

## Literature Scope

Cloudcast sits at the intersection of several literatures. The OKG
should model all of them because an agent may need to borrow a trick
from outside the exact Cloudcast paper lineage.

### Tier 0: Benchmark And Ground Truth

These are mandatory.

- Cloudcast: High-Throughput, Cost-Aware Overlay Multicast in the Cloud
  (NSDI 2024).
- Cloudcast code, if available through the Skyplane project or another
  open artifact.
- The Engram Cloudcast benchmark prompt, evaluator, simulator,
  profiles, and baseline/oracle separation.
- Engram paper sections and appendix snippets that discuss Cloudcast
  reproduction, prompt sensitivity, and generated solution families.

Evidence to extract:

- exact objective and constraints;
- why per-GB cloud egress pricing breaks bandwidth-only formulations;
- why the full MILP is intractable;
- which approximations Cloudcast used: node clustering, hop
  constraining, and stripe-iterative solving;
- measured approximation quality and solver speedup;
- failure modes of direct, shortest-path, and Steiner-only approaches.

### Tier 1: Direct Predecessors And Comparators

These papers and systems are directly named by Cloudcast or are close
predecessors.

- Skyplane: cloud-aware overlays for unicast cost/throughput
  optimization.
- CloudMPCast: cost-aware multi-datacenter bulk transfers from the
  customer side.
- SPANStore: multi-cloud geo-distributed storage and egress-aware relay
  placement.
- Jetway: cost minimization for inter-datacenter video traffic.
- Cascara and Entact: cost-aware traffic engineering for cloud/provider
  settings.
- RON and other resilient overlay routing work.
- Overlay multicast systems: End System Multicast, ALMI, Overcast,
  SplitStream, Bullet, and SPIDER.
- Peer-to-peer distribution systems: BitTorrent, Kraken, Dragonfly.
- Inter-datacenter multicast/bulk transfer systems: NetStitcher,
  CodedBulk, BDS, deadline-aware inter-DC multicast, and related bulk
  transfer schedulers.
- Geo-distributed storage services and systems: AWS S3 cross-region
  replication, S3 multi-region access points, GCP multi-region buckets,
  and Owl-like hot-content distribution systems.

Evidence to extract:

- objective function;
- topology model;
- whether multicast is supported;
- whether cloud pricing is modeled;
- whether striping or multiple trees are supported;
- whether elastic resources are modeled;
- why each technique does or does not transfer to Cloudcast.

### Tier 2: Algorithmic Foundations

These are needed so an agent can reason beyond named systems papers.

Network design and trees:

- minimum spanning tree, arborescence, Edmonds' optimum branching;
- directed and undirected Steiner tree;
- Steiner tree with delays, hop constraints, QoS, and cost-distance
  objectives;
- group Steiner tree, prize-collecting Steiner tree, buy-at-bulk
  network design, facility-location network design;
- approximation algorithms for network design and primal-dual methods.

Flow and optimization:

- max flow, min-cost flow, min-cost max-flow;
- multi-commodity flow and integral multi-commodity flow;
- path-based and edge-based flow formulations;
- unsplittable flow, splittable flow, and striping as a discrete
  approximation to splitting;
- flow conservation tricks using sink augmentation;
- capacity-constrained network design;
- Lagrangian relaxation, Benders decomposition, column generation,
  branch-and-cut, cutting planes, LP relaxation, rounding, and
  warm-starts.

Solver engineering:

- MILP modeling patterns for binary edge variables and integer resource
  counts;
- big-M constraints and how to avoid weak relaxations;
- candidate-edge pruning;
- hop limits and layered graphs;
- path enumeration versus edge selection;
- optimality gaps and time limits;
- solver portfolios and fallback heuristics;
- CBC, Gurobi, CVXPY, PuLP, OR-Tools, and SciPy optimization mechanics.

Evidence to extract:

- formulation templates;
- complexity and intractability reasons;
- practical approximations;
- implementation guidance an agent can use in Python under a few
  minutes.

### Tier 3: Data Structures And Implementation Patterns

These are not "literature" in the paper-only sense, but they are
critical context for an autonomous coding agent.

Graph primitives:

- adjacency maps and sparse edge lists;
- Dijkstra and Bellman-Ford;
- Yen and Eppstein k-shortest paths;
- all-pairs shortest-path caching;
- min-cost max-flow residual networks;
- priority queues and indexed heaps;
- union-find for MST/Kruskal baselines;
- Edmonds branching implementations;
- bitmask dynamic programming for small terminal sets;
- memoized path and provider-subgraph caches;
- sparse matrices for candidate formulation construction.

Search-space control:

- top-k gateway selection;
- per-provider candidate clustering;
- cheap cross-provider edge filters;
- hop-constrained path enumeration;
- partition/stripe grouping;
- scenario classification into intra-provider and inter-provider cases;
- portfolio selection among direct, hub, tree, and MILP candidates.

Testing patterns:

- path validity checks;
- edge-attribute preservation checks;
- capacity accounting per provider and per VM;
- unit conversion checks between GB, Gb, seconds, and Gbps;
- objective decomposition into egress cost and instance cost;
- benchmark fixtures that isolate single-provider, cross-provider, and
  high-fanout cases.

Evidence to extract:

- concrete code idioms;
- known pitfalls;
- runtime trade-offs;
- sanity checks for simulation output.

### Tier 4: Cloud Economics And Measurement

The agent needs enough operational context to understand why the
objective looks strange.

- AWS, GCP, and Azure egress pricing pages.
- Cloud provider VM pricing and network limits.
- Cloud bandwidth profiling practices, especially iperf-style
  measurements.
- Work on bandwidth stability, regional variability, and source
  bottlenecks.
- Cost-allocation and egress-cost engineering posts from cloud
  providers and large users.

Evidence to extract:

- pricing axes: intra-region, inter-region, inter-cloud, internet
  egress;
- why per-GB pricing makes cost proportional to transferred data volume;
- why VM startup cost matters only above/below certain transfer sizes;
- what changes over time and therefore should be periodically refreshed.

### Tier 5: Stretch Connections

These are lower priority but could produce useful analogies.

- CDN request routing and content placement.
- multicast in SDN and datacenter fabrics.
- content distribution and package/container image distribution.
- distributed backup, disaster recovery, and geo-replication.
- stream scheduling with deadlines.
- vehicle-routing and facility-location analogies.
- approximation algorithms for survivable network design.
- reinforcement learning or bandit methods for routing only as a
  contrast class; they are likely too sample-hungry for the benchmark
  but may supply features or portfolio-selection ideas.

## First Seed Manifest

Start with these named seeds, then expand by citation and keyword.

Mandatory seeds:

- Cloudcast.
- Skyplane.
- CloudMPCast.
- SPANStore.
- Jetway.
- Cascara.
- Entact.
- RON.
- End System Multicast.
- ALMI.
- Overcast.
- SplitStream.
- Bullet.
- SPIDER.
- BitTorrent.
- Kraken.
- Dragonfly.
- NetStitcher.
- CodedBulk.
- BDS.
- Deadline-aware inter-datacenter multicast.
- Cost-efficient multicast with deadline guarantees across edge
  datacenters.
- Steiner Tree Problems (Hwang and Richards).
- A modern approximation algorithms/network-design survey.
- A multi-commodity network flow survey.
- One practical MILP modeling reference for network design.

Expansion queries:

- `"cost-aware" "cloud" "multicast" egress`
- `"bulk transfer" inter-datacenter multicast deadline`
- `"overlay multicast" high bandwidth file distribution`
- `"cloud-aware overlays" transfer cost throughput`
- `"directed Steiner tree" multicast routing approximation`
- `"multi-commodity flow" network design MILP`
- `"hop constrained" Steiner tree multicast`
- `"path based formulation" multicast network design`
- `"Benders decomposition" network design multicast`
- `"column generation" network design multicast`

Venue filters:

- NSDI, SIGCOMM, CoNEXT, HotNets, OSDI, SOSP, EuroSys, USENIX ATC,
  SoCC.
- INFOCOM, ICNP, ICDCS, IEEE/ACM Transactions on Networking, TON,
  TCC, TPDS for direct networking/cloud systems comparators.
- SODA, STOC, FOCS, IPCO, Integer Programming and Combinatorial
  Optimization, Mathematical Programming, Operations Research for
  algorithmic foundations.

## OKG Extraction Targets

For every paper/document in the Cloudcast slice, extract:

- `problem_class`: overlay multicast, inter-DC transfer, cloud
  economics, network design, flow optimization, tree approximation,
  solver engineering, graph implementation.
- `objective`: cost, throughput, latency, deadline, reliability,
  fairness, resource cost, or mixed.
- `constraints`: bandwidth, ingress, egress, VM count, hop count,
  deadline, path length, availability, region/provider.
- `decision_variables`: edges, paths, relay/waypoint nodes, stripe
  assignment, bandwidth, VM count, tree membership.
- `mechanism`: MILP, LP relaxation, Steiner tree, min-cost flow,
  multi-commodity flow, path enumeration, clustering, hop pruning,
  stripe iteration, gateway selection.
- `failure_modes`: ignores pricing, ignores throughput, ignores data
  identity, ignores elastic resources, fails to scale, violates
  capacity, high startup overhead, poor cross-provider handling.
- `implementation_notes`: data structures, solver options, candidate
  pruning, time limits, fallback strategies.
- `transfer_to_cloudcast`: direct, partial, contrast-only, or stretch.

## Context Packet Shape

The Cloudcast packet should not be a literature survey. It should be a
compact design guide:

1. Problem framing: constrained cost-aware multicast over directed
   cloud-region graph.
2. Why direct/shortest-path/Steiner-only baselines fail.
3. Optimization families to try: MILP, reduced MILP, path-based ILP,
   min-cost flow relaxations, DP over candidate hubs, and portfolios.
4. Tractability knobs: candidate node pruning, provider clustering,
   hop limits, k-shortest paths, stripe-iterative solving, time limits,
   fallback heuristics.
5. Implementation checklist: unit conversions, capacity accounting,
   path validity, solver timeout behavior, scenario classification.
6. Evidence index with source/chunk ids.

## Acquisition Policy

- Prefer open access sources: USENIX, arXiv, project pages, RFC-style
  documents, official cloud docs, and open technical reports.
- Use DBLP/OpenAlex/Crossref/Semantic Scholar only for metadata and
  citation expansion unless an open full-text link is available.
- MIT-authenticated publisher material should become an operator asset:
  a human retrieves the file through approved channels and places it in
  a private local asset cache for hashing and parsing.
- Do not script publisher login, Touchstone, libproxy, or ebook portals.

## Immediate Next Work

1. Add a `cloudcast_literature.yaml` manifest with the Tier 0/Tier 1
   seed list and access-basis fields.
2. Add a benchmark artifact source for the Cloudcast local files.
3. Patch Engram model routing so OpenRouter model slugs do not break
   result paths and can be passed to LangChain cleanly.
4. Add the `codex_cli_gpt55_high` runner wrapper and fixture evaluator
   handoff.
5. Run a one-agent five-minute OpenRouter `openai/o3` smoke test.
6. Run one Codex CLI baseline smoke test with no OKG context.
7. Generate the first hand-reviewed context packet from the Cloudcast
   paper plus 5-10 direct predecessor papers.
8. Expand to the 20-50 source literature slice once the packet shape is
   useful.
