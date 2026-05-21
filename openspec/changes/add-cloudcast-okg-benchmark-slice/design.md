## Context

Cloudcast is the first concrete benchmark for testing whether Memex-SR
can help Engram act more like an autonomous systems researcher. The
benchmark is local, cheap, systems-native, and has known failure modes:
shortest-path and Steiner-only approaches can look attractive but miss
provider egress, capacity, striping, and tractability constraints.

Engram currently supports Cloudcast through
`examples/handoff_example_usage.py --problem_name cloudcast`. The fair
prompt is `task_prompt_direction.txt`; the `--give_files` path exposes
oracle artifacts and is not suitable for fair A/B tests.

Memex-SR currently has deployment planning docs and paper metadata, but
not a Cloudcast-specific graph slice, context packet generator, or
Engram workspace harvester. Engram did not previously have a top-level
OpenSpec workspace; that is now initialized so deployment work can be
reviewed separately from OKG substrate changes.

## Goals / Non-Goals

**Goals:**

- Make the Cloudcast work a formal Engram OpenSpec change.
- Reproduce the paper's Cloudcast setup as closely as practical through
  OpenRouter: `o3`, Direction prompt, 10 runs, and 100 evaluations per
  run.
- Build a Cloudcast OKG seed corpus covering direct systems papers,
  algorithmic foundations, data structures, implementation patterns,
  and cloud economics.
- Generate concise context packets from a pinned OKG generation.
- Keep benchmark fairness explicit by excluding oracle artifacts from
  context and tools.
- Add a plain Codex CLI baseline using `gpt-5.5` with high reasoning
  effort, so we can compare Engram and OKG-assisted Engram against a
  strong general coding agent.
- Harvest Engram run outputs into Memex-SR through normal source
  publication.

**Non-Goals:**

- Do not implement full-text acquisition for all systems literature in
  this change.
- Do not automate MIT-authenticated publisher downloads.
- Do not expose raw SQL or unbounded OKG scans to Engram agents.
- Do not modify OKG substrate behavior inside this Engram change.
- Do not claim reproduction success until the evaluator, prompt, model,
  and budget controls are reconciled with the paper.

## Decisions

1. **Use Engram OpenSpec for this change.**

   Engram owns the benchmark harness, Memex-SR deployment files, and
   OpenRouter runner path. OKG substrate changes remain in
   `external/okg/openspec`. This prevents deployment-specific benchmark
   work from being mixed into the generic OKG substrate roadmap.

2. **Split Cloudcast evidence into tiers.**

   The literature plan uses Tier 0 for benchmark/ground-truth material,
   Tier 1 for direct systems predecessors, Tier 2 for algorithmic
   foundations, Tier 3 for data structures and implementation patterns,
   Tier 4 for cloud economics and measurement, and Tier 5 for stretch
   analogies. This makes the corpus broad without making every source
   equally important to the first packet.

3. **Reproduce with OpenRouter model aliases, not raw slugs in paths.**

   OpenRouter exposes `openai/o3` and `openai/gpt-5.2`, but Engram
   currently expects model names that are also safe for result paths.
   The runner should accept an alias such as `openrouter:openai/o3`,
   route the API call to the OpenAI-compatible OpenRouter endpoint, and
   sanitize the result-path label.

4. **Budget by evaluation calls and wall time.**

   The paper reports 100 evaluation calls per run. Engram examples
   currently expose `max_agents` and `agent_timeout`, so reproduction
   should also record and, if needed, enforce a simulation-call cap.

5. **Treat the `$419` local prompt target as unresolved.**

   The local Cloudcast prompt mentions an expert solution around `$419`,
   while the Engram paper reports Cloudcast human SOTA around `$626`.
   The run report must reconcile evaluator/config differences before
   using either number as a target.

6. **Start context-first; defer live OKG tools.**

   The first A/B should append one context packet to the task prompt.
   Live OKG tools are useful later, but context-first mode is easier to
   reproduce and isolates whether graph-backed guidance changes search.

7. **Harvest through source publication.**

   Engram run artifacts should become Memex-SR graph facts through a
   source adapter and published OKG generation, not direct writes to
   live graph tables.

