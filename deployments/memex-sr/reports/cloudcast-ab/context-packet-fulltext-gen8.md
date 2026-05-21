# Research Context Packet

**Problem:** cloudcast
**Domain:** networking
**Topics:** multicast, routing, traffic-engineering, cost-aware-routing
**Generation:** 8

## Problem Class

Wide-area network capacity planning and load balancing — cloudcast targets the cost-tuned routing / multicast selection family (objective: minimize $/byte under throughput + jitter SLOs). Adjacent problem families: BGP route reflector design, anycast prefix steering, MPLS TE path computation.

## Design Principles

- Keep benchmark evidence separate from oracle artifacts.

  - Why it matters: Cloudcast contains oracle files that can invalidate comparisons. Agents should use fair prompts, evaluator behavior, and public systems knowledge rather than hidden optimal solutions.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- Model bottleneck capacity and provider limits before treating edge price as the only routing objective.

  - Why it matters: A cheaper edge can still be unusable or slow when throughput, ingress, egress, or VM-region limits become binding.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- Optimize the shared multicast structure before tuning individual source-to-destination paths.

  - Why it matters: Cloudcast cost is driven by the union of partition traffic through edges. Independent shortest paths miss sharing opportunities and can pay the same expensive egress repeatedly.

  - Evidence: generic_evidence:cloudcast:benchmark-objective, generic_evidence:cloudcast:evaluator-shared-edge-charge
- Separate topology selection from partition assignment when the full integer problem is too large.

  - Why it matters: Selecting a low-cost multicast tree and then deciding whether partitions should share or diversify paths is easier to reason about than solving all destination and partition choices at once.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result


## Mechanisms To Try

- Directed Steiner dynamic program over terminal subsets
  - Applicability: Useful when the destination set is small enough to enumerate terminal subsets and the objective favors a shared directed tree.

  - Known limits: Runtime grows exponentially in destination count and it does not by itself solve partition-level load spreading.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result
- Provider-limit-aware cost estimator
  - Applicability: Useful as an internal scoring function for candidate routes before spending official evaluator calls.

  - Known limits: Must match simulator semantics closely; a partial estimator can overfit edge price while missing bottleneck or VM-region effects.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- Equal-cost tree diversification for partitions
  - Applicability: Useful after a low-cost shared tree is found, especially when a small set of alternate edges can reduce bottleneck time without materially increasing egress cost.

  - Known limits: Blind diversification can add instance or edge costs and erase the savings from multicast sharing.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result
- Min-cost flow or MILP formulation
  - Applicability: Useful for explicitly representing edge usage, capacity limits, egress price, and partition assignment when solve time is acceptable.

  - Known limits: Full formulations can be slow or brittle under benchmark time budgets, so relaxations or decomposition may be needed.

  - Evidence: generic_evidence:cloudcast:benchmark-objective


## Trade-Off Map

- low egress price vs sufficient throughput and provider capacity
  - Tension: Cheapest edges are not always best when they create bottlenecks or violate provider ingress and egress limits.

  - Failure modes: Cost-only routing can look cheap in a static path search but fail or score poorly once throughput and VM capacity are evaluated.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- shared multicast tree reuse vs path diversity for bottleneck relief
  - Tension: Reusing one tree minimizes egress cost, but sending all partitions through the same bottleneck can increase completion time.

  - Failure modes: Too little diversity leaves transfer time high; too much diversity increases edge and instance costs enough to lose the main benefit.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result
- exact optimization quality vs benchmark solve time
  - Tension: Exact DP or MILP can find better structures, but high solve time reduces robustness under the benchmark's agent loop.

  - Failure modes: A solver-heavy approach may time out, burn evaluation budget, or become too complex to repair after one failed run.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result


## Experiment Advice

- Metrics to inspect: per-flow $/byte, p99 latency, jitter, link utilization variance.
- Stress cases to add: bursty traffic (Pareto-distributed flow sizes); link failures mid-run; asymmetric capacity.
- Ablations to run: hold the topology fixed and vary the objective weighting (latency vs cost); hold the objective fixed and vary the multicast tree algorithm.

## Anti-Patterns

- Optimize only per-edge price without modeling throughput, bottleneck time, provider ingress, or provider egress.

  - Why it tends to fail: The evaluator combines cost and transfer-time behavior; invalid or slow routes lose even when the nominal edge price is low.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- Route each destination independently with shortest path or cheapest path.

  - Why it tends to fail: It ignores multicast sharing, so the same source egress or relay opportunity can be paid repeatedly across destinations.

  - Evidence: generic_evidence:cloudcast:evaluator-shared-edge-charge
- Use optimal.py or task_prompt_direction_with_optimal.txt as context for a fair benchmark comparison.

  - Why it tends to fail: It leaks the holdout solution and makes any reported improvement uninterpretable.

  - Evidence: generic_evidence:cloudcast:benchmark-objective
- Diversify partitions across alternate paths without a cost and capacity estimator.

  - Why it tends to fail: Added path diversity can increase edge and instance cost more than it reduces transfer time.

  - Evidence: generic_evidence:cloudcast:shared-tree-smoke-result


## Evidence Index

- generic_evidence:cloudcast:benchmark-objective: benchmark_contract — Cloudcast asks the agent to minimize total transfer cost while respecting throughput constraints and provider ingress/egress limits across a directed multi-cloud graph.

- generic_evidence:cloudcast:context-packet-gap: graph_gap — The first generated Cloudcast context packet had zero design principle, mechanism, trade-off, anti-pattern, and evidence rows.

- generic_evidence:cloudcast:evaluator-shared-edge-charge: evaluator_semantics — The evaluator rewards multicast sharing because shared edges are charged by partition traffic through the edge, not independently for every destination that uses the same edge.

- generic_evidence:cloudcast:shared-tree-smoke-result: benchmark_result — A directed-Steiner-style shared-tree candidate scored 0.001601037995 with inferred total cost 623.594796 and 5/5 successful configs in the Codex+OKG-MCP smoke run.

- generic_evidence:cloudcast:baseline-smoke-result: benchmark_result — The no-OKG Codex smoke baseline scored 0.001602764006 with inferred total cost 622.922172 and 5/5 successful configs.
