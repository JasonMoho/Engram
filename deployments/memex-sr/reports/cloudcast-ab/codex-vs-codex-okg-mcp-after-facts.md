# Cloudcast A/B Smoke Comparison

Generated: `2026-05-20 12:45:16 UTC`

This report separates Engram arms from the Codex CLI baseline. Codex is a fair out-of-box baseline, not a strict Engram architecture ablation.

| Arm | Family | Success | Score | Inferred cost | Eval calls | Elapsed s | Model | OKG gen | OKG MCP calls | Result dir |
|:--|:--|:--|--:|--:|--:|--:|:--|:--|:--|:--|
| codex_cli_gpt55_high | codex_cli | true | 0.001602764006 | 622.922172 | 1 | 550.3 | gpt-5.5 | n/a | n/a | `/Users/jason/projects/mit/Engram/results/codex_baseline_cloudcast/20260520T035654Z` |
| codex_cli_gpt55_high_okg_mcp | codex_cli | true | 0.001602093323 | 623.183364 | 2 | 649.9 | gpt-5.5 | 7 | 3/3 | `/Users/jason/projects/mit/Engram/results/codex_okg_mcp_cloudcast/20260520T123410Z` |

## Readout

- Best Codex smoke score: `0.001602764006` (cost `622.922172`).
- No Engram run directories were supplied to this report.

## Contamination Notes

- Fair Engram control runs should omit `--give_files`.
- OKG-context runs should record `okg_context_hash` and `okg_generation_id` in `benchmark_run_config.json`.
- Codex baseline workspaces exclude `optimal.py`, `task_prompt_direction_with_optimal.txt`, and OKG context packets.
- Codex+OKG-MCP runs may query bounded graph tools, but their workspaces still exclude oracle files and pre-rendered OKG packets.
