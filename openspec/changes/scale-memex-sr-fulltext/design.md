## Design

### Acquisition

The acquisition script reads `paper_cut.json` and selects open PDF assets
whose hosts are allowed by `download_host_policy.yaml`. The first lane is
USENIX and PVLDB because those URLs are already in the paper cut, open,
and stable enough for a local batch. ACM/IEEE/DOI landing pages remain
metadata/manual until an operator supplies local bytes or an approved MIT
retrieval workflow.

The script writes:

- cached bytes under `deployments/memex-sr/.cache/paper_fulltext/<host>/<asset_id>.pdf`;
- `deployments/memex-sr/manifests/paper_fulltext_assets.jsonl` with paper
  id, asset id, title, venue, year, URL, local path, hash, and state;
- a markdown acquisition report with counts and failures.

### Publish Source

`PaperFulltextDocumentsSource` reads the JSONL manifest only. It does no
network I/O. For available records it extracts PDF text with `pdfminer`,
normalizes text, chunks by character window, and emits:

- `document_asset` with `downloaded=true`, content hash, local path, and
  source metadata;
- `document` with paper id, venue/year, source asset, parse warnings, and
  searchable title/body prefix;
- `document_chunk` nodes with full chunk text and paper metadata;
- `document contains chunk` and `chunk member_of document` edges.

Record-set reconciliation makes no-change reruns append zero facts and
skip publish.

### Distillation Follow-On

This change stops at full-text projection. Principle/mechanism extraction
will run over the published paper chunks and must emit source-backed typed
facts with evidence IDs resolving to chunks/documents from published
generations.
