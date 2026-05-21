# Gemini 3.5 Flash Extraction Comparison

Generated: `2026-05-20`

This compares the existing `openai/gpt-5-mini` 10-paper extraction manifest with a same-input `google/gemini-3.5-flash` run. The Gemini run was written to a separate manifest and was not published to the graph.

## Manifests

- GPT-5-mini: `deployments/memex-sr/manifests/paper_research_facts.jsonl`
- Gemini 3.5 Flash: `deployments/memex-sr/manifests/paper_research_facts_gemini35_sample.jsonl`
- Gemini usage probe: `deployments/memex-sr/manifests/paper_research_facts_gemini35_usage_probe.jsonl`
- GPT-5-mini usage probe: `deployments/memex-sr/manifests/paper_research_facts_gpt5mini_usage_probe.jsonl`

## 10-Paper Output Counts

| Model | Evidence | Principles | Mechanisms | Trade-offs | Anti-patterns |
|:--|--:|--:|--:|--:|--:|
| openai/gpt-5-mini | 61 | 29 | 30 | 24 | 19 |
| google/gemini-3.5-flash | 46 | 23 | 22 | 13 | 13 |

## One-Paper Exact Usage Probes

The original 10-paper runs did not capture provider usage. After adding `usage: {include: true}`, one forced probe was run for each model on the first paper. These are exact OpenRouter-reported costs for that paper only.

| Model | Prompt tokens | Completion tokens | Reasoning tokens | Cost |
|:--|--:|--:|--:|--:|
| openai/gpt-5-mini | 4296 | 3543 | 1152 | $0.008160 |
| google/gemini-3.5-flash | 4581 | 3017 | 1292 | $0.034024 |

## Initial Quality Read

- Gemini 3.5 Flash is more conservative: fewer total facts, especially trade-offs and anti-patterns.
- Gemini often produces cleaner canonical labels, such as `Clique-Based Network Partitioning` and `Hybrid Memory Hierarchy for Switch Scale`.
- Gemini also sometimes over-compresses into labels that need evidence scrutiny, such as `Network Function Collapsing` or `Allocation-Free Packet Processing`.
- GPT-5-mini produced richer evidence and more detailed mechanisms/limits, but also more candidate facts, which increases review burden and noise risk.
- For the production extractor, neither model should be trusted in one pass. The better architecture is evidence extraction, quote/span verification, candidate fact extraction, and a separate reviewer/promotion pass.

## Recommendation

Use Gemini 3.5 Flash as a candidate reviewer/canonicalizer, not necessarily as the only first-pass extractor. GPT-5-mini is cheaper on the one-paper exact probe and more verbose; Gemini is more compact and expensive. The production design should be model-agnostic and select models per stage: cheap evidence extraction, stronger/refinement model for promotion decisions.
