## 1. Diagnose Current Failure Mode

- [x] 1.1 Capture the prior Codex+OKG run as an underuse diagnostic.
  Verification: a report records generation id, MCP call count, tool
  names, retrieved node ids, timing relative to first edit/evaluation,
  and classifies the run as `okg_attached_but_underused`.
- [x] 1.2 Add a graph coverage snapshot for the current Cloudcast slice.
  Verification: a pinned-generation query reports counts for
  `document`, `document_chunk`, `paper`, `design_principle`,
  `mechanism`, `trade_off`, `anti_pattern`, and `generic_evidence`
  filtered to Cloudcast/topic slugs.

## 2. Build Reviewed Cloudcast Source Corpus

- [x] 2.1 Create a reviewed Cloudcast source manifest with tiers,
  access basis, source urls/local paths, transfer-to-Cloudcast labels,
  holdout status, and extraction targets. Verification: the manifest
  includes at least 20 non-holdout sources across direct systems,
  algorithms, implementation guidance, and cloud economics.
- [x] 2.2 Add a local acquisition/cache workflow for open and
  operator-supplied sources. Verification: a dry run lists target files,
  cache paths, access basis, and rate-limit policy without downloading
  or touching holdout artifacts.
- [x] 2.3 Parse and chunk the first reviewed source slice through
  Memex-SR publication. Verification: a published OKG generation adds
  non-zero `document` and `document_chunk` nodes for the source slice,
  and `okg doctor` reports no RED findings.
- [x] 2.4 Verify acquisition incrementality. Verification: rerunning the
  source import with no changed source files publishes no new live facts
  or reports a no-op source run.

## 3. Distill Actionable Cloudcast Facts

- [ ] 3.1 Define the Cloudcast fact schema/profile fields needed for
  actionable guidance: algorithm family, objective, constraints,
  decision variables, tractability knobs, data structures,
  implementation checks, failure modes, provenance, confidence, and
  review state. Verification: fixture facts validate before publish.
- [ ] 3.2 Extract or curate typed facts from the reviewed source slice.
  Verification: a published generation contains at least 15
  `mechanism`, 10 `design_principle`, 10 `trade_off`, 10
  `anti_pattern`, and 20 `generic_evidence` Cloudcast-relevant nodes,
  each with evidence ids that resolve to source-backed nodes.
- [ ] 3.3 Verify graph links are useful. Verification: representative
  mechanisms link to principles with `instantiates`, trade-offs link to
  mechanisms with `restricts`, anti-patterns link to mitigations with
  `mitigated_by`, and traversal from each sampled fact reaches at least
  one source evidence node.
- [ ] 3.4 Verify fact incrementality. Verification: rerunning the fact
  source without changes appends zero new live facts for the Cloudcast
  fact scope.

## 4. Ship Context-First Treatment

- [ ] 4.1 Generate a Cloudcast research brief from a pinned generation.
  Verification: the brief includes generation id, packet hash, source
  hashes, evidence ids, and sections for problem framing, mechanisms,
  trade-offs, anti-patterns, implementation checks, and evidence index.
- [ ] 4.2 Add a context-first benchmark arm. Verification: the arm
  appends the generated brief to the fair Cloudcast prompt, records the
  brief path/hash/generation id in metadata, and excludes live OKG tools
  and holdout artifacts.
- [ ] 4.3 Run a small context-first smoke A/B. Verification: no-OKG and
  context-first arms produce result directories, normalized metrics,
  prompt/context hashes, evaluator hashes, and contamination audit
  entries.

## 5. Add Structured MCP Treatment

- [ ] 5.1 Update the MCP prompt protocol to require evidence gathering
  before code edits. Verification: generated task text requires graph
  inspect, at least three targeted searches, at least three expansions
  or equivalent evidence lookups, and a short plan citing node ids
  before editing or evaluating.
- [ ] 5.2 Add usage-compliance parsing for Codex JSONL events.
  Verification: the parser reports call counts by tool, first OKG call
  time, first edit time, first evaluation time, retrieved node ids, and
  whether node ids appear in the plan/final message.
- [ ] 5.3 Run a structured MCP smoke test. Verification: report records
  whether the run satisfied usage protocol, plus score/cost/eval calls
  and comparison to no-OKG and context-first arms.

## 6. Harvest Runs Back Into OKG

- [ ] 6.1 Add or configure a Cloudcast run harvester for Codex/Engram
  result directories. Verification: a published generation contains run,
  attempt, candidate implementation, metric observation, research note,
  and failure/success diagnosis facts for at least one completed run.
- [ ] 6.2 Link harvested runs to OKG evidence. Verification: a run that
  used a context brief or MCP facts links to the context/evidence ids
  used during that run.
- [ ] 6.3 Verify harvester incrementality. Verification: a no-op rerun
  over the same result directory appends zero new live facts for that
  run scope.

## 7. Reporting And Handoff

- [ ] 7.1 Extend Cloudcast reports with OKG usefulness metrics.
  Verification: reports include graph coverage counts, context metadata,
  usage protocol status, evidence ids retrieved/cited, score, inferred
  cost, evaluation calls, and contamination audit.
- [ ] 7.2 Document the workflow for collaborators. Verification:
  Memex-SR docs explain how to add sources, publish facts, generate a
  context-first brief, run A/B arms, inspect usage compliance, and
  harvest run outputs.
- [x] 7.3 Validate the OpenSpec change. Verification:
  `openspec validate make-cloudcast-okg-actionable --strict` passes.