8. **Treat Codex CLI as a separate baseline family.**

   The Codex baseline should invoke `codex exec` non-interactively with
   `-m gpt-5.5` and `-c model_reasoning_effort="high"`. It is not an
   Engram run and must not be reported as one. The arm name should be
   `codex_cli_gpt55_high`.

   The primary goal is a fair out-of-box Codex comparison, not a
   perfectly matched Engram architecture ablation. It should answer:
   given the same clean Cloudcast task and no OKG help, what can Codex
   CLI do as a general coding agent?

   The baseline should receive the same fair Cloudcast problem prompt
   and initial program as the Engram control. It should run with normal
   Codex CLI behavior: shell access, file editing, search, and its usual
   planning loop inside an isolated benchmark workspace. It should not
   receive OKG context unless a later treatment explicitly adds
   `codex_cli_gpt55_high_okg_context`.

   The Codex workspace should be benchmark-clean: include `task.md`,
   `initial_program.py`, a candidate output location, and a documented
   `evaluate_candidate` command that calls the Cloudcast evaluator
   outside the workspace. Exclude `optimal.py`,
   `task_prompt_direction_with_optimal.txt`, OKG context packets, and
   any other oracle or holdout material. The evaluator wrapper should
   enforce a configured evaluation-call cap and archive every call.

   The harness should run Codex in an isolated temporary workspace or
   worktree, capture JSONL events, capture the final message with
   `--output-last-message`, extract the candidate implementation, and
   evaluate it with the same Cloudcast evaluator used by Engram. The
   evaluator, not Codex's self-report, is the source of benchmark
   scores.

   A second Codex treatment arm may inject the Memex-SR MCP server
   while preserving the same model, reasoning effort, workspace,
   prompt, evaluator wrapper, and evaluation cap. This arm should be
   named `codex_cli_gpt55_high_okg_mcp` and reported as
   `fair_out_of_box_baseline_with_okg_mcp`. It answers a narrower
   question than the primary baseline: whether giving the same general
   coding agent bounded OKG access changes Cloudcast search behavior.
   The arm should expose the compact operator MCP surface
   (`inspect`, `search`, `expand`, `filter`, `map`, `aggregate`,
   `propose`, `query`) and hide `generate_context_packet` for now, so
   live agents interact with graph facts directly rather than consuming
   a pre-rendered packet. It must not use raw SQL, broad graph dumps,
   oracle artifacts, generated context-packet tools, or pre-rendered
   context packets copied into the workspace.

   Suggested command shape:

   ```bash
   codex exec \
     -C "$WORKSPACE" \
     -m gpt-5.5 \
     -c 'model_reasoning_effort="high"' \
     --json \
     --output-last-message "$RESULT_DIR/codex_last_message.md" \
     "$PROMPT"
   ```

   Every run should save Codex CLI version, model, reasoning effort,
   command, prompt hash, evaluator hash, allowed-file manifest hash,
   elapsed time, JSONL event log, final message path, candidate file
   hash, and normalized Cloudcast metrics.

## Risks / Trade-offs

- Oracle leakage -> Mark `optimal.py` and
  `task_prompt_direction_with_optimal.txt` holdout-only and assert they
  never appear in context-packet evidence ids.
- OpenRouter incompatibility -> Add a small smoke test before any long
  run and keep a provider/model metadata file in the result directory.
- Paper reproduction drift -> Record prompt hash, evaluator hash, model
  slug, API base URL, budget, and result parser version for every run.
- Codex baseline drift -> Override model and reasoning effort on the
  CLI rather than relying on the user's local Codex defaults, and record
  the Codex CLI version in every run directory.
- False comparison claim -> Label the primary Codex arm as
  `fair_out_of_box_baseline`. It is useful for understanding whether
  Engram/OKG beats a strong general agent, but it should not be used as
  a clean architecture ablation unless a later matched-control arm is
  added.
- Literature sprawl -> Require source tiers and `transfer_to_cloudcast`
  labels so the context packet stays concise.
- OKG silent failure -> Verify catalog load, publish generation, graph
  deltas, and no-op rerun behavior before using graph output in Engram.

## Migration Plan

1. Land the OpenSpec proposal and refined planning docs.
2. Add fixture manifests and parsers without changing the baseline
   Cloudcast run path.
3. Add OpenRouter model routing behind explicit CLI/env config.
4. Add context-packet support behind `--okg_context_file`.
5. Add Memex-SR graph sources and publish a Cloudcast fixture
   generation.
6. Add the harvester and publish fixture run artifacts.
7. Run smoke, pilot, then paper-like reproduction.

Rollback is straightforward: omit the OKG/OpenRouter flags and Engram
continues using the existing Cloudcast path.

## Open Questions

- Which OpenRouter model should be the first serious run:
  `openai/o3`, `openai/gpt-5.2`, or both?
- Should the first A/B use `max_agents=5` and rely on a 100-evaluation
  cap, or match the current example's wall-clock controls first?
- Which 20-50 literature seeds should be manually approved before the
  first useful context packet?
- Is the local `$419` target from a different Cloudcast configuration,
  an oracle variant, or stale prompt text?
