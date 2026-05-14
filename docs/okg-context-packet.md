# OKG Context Packet Draft

This packet is the first contract between Engram agents and the OKG
memex-sr deployment. It is intentionally a file contract
first: Engram can prepend or attach this text to an agent run without
depending on a live OKG server.

## Packet Inputs

- `problem_name`: Engram problem id, such as `cloudcast`, `vidur`, or
  `llm_sql`.
- `domain`: networking, ML systems, databases, distributed systems, or
  another configured domain.
- `topic_slugs`: OKG topics/concepts to retrieve.
- `generation_id`: pinned OKG generation used to produce the packet.
- `evidence_budget`: maximum evidence chunks or claims to include.
- `token_budget`: maximum output size.

## Packet Output

```markdown
# Research Context Packet

## Problem Class
[1-2 paragraphs mapping the Engram task to known systems problem
families.]

## Design Principles
- [Principle statement]
  - Why it matters:
  - Evidence: [paper/document/chunk ids]

## Mechanisms To Try
- [Algorithmic mechanism or design pattern]
  - Applicability:
  - Known limits:
  - Evidence:

## Trade-Off Map
- [Objective A] vs [Objective B]
  - Tension:
  - Failure modes:
  - Evidence:

## Experiment Advice
- Metrics to inspect:
- Stress cases to add:
- Ablations to run:

## Anti-Patterns
- [Approach]
  - Why it tends to fail:
  - Evidence:

## Evidence Index
- [id]: [title/source/short locator]
```

## Initial OKG Questions

These are good smoke-test questions for the memex-sr graph:

- For congestion control, what are the major design families and what
  trade-offs do they make between throughput, latency, fairness, and
  stability?
- For resource placement problems, what objective functions and
  constraint relaxations recur across systems papers?
- For request routing in ML serving, what mechanisms balance queueing
  delay, locality, load, and tail latency?
- For cache reuse and query workloads, what assumptions make a reuse
  strategy work or fail?
- Which papers introduce mechanisms that resemble Engram's current
  benchmark task?
- Which extracted claims have direct support from full-text chunks, and
  which are still inference-only?

## Engram Agent Instructions

Agents receiving a context packet should:

- Treat packet claims as hypotheses to test, not as ground truth.
- Preserve evidence ids in their reasoning when a principle influences a
  design choice.
- Translate principles into concrete implementation changes and evaluate
  them with `run_simulation`.
- When a packet suggests a trade-off, design an experiment that can
  distinguish the sides of the trade-off.
- Add negative results to the handoff summary so later agents do not
  rediscover the same dead end.

## Harvest Back Into OKG

After a run, the harvester should be able to turn Engram artifacts into
graph evidence:

- `research_journal.md` -> run-level digest document.
- `knowledgebase/agent_N/experiments/exp_*/score.txt` -> experiment
  result facts.
- `snapshot.py` or `snapshot.cpp` -> candidate solution artifact.
- final result JSON -> best solution, score, total simulations, total
  agents, convergence reason.
- agent summaries -> empirical claims, failed approaches, and
  recommended next steps.

Each harvested record should carry the Engram run id, problem name,
agent number, experiment id, artifact path, content hash, and source
generation id when it was produced from an OKG context packet.
