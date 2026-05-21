## Why

Why is this broken?

Memex-SR currently has a respectable paper metadata cut, but the graph is
not yet a useful research substrate because most paper assets are only URL
hints. The incomplete substrate stage is source coverage and projection:
full text has not been acquired into a local cache, parsed into documents,
chunked, published, and then distilled into systems-research facts.

The Cloudcast source slice proved the path but stayed too small. A real
systems-research deployment needs thousands of live text chunks from the
paper cut, plus a follow-on distillation lane that turns paper evidence
into DesignPrinciple, Mechanism, TradeOff, AntiPattern, Algorithm, and
Evidence nodes.

## What Changes

- Add an operator-controlled full-text acquisition workflow for open PDF
  assets from the existing `paper_cut.json`.
- Keep publish network-free: downloaded files go into a deterministic
  local cache and a JSONL acquisition manifest.
- Add a Memex-SR source adapter that parses cached paper PDFs/text into
  `document` and `document_chunk` nodes, updates `document_asset` state,
  and links chunks back to paper metadata through attributes.
- Publish a first materially large local batch that adds thousands of
  graph rows, not hundreds.
- Leave MIT/authenticated publisher retrieval for an explicit operator
  queue; do not claim papers are ingested until bytes exist locally.
- Prepare the next lane for source-backed principle/mechanism extraction
  over the newly published chunks.

## Impact

- Affected deployment files:
  - `deployments/memex-sr/source_registry.yaml`
  - `deployments/memex-sr/scripts/`
  - `deployments/memex-sr/sources/`
  - `deployments/memex-sr/manifests/`
  - `deployments/memex-sr/reports/`
- No OKG substrate behavior changes intended.
- Acquisition is polite/cache-first and avoids blocked publisher hosts.
