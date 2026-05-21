## Context

The current Cloudcast OKG treatment used generation `7` of Memex-SR. It
had a healthy deployment surface but only a small Cloudcast-specific
knowledge slice:

- `4` design principles;
- `4` mechanisms;
- `3` trade-offs;
- `4` anti-patterns;
- `5` generic evidence nodes.

The Codex+OKG run made three successful MCP calls and retrieved relevant
but shallow guidance. That guidance overlapped heavily with the
benchmark prompt itself: optimize shared multicast structure, avoid
edge-price-only objectives, and consider MILP/min-cost-flow families.
For a strong general coding agent, this is not enough signal.

The next milestone should test whether Memex-SR can act like a compact
systems-research textbook: it should supply distilled principles,
algorithm families, failure modes, tractability knobs, implementation
checks, and experimental lessons with provenance.

## Goals / Non-Goals

**Goals:**

- Make the Cloudcast graph evidence dense enough to change agent
  behavior.
- Prefer source-backed facts over operator intuition.
- Deliver the first serious OKG treatment as a pinned context-first
  brief, then test live MCP as a separate treatment.
- Make "OKG was used" auditable through evidence ids, cited node ids,
  and usage timing relative to edits/evaluations.
- Feed successful and failed Cloudcast experiments back into the graph.
- Keep every benchmark arm fair by excluding oracle and holdout
  artifacts.

**Non-Goals:**

- Do not claim OKG improves Cloudcast until the context-first A/B has
  enough samples and usage-compliance evidence.
- Do not download the entire systems literature in this change.
- Do not rely on raw SQL, broad graph dumps, or unpublished local facts
  in agent-facing contexts.
- Do not modify OKG substrate behavior from Engram.
- Do not expose the generated context-packet MCP tool in the live Codex
  MCP arm until the context-first treatment is separately evaluated.

## Decisions

1. **Treat the prior MCP run as a diagnostic, not a benchmark result.**

   The previous arm established that the server starts and bounded tools
   are callable. It did not establish useful graph assistance because
   the agent performed only minimal retrieval and did not cite graph
   evidence in a research plan.

2. **Context-first before live-tool-first.**

   The next A/B should append a generated Cloudcast research brief to
   the task prompt. This removes tool-use variance and tests the core
   claim: does distilled graph knowledge help the agent? Live MCP
   remains a later treatment with a structured protocol.

3. **Separate literature coverage from distilled guidance.**

   The deployment should store acquired papers/docs as source documents
   and chunks, but the agent-facing payload should be a concise
   distillation. The graph needs both layers:

   - document chunks for provenance and re-extraction;
   - typed facts for direct agent use.

4. **Use tiers and extraction targets.**

   Every corpus seed should declare a tier and extraction targets:
   objective, constraints, variables, algorithm family, decomposition
   strategy, data structures, implementation checks, failure modes, and
   transfer-to-Cloudcast relevance. This makes review and context
   generation deterministic.

5. **Make graph usage a measurable benchmark output.**

   Reports should include whether an OKG-assisted run:

   - retrieved Cloudcast-specific typed facts;
   - expanded from facts to evidence;
   - cited node ids in a written plan;
   - used evidence before editing `candidate.py`;
   - used evidence before the first evaluator call.

   A run with an MCP server attached but no evidence-backed plan should
   be marked as `okg_attached_but_underused`.

6. **Harvest every run.**

   The graph should remember candidate algorithm families, scores,
   costs, transfer-time bottlenecks, invalid-route failures, and agent
   notes. This converts benchmark attempts into evidence for later
   agents.

## Corpus Shape

The first actionable corpus should be small enough to inspect but broad
enough to teach the benchmark:

- Direct systems comparators: Cloudcast, Skyplane, CloudMPCast,
  SPANStore, Jetway, Cascara, Entact, RON, End System Multicast, ALMI,
  Overcast, SplitStream, Bullet, SPIDER, BitTorrent, Kraken,
  Dragonfly, NetStitcher, CodedBulk, BDS.
- Algorithmic foundations: directed Steiner tree, multicast network
  design, min-cost flow, multi-commodity flow, LP relaxation and
  rounding, Benders decomposition, column generation, path-based
  formulations, approximation algorithms for network design.
- Implementation guidance: priority queues, k-shortest paths,
  all-pairs shortest-path precomputation, subset dynamic programming,
  sparse graph pruning, solver time limits, candidate scoring, and
  simulator-compatible validation.
- Cloud economics and measurement: cloud egress pricing,
  inter-region bandwidth, provider ingress/egress constraints, and WAN
  traffic engineering.

The first target is not "all papers"; it is a reviewed 20-50 source
slice with enough facts to create a useful brief.

## Agent Delivery Modes

### Context-First

The agent receives a generated markdown brief with:

- graph generation id and packet hash;
- problem framing;
- algorithm families to consider;
- tractability knobs;
- implementation/data-structure guidance;
- known anti-patterns;
- evidence index with node ids and source ids;
- holdout/oracle exclusion statement.

### Structured MCP

The agent receives bounded tools, but the task protocol requires:

1. Inspect graph summary.
2. Search at least three targeted topics.
3. Expand at least three typed facts to related evidence.
4. Write a short evidence-backed plan citing node ids.
5. Only then edit code or evaluate.

The harness should classify compliance automatically from Codex JSONL
events and the final plan/candidate artifacts where possible.

## Risks / Trade-offs

- Too much context can drown out the benchmark prompt. Mitigation:
  token-budgeted context sections and evidence budgets.
- Source acquisition can become a separate project. Mitigation: start
  with open/operator-supplied files and a reviewed seed manifest.
- Agent compliance checks can become brittle. Mitigation: measure
  simple event facts first: call counts, timing, node ids in text, and
  evaluator-call order.
- Distilled facts can encode operator bias. Mitigation: each fact
  carries source ids, extraction method, confidence, and review state.
- Benchmark overfitting is easy. Mitigation: continue excluding oracle
  files and avoid public-config-specific route incumbents in
  graph-provided guidance.

## Rollout

1. Write the source manifest and acquisition policy.
2. Add fixture/full-text sources and publish a generation with document
   chunks.
3. Add typed fact extraction/distillation and publish a generation with
   non-zero typed facts from source-backed evidence.
4. Generate a context-first brief and run a small A/B.
5. Add structured MCP usage protocol and run a separate MCP arm.
6. Harvest all runs back into OKG and verify no-op incrementality.
7. Update reports to compare score and OKG usage depth.

## Open Questions

- Which 20-50 sources are mandatory for the first reviewed corpus?
- Should the first distillation pass be manual, LLM-assisted with human
  review, or fully automated with confidence labels?
- Should context-first be tested with Codex first, Engram first, or both?
- What minimum usage-compliance threshold should mark a run as a valid
  OKG-assisted treatment?
- Should public Cloudcast benchmark configurations be considered
  trainable context, or should graph guidance avoid any
  configuration-specific route structures?
