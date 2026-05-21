# Tasks: Cloudcast OKG A/B Evaluation Slice

## 0. Scope And Controls

- [ ] 0.1 Freeze the fair Cloudcast benchmark inputs.
      Record hashes for `task_prompt_direction.txt`,
      `initial_program.py`, `evaluator.py`, `simulator.py`, profile
      CSVs, and `config_direction.yaml`.
      Verification: a committed manifest records each path and content
      hash, and explicitly marks `optimal.py` plus
      `task_prompt_direction_with_optimal.txt` as excluded oracle
      artifacts.

- [ ] 0.2 Decide the first A/B run budget.
      Record model, run count, `max_agents`, `agent_timeout`,
      `remove_kb`, `give_files`, and result-directory naming.
      Verification: the run config is committed under the Memex-SR
      Cloudcast report directory and both arms share every value except
      the OKG context-packet flag.

- [ ] 0.3 Define Cloudcast score reporting.
      Standardize best score, inferred total cost `1 / score - 1`,
      total simulations, elapsed time, success flag, and threshold
      crossings.
      Verification: a fixture score file is parsed into the normalized
      metric shape used by the report and future OKG harvest.

## 1. OKG Cloudcast Graph Slice

- [ ] 1.1 Add a Cloudcast benchmark artifact source.
      Emit graph records for the problem, prompt, evaluator, simulator,
      config, profiles, and initial program.
      Verification: a real OKG publish creates expected
      `BenchmarkProblem` and `BenchmarkArtifact` rows or their approved
      equivalent subtypes, and `okg generation describe <g>` reports the
      generation as published.

- [ ] 1.2 Add required ontology and bridge narrowings.
      Extend the Memex-SR overlay only for concepts not already covered
      by substrate modules.
      Verification: `okg catalog load --apply` succeeds, and a fixture
      publish lands every new edge route without narrowing violations.

- [ ] 1.3 Add a curated Cloudcast literature/reference manifest.
      Start with 20-50 reviewed sources across multi-cloud multicast,
      traffic engineering, min-cost/multi-commodity flow, Steiner-tree
      approximations, capacity constraints, and transfer scheduling.
      Verification: the publish adds the expected paper/document asset
      records, and a coverage report lists title, venue/source, access
      basis, and evidence quality for every seed.

- [ ] 1.4 Parse and chunk acquired open/operator assets.
      Use only local cached assets; do not perform network fetches
      during publish.
      Verification: published graph counts show document/chunk deltas
      for the Cloudcast seed set, parser warnings are recorded, and
      chunks link back to their parent documents.

- [ ] 1.5 Add Cloudcast evidence/distillation records.
      Emit evidence-backed principles, mechanisms, trade-offs,
      anti-patterns, and experiment advice.
      Verification: graph search for "Cloudcast min-cost flow",
      "capacity constrained multicast", and "provider egress limits"
      returns evidence-bearing records with source/chunk provenance.

- [ ] 1.6 Verify incremental behavior for the graph slice.
      Rerun Cloudcast sources without input changes.
      Verification: the next publish reports zero new live node/edge
      deltas for unchanged Cloudcast source scopes, and queue/DLQ
      metrics remain clean.

## 2. Context Packet

- [ ] 2.1 Implement a Cloudcast context-packet generator.
      Inputs should include problem name, topic slugs, generation id,
      evidence budget, and token budget.
      Verification: generated Markdown includes problem class, design
      principles, mechanisms, trade-off map, experiment advice,
      anti-patterns, and an evidence index.

- [ ] 2.2 Enforce contamination controls in packet generation.
      Exclude oracle artifacts and any node marked holdout-only.
      Verification: the generated packet and evidence ids do not contain
      `optimal.py`, `task_prompt_direction_with_optimal.txt`, or derived
      oracle solution text.

- [ ] 2.3 Save packet metadata for reproducibility.
      Include graph generation id, packet hash, topic list, evidence
      ids, generator version, and prompt hash.
      Verification: metadata JSON validates against the committed packet
      and can be copied into an Engram run directory.

## 3. Engram Integration

- [ ] 3.1 Add `--okg_context_file` to the handoff example path.
      Append packet content to the task prompt and record packet
      metadata in the result directory.
      Verification: running without the flag produces byte-for-byte
      identical task prompt content to the current path, while running
      with the flag logs the context packet path, hash, and generation.

- [ ] 3.2 Add a run-config output for OKG-assisted runs.
      Persist arm name, problem name, model, budget, OKG generation,
      packet id/hash, and evidence ids.
      Verification: every result directory contains a machine-readable
      config that the report script and harvester can parse.

- [ ] 3.3 Keep live OKG tools optional.
      Do not block the context-first A/B on `okg_search` or
      `okg_traverse_path`.
      Verification: the context-only run succeeds with no MCP server
      available after packet generation.

