## 1. OpenSpec And Plan Cleanup

- [ ] 1.1 Review the Cloudcast planning docs against this OpenSpec
  change and remove inconsistencies between proposal, literature plan,
  tasks, and README. Verification: `openspec validate
  add-cloudcast-okg-benchmark-slice --strict` passes and README links
  the formal OpenSpec change.
- [ ] 1.2 Decide whether any required behavior belongs in
  `external/okg/openspec` instead of Engram. Verification: substrate
  changes are either explicitly out of scope or tracked by a separate
  OKG change id.

## 2. Benchmark Controls

- [ ] 2.1 Create a Cloudcast benchmark-control manifest with fair input
  hashes and holdout/oracle exclusions. Verification: manifest includes
  prompt, evaluator, simulator, profile, initial-program hashes, and
  marks `optimal.py` plus `task_prompt_direction_with_optimal.txt`
  holdout-only.
- [ ] 2.2 Reconcile the `$419` local prompt target with the Engram
  paper's `$626` human-SOTA reference. Verification: a report note
  identifies the evaluator/config source of the discrepancy or blocks
  target comparisons until resolved.
- [ ] 2.3 Add normalized Cloudcast metric parsing. Verification: a
  fixture score file parses into best score, inferred total cost,
  success flag, simulations, and threshold crossings.

## 3. OpenRouter Reproduction

- [ ] 3.1 Add provider/model normalization for OpenRouter model slugs.
  Verification: `openrouter:openai/o3` routes to OpenRouter and uses a
  filesystem-safe run label.
- [ ] 3.2 Add run metadata for provider, model slug, API base URL class,
  and budget. Verification: each result directory contains
  machine-readable metadata without storing API keys.
- [ ] 3.3 Run a one-agent Cloudcast OpenRouter smoke test. Verification:
  the run completes or fails with archived logs, and the result metadata
  records `openai/o3` through OpenRouter.

## 4. Cloudcast Corpus And Context

- [ ] 4.1 Add `cloudcast_literature.yaml` with tiered seed sources.
  Verification: manifest covers Tier 0 through Tier 4 and includes
  access basis plus `transfer_to_cloudcast` labels.
- [ ] 4.2 Add a Cloudcast benchmark artifact source for local benchmark
  files. Verification: a Memex-SR publish creates benchmark/artifact
  rows in a published OKG generation.
- [ ] 4.3 Add first-pass Cloudcast evidence extraction fields.
  Verification: graph records expose objective, constraints, decision
  variables, mechanism, failure modes, and implementation notes for a
  fixture source.
- [ ] 4.4 Generate a first Cloudcast context packet from a pinned OKG
  generation. Verification: packet includes generation id, packet hash,
  evidence ids, source hashes, and no holdout artifacts.
- [x] 4.5 Add a first-pass Cloudcast systems-research fact source.
  Verification: a Memex-SR publish creates non-zero
  `design_principle`, `mechanism`, `trade_off`, `anti_pattern`, and
  `generic_evidence` nodes with Cloudcast topic slugs in a published
  generation, and the facts exclude oracle artifacts.

## 5. Engram Integration

- [ ] 5.1 Add `--okg_context_file` to the Cloudcast handoff example.
  Verification: no-flag prompt content is unchanged; flag-enabled runs
  append the packet and save packet metadata.
- [ ] 5.2 Keep live OKG lookup tools out of the first A/B arm.
  Verification: the context-only arm can run with no live MCP server
  after packet generation.
- [ ] 5.3 Add optional bounded OKG tools as a later treatment. Verification:
  each tool response includes pinned generation id, result limits, and
  evidence provenance, with raw SQL unavailable.

## 6. Harvest And Report

- [ ] 6.1 Implement a Cloudcast run harvester. Verification: a fixture
  run publishes research-run, agent-attempt, experiment,
  candidate-implementation, metric-observation, failure-diagnosis,
  research-note, and workspace-artifact facts or approved equivalents.
- [ ] 6.2 Verify harvest incrementality. Verification: a no-op rerun of
  the harvester appends zero new live facts in the next published OKG
  generation.
- [ ] 6.3 Run a control-vs-context smoke A/B. Verification: both arms
  produce result directories and the OKG arm records packet metadata.
- [ ] 6.4 Produce the pilot A/B report. Verification: report includes
  graph counts, commands, per-run metrics, aggregate metrics, source
  coverage, and oracle-contamination audit.

## 7. Codex CLI Baseline

- [x] 7.1 Add a Codex baseline runner wrapper around `codex exec`.
  Verification: the wrapper invokes `codex exec -m gpt-5.5 -c
  'model_reasoning_effort="high"'`, uses an isolated workspace or
  worktree, and writes JSONL events plus `codex_last_message.md` into
  the result directory.
- [x] 7.2 Add a benchmark-clean out-of-box Codex workspace and evaluator
  wrapper. Verification: the workspace contains `task.md`,
  `initial_program.py`, candidate output instructions, and an
  `evaluate_candidate` command; Codex can use normal CLI shell/edit/search
  affordances; oracle and holdout files are absent; the wrapper enforces
  the configured evaluation-call cap and records every attempt.
- [x] 7.3 Add candidate extraction and evaluator handoff for Codex
  output. Verification: a fixture Codex-produced candidate is scored by
  the same Cloudcast evaluator and normalized metric parser used by the
  Engram arms.
- [x] 7.4 Run a no-OKG Codex baseline smoke test. Verification: result
  metadata records Codex CLI version, model, reasoning effort, prompt
  hash, evaluator hash, allowed-file manifest hash, elapsed time, and
  no oracle or OKG context artifacts.
- [x] 7.5 Add Codex baseline rows to the report parser. Verification:
  the Cloudcast report includes `codex_cli_gpt55_high` as a separate
  arm alongside Engram control and OKG-assisted Engram results, and
  labels the primary Codex arm as `fair_out_of_box_baseline` rather than
  as a strict Engram architecture ablation.
- [x] 7.6 Add and run a Codex+OKG-MCP treatment arm. Verification: the
  wrapper invokes the same Codex CLI model, reasoning effort, workspace,
  prompt, and evaluation cap as the no-OKG baseline while injecting the
  `okg-memex-sr` MCP server; metadata records OKG DSN, deployment,
  latest published generation, and no oracle/context-packet files in the
  workspace.
- [x] 7.7 Compare no-OKG Codex with Codex+OKG-MCP. Verification: the
  Cloudcast report includes both `codex_cli_gpt55_high` and
  `codex_cli_gpt55_high_okg_mcp`, with score, inferred cost, eval calls,
  elapsed time, model, result directories, and OKG generation for the
  MCP arm.
- [x] 7.8 Hide `generate_context_packet` from the live Codex MCP arm.
  Verification: prepare-only metadata shows `OKG_MCP_TOOL_SURFACE` set
  to `operator`, approved tools do not include `generate_context_packet`,
  and the generated task prompt instructs Codex to use bounded
  inspect/search-style graph tools instead.
