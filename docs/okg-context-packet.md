# OKG Context Packet

Engram agents should get Memex-SR context through the OKG MCP tool
`generate_context_packet`, not by reading a static packet file. The
packet is generated from a pinned OKG generation, and every evidence id
in the rendered markdown should resolve through `get_node`.

## MCP Call

```python
packet_markdown = mcp_client.call_tool(
    "generate_context_packet",
    {
        "problem_name": "cloudcast",
        "domain": "networking",
        "topic_slugs": ["multicast", "routing"],
        "evidence_budget": 20,
        "token_budget": 4000,
        # Optional: pass generation_id to pin explicitly.
    },
)

agent.prompt = packet_markdown + "\n\n---\n\n" + agent.task_prompt
```

## Packet Shape

```markdown
# Research Context Packet

## Problem Class

## Design Principles

## Mechanisms To Try

## Trade-Off Map

## Experiment Advice

## Anti-Patterns

## Evidence Index
```

## Agent Rules

- Treat packet claims as hypotheses to test, not ground truth.
- Preserve evidence ids when a principle or mechanism affects a design
  choice.
- Turn principles into concrete implementation changes and evaluate
  them with the benchmark harness.
- When the packet suggests a trade-off, design an experiment that can
  distinguish the sides of that trade-off.
- Write negative results into Engram run artifacts so Memex-SR can
  ingest them through `engram_runs`.

## Smoke Questions

- For Cloudcast, what prior mechanisms are relevant to multicast,
  routing, scheduling, replication, and bandwidth-delay trade-offs?
- Which design principles are supported by papers versus by Engram run
  evidence?
- Which mechanisms have known failure modes or anti-patterns?
- Which evidence ids in the packet resolve to live `paper`,
  `document_chunk`, `experiment_result`, or `empirical_claim` nodes?
