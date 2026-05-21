## ADDED Requirements

### Requirement: Cloudcast Benchmark Controls

The system SHALL record enough metadata to reproduce each Cloudcast run
and distinguish fair benchmark inputs from oracle or holdout inputs.

#### Scenario: Fair run metadata is captured
- **WHEN** a Cloudcast run is launched for control or OKG-assisted A/B
- **THEN** the run metadata SHALL include problem name, prompt path,
  prompt hash, evaluator path, evaluator hash, initial program hash,
  model slug, provider, API base URL class, run budget, result parser
  version, and result directory.

#### Scenario: Oracle artifacts are excluded
- **WHEN** a fair Cloudcast run or context packet is prepared
- **THEN** `optimal.py` and `task_prompt_direction_with_optimal.txt`
  SHALL be marked holdout-only and SHALL NOT be available in the agent
  prompt, context packet, or OKG evidence set.

#### Scenario: Baseline behavior remains unchanged
- **WHEN** no OKG or OpenRouter-specific flags are supplied
- **THEN** the existing Cloudcast handoff example SHALL run with the
  same prompt content and initial files as before this change.

### Requirement: OpenRouter Reproduction Path

The system SHALL support Cloudcast reproduction through OpenRouter while
preserving model identity and filesystem-safe run labels.

#### Scenario: OpenRouter o3 smoke run
- **WHEN** `OPENROUTER_API_KEY` is present and the user selects
  `openrouter:openai/o3`
- **THEN** Engram SHALL route model calls through the OpenAI-compatible
  OpenRouter endpoint and store a sanitized model label in result paths.

#### Scenario: Paper-like run budget is represented
- **WHEN** a paper-like reproduction run is configured
- **THEN** the configuration SHALL represent the paper controls of 10
  runs and 100 Cloudcast evaluation calls per run, even when wall-clock
  limits are also present.

#### Scenario: Benchmark target discrepancy is explicit
- **WHEN** Cloudcast report generation compares results to reference
  targets
- **THEN** the report SHALL distinguish the Engram paper's `$626`
  human-SOTA reference from the local prompt's `$419` expert-solution
  statement until the evaluator/config difference is resolved.

### Requirement: Codex CLI Baseline

The system SHALL support a non-Engram Cloudcast baseline that invokes
Codex CLI with `gpt-5.5` and high reasoning effort, then scores the
produced candidate with the same Cloudcast evaluator used by the Engram
arms. The primary Codex arm is a fair out-of-box baseline, not a strict
Engram architecture ablation.

#### Scenario: Codex baseline command is explicit
- **WHEN** the Codex baseline is launched
- **THEN** the runner SHALL call `codex exec` with `-m gpt-5.5` and
  `-c model_reasoning_effort="high"` or the TOML-equivalent quoted
  override, independent of the user's local Codex defaults.

#### Scenario: Codex baseline uses fair benchmark inputs
- **WHEN** the Codex baseline workspace is prepared
- **THEN** it SHALL receive the same fair Cloudcast prompt, initial
  program, candidate output instructions, and configured evaluation-call
  budget as the no-OKG Engram control, and SHALL NOT receive OKG context
  or holdout/oracle artifacts unless the arm name explicitly declares a
  separate treatment.

#### Scenario: Codex baseline uses out-of-box CLI affordances
- **WHEN** the Codex baseline run starts
- **THEN** Codex SHALL be allowed to use its normal CLI affordances,
  including shell access, file editing, file search, and command
  execution inside the isolated benchmark workspace.

#### Scenario: Codex baseline uses a benchmark-clean evaluator wrapper
- **WHEN** the Codex baseline is allowed to test candidate code during a
  run
- **THEN** the workspace SHALL expose an `evaluate_candidate` command
  that invokes the Cloudcast evaluator outside the workspace, enforces
  the configured call cap, records every evaluation attempt, and avoids
  exposing oracle or holdout files to Codex.

#### Scenario: Codex output is evaluated externally
- **WHEN** Codex produces a candidate implementation
- **THEN** the benchmark score SHALL come from the Cloudcast evaluator,
  not from Codex's final message or self-reported score.