- [ ] 3.4 Add bounded live OKG tools as a second treatment arm.
      Wrap the regular OKG MCP operations with pinned generation,
      result limits, route limits, and no raw SQL.
      Verification: a smoke agent can call each allowed tool, every tool
      response includes generation id and evidence provenance, and
      forbidden broad operations are unavailable.

## 4. Run Harvesting

- [ ] 4.1 Implement a Cloudcast Engram run harvester.
      Parse result JSON, args, console logs, research journal,
      experiment score files, code snapshots, and result CSVs.
      Verification: a fixture run publishes `ResearchRun`,
      `AgentAttempt`, `Experiment`, `CandidateImplementation`,
      `MetricObservation`, `FailureDiagnosis`, `ResearchNote`, and
      `WorkspaceArtifact` rows or their approved equivalent subtypes.

- [ ] 4.2 Link harvested runs to OKG context.
      When a run used a packet, link the research run and candidate
      implementations to the packet and evidence ids.
      Verification: graph traversal from the run reaches the context
      packet and the evidence records that informed it.

- [ ] 4.3 Verify harvest incrementality.
      Rerun harvest on the same result directory.
      Verification: the second publish appends zero new facts for
      unchanged artifacts; changing one score file scopes the delta to
      that metric and dependent summaries.

## 5. Codex CLI Baseline

- [x] 5.1 Add a Codex baseline runner.
      Invoke `codex exec` with `-m gpt-5.5` and `-c
      'model_reasoning_effort="high"'` in an isolated workspace.
      Verification: a dry-run or fixture run stores the exact command,
      Codex CLI version, JSONL events, final message, prompt hash, and
      allowed-file manifest hash.

- [x] 5.2 Add a benchmark-clean out-of-box Codex workspace and evaluator
      wrapper.
      Include `task.md`, `initial_program.py`, candidate output
      instructions, and an `evaluate_candidate` command. Allow normal
      Codex CLI shell/edit/search behavior inside the workspace.
      Verification: oracle and holdout files are absent; the evaluator
      wrapper enforces the configured evaluation-call cap and records
      every attempt.

- [x] 5.3 Add Codex candidate extraction and scoring.
      Extract the generated Cloudcast candidate and evaluate it with the
      same local Cloudcast evaluator as the Engram arms.
      Verification: a fixture candidate produces normalized best score,
      inferred total cost, success flag, simulations, and elapsed time.

- [x] 5.4 Run a no-OKG Codex smoke baseline.
      Do not provide OKG context, live OKG tools, `optimal.py`, or
      `task_prompt_direction_with_optimal.txt`.
      Verification: the result directory records
      `codex_cli_gpt55_high`, model, reasoning effort, candidate hash,
      evaluator hash, contamination-audit status, and
      `comparison_type=fair_out_of_box_baseline`.

## 6. A/B Execution

- [ ] 6.1 Run one control smoke, one OKG-context smoke, and one Codex
      baseline smoke.
      Use `max_agents=1` and a short timeout to validate wiring.
      Verification: all three runs complete or fail with archived result
      directories, the OKG arm records the packet hash/generation, and
      the Codex arm records CLI/model/reasoning metadata.

- [ ] 6.2 Run a three-seed pilot.
      Use equal budgets across Engram control and OKG-context arms, and
      comparable evaluator-call and wall-clock reporting for Codex.
      Verification: the report parser produces per-run best score,
      inferred total cost, simulations, elapsed time, and design-family
      labels for all runs.

- [ ] 6.3 Decide whether the serious A/B is warranted.
      Review pilot stability, score variance, and any obvious packet
      quality problems.
      Verification: a short decision note records whether to improve the
      graph slice, add live tools, or proceed to the 10-run arm.

- [ ] 6.4 Run the serious A/B.
      Use the agreed model and budget, with at least 10 runs per arm if
      making a claim.
      Verification: every run directory is harvested into OKG, and the
      final report includes aggregate metrics and baseline comparisons.

## 7. Reporting And Handoff

- [ ] 7.1 Create the Cloudcast A/B report.
      Include graph generation counts, source/evidence coverage,
      commands, environment, per-run metrics, aggregate metrics,
      qualitative analysis, and contamination audit.
      Verification: a collaborator can reproduce one control and one
      OKG-context run plus one Codex baseline from the report commands.

- [ ] 7.2 Update Memex-SR docs with the Cloudcast workflow.
      Link proposal, tasks, packet contract, run commands, and harvester
      output shape.
      Verification: a reader starting from `deployments/memex-sr/README.md`
      can find the Cloudcast proposal, run instructions, and extension
      points.

- [ ] 7.3 Record next benchmark recommendations.
      Decide whether to apply the same OKG flow to Vidur, LLM-SQL, EPLB,
      or another ADRS problem.
      Verification: a follow-up note names the next target and lists the
      corpus/ontology changes needed before running it.
