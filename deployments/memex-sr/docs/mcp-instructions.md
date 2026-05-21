# Memex-SR MCP Instructions

This OKG deployment is the local Memex-SR graph, the Engram-owned memory
substrate for autonomous systems research.

Use it to answer questions about:

- the Memex-SR deployment plan and ontology direction
- the current systems/database paper metadata cut
- how Engram should use OKG as a read tool
- how to generate Engram research context packets
- what prior Engram runs learned, after run artifacts are ingested
- what data is currently indexed in the local graph

Start with `describe_graph`, then use `search`, `list_neighbors`,
`traverse_path`, and `get_node` to ground answers in graph evidence.
For literature metadata, search `paper`, `venue`, `venue_edition`, and
`document_asset` nodes, then traverse `authored_by`, `published_in`, and
`contains` edges to authors, venue editions, and URL hints.

For Engram agent context, call `generate_context_packet` with
`problem_name`, `domain`, `topic_slugs`, `evidence_budget`, and
`token_budget`. Resolve packet evidence ids with `get_node` before
treating them as important.

Current local generation `5` includes paper metadata and asset URL hints
from USENIX, PVLDB, and OpenAlex. It does not yet include parsed paper
full text, evidence slices, or distilled textbook-style principles. For
full current graph contents and extension guidance, see
`deployments/memex-sr/docs/okg-newcomer-guide.md`.