#### Scenario: Codex baseline artifacts are captured
- **WHEN** a Codex baseline run completes or fails
- **THEN** the result directory SHALL include Codex CLI version, model,
  reasoning effort, command, prompt hash, evaluator hash, allowed-file
  manifest hash, JSONL event log, final message, candidate file hash
  when present, elapsed time, normalized metric output, and failure
  reason when applicable.

#### Scenario: Report labels comparison type
- **WHEN** a report includes the primary Codex CLI baseline
- **THEN** it SHALL label the arm as `fair_out_of_box_baseline` and
  SHALL NOT describe it as a strict apples-to-apples Engram architecture
  ablation unless a separate matched-control arm is run.

### Requirement: Cloudcast Literature Corpus

The Memex-SR Cloudcast corpus SHALL include direct systems references,
algorithmic foundations, data-structure implementation guidance, and
cloud-economics sources with explicit relevance labels.

#### Scenario: Seed manifest covers required tiers
- **WHEN** the Cloudcast literature manifest is generated
- **THEN** it SHALL include Tier 0 benchmark sources, Tier 1 direct
  predecessor/comparator systems, Tier 2 algorithmic foundations, Tier
  3 implementation/data-structure references, Tier 4 cloud economics
  and measurement sources, and optional Tier 5 stretch references.

#### Scenario: Source relevance is extractable
- **WHEN** a source is included in the Cloudcast corpus
- **THEN** its metadata SHALL include access basis, source tier,
  `transfer_to_cloudcast` label, and extraction targets such as
  objective, constraints, decision variables, mechanism, failure modes,
  and implementation notes.

### Requirement: Cloudcast OKG Context Packet

The system SHALL generate a concise Cloudcast context packet from a
pinned Memex-SR OKG generation.

#### Scenario: Packet has provenance
- **WHEN** a Cloudcast context packet is generated
- **THEN** it SHALL include OKG generation id, topic inputs, source
  hashes, evidence ids, packet hash, and generator version.

#### Scenario: Packet gives actionable research guidance
- **WHEN** an Engram agent receives the Cloudcast context packet
- **THEN** the packet SHALL include problem framing, failed baseline
  patterns, optimization families to try, tractability knobs,
  implementation checks, and an evidence index.

#### Scenario: Packet avoids oracle leakage
- **WHEN** the packet is generated for a fair A/B run
- **THEN** the packet SHALL exclude holdout-only artifacts and evidence
  derived from oracle solution text.

### Requirement: Engram Run Harvesting

The system SHALL harvest Cloudcast run artifacts into Memex-SR through
normal source publication.

#### Scenario: Run artifacts become graph facts
- **WHEN** a Cloudcast run directory is harvested
- **THEN** the harvester SHALL emit source facts for the research run,
  agent attempts, experiments, candidate implementations, metric
  observations, failure diagnoses, research notes, and workspace
  artifacts.

#### Scenario: Harvested facts link to context
- **WHEN** a harvested run used an OKG context packet
- **THEN** the resulting graph facts SHALL link the research run and
  relevant candidate implementations to the context packet and evidence
  ids used by that run.

#### Scenario: Harvest is incremental
- **WHEN** the same unchanged Cloudcast run directory is harvested twice
- **THEN** the second publish SHALL append zero new live facts for that
  run scope.

### Requirement: A/B Reporting

The system SHALL produce a Cloudcast A/B report that is reproducible
and benchmark-fair.

#### Scenario: Report includes quantitative metrics
- **WHEN** control, Codex baseline, and OKG-assisted Cloudcast runs
  complete
- **THEN** the report SHALL include per-run best score, inferred total
  cost, total simulations, elapsed time, threshold crossings, aggregate
  mean/median/best/variance, and confidence intervals when sample size
  permits.

#### Scenario: Report separates agent families
- **WHEN** the report includes Codex CLI results
- **THEN** it SHALL label those rows as `codex_cli_gpt55_high` and SHALL
  NOT merge them with Engram control or OKG-assisted Engram arms.

#### Scenario: Report includes graph and contamination audit
- **WHEN** an OKG-assisted arm is reported
- **THEN** the report SHALL include graph generation counts, context
  packet metadata, evidence ids, source coverage summary, and an oracle
  contamination audit.
