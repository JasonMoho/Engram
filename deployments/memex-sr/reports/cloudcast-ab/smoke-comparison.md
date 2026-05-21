# Cloudcast A/B Smoke Comparison

Generated: `2026-05-20 05:03:34 UTC`

This report separates Engram arms from the Codex CLI baseline. Codex is a fair out-of-box baseline, not a strict Engram architecture ablation.

| Arm | Family | Success | Score | Inferred cost | Eval calls | Elapsed s | Model | OKG gen | Result dir |
|:--|:--|:--|--:|--:|--:|--:|:--|:--|:--|
| codex_cli_gpt55_high | codex_cli | true | 0.001602764006 | 622.922172 | 1 | 550.3 | gpt-5.5 | n/a | `/Users/jason/projects/mit/Engram/results/codex_baseline_cloudcast/20260520T035654Z` |

## Readout

- Best Codex smoke score: `0.001602764006` (cost `622.922172`).
- No Engram run directories were supplied to this report.

## Contamination Notes

- Fair Engram control runs should omit `--give_files`.
- OKG-context runs should record `okg_context_hash` and `okg_generation_id` in `benchmark_run_config.json`.
- Codex baseline workspaces exclude `optimal.py`, `task_prompt_direction_with_optimal.txt`, and OKG context packets.
