# Cloudcast Codex Baseline Smoke

Run timestamp: `20260520T035654Z`

Command:

```bash
.venv/bin/python deployments/memex-sr/scripts/run_cloudcast_codex_baseline.py \
  --max-evals 2 \
  --codex-timeout-seconds 900
```

Run metadata:

- Arm: `codex_cli_gpt55_high`
- Comparison type: `fair_out_of_box_baseline`
- Codex CLI: `codex-cli 0.131.0-alpha.9`
- Model: `gpt-5.5`
- Reasoning effort: `high`
- Evaluation cap: 2
- Evaluations used by Codex: 1
- Result directory: `results/codex_baseline_cloudcast/20260520T035654Z`

Final external Cloudcast score:

- Success: true
- Combined score: `0.0016027640062773725`
- Inferred total cost: `622.922172`
- Successful configs: 5
- Failed configs: 0
- Final evaluator elapsed time: `1.0059320000000298` seconds

Initial-program reference from the same evaluator:

- Combined score: `0.0009552371980292827`
- Inferred total cost: `1045.860405`
- Successful configs: 5
- Failed configs: 0

Contamination controls:

- No OKG context was supplied.
- `optimal.py` was excluded from the workspace.
- `task_prompt_direction_with_optimal.txt` was excluded from the
  workspace.
- The workspace used a copied non-oracle Cloudcast evaluator bundle so
  simulator output writes stayed inside the Codex sandbox.
