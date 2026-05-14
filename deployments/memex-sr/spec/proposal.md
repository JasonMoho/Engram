# Change: Add Memex-SR Deployment

## Why

Why is this broken?

The incomplete substrate stage is **source coverage**, with a secondary
publish/read-side performance problem. The current `memex` graph is a
large mixed-purpose research memory: methodology artifacts, historical
paper metadata, legacy cache material, HEP residue from older
generations, and a small newly proven paper full-text path. That is too
broad and too slow for the next collaborator goal: an autonomous systems
researcher that can quickly answer evidence-backed questions over recent
systems and database papers.

The deployment needs to fork `memex` into a narrow, fast, proper corpus:
all papers from selected systems and database conferences from 2022
through 2026 year-to-date, with durable source progress, scoped
acquisition, parsed full text when lawfully available, and MCP guidance
for agent research workflows.

The longer-term product direction is broader than the first fork:
eventually this should cover all relevant CS papers plus technical
reports, standards, protocols, code-adjacent docs, and high-signal
research/engineering blog posts. The first memex-sr deployment
therefore needs a reusable document acquisition and parsing layer, not a
one-off "paper metadata only" pipeline.

## What Changes

- Add a new substrate deployment named `memex-sr`, forked from the
  memex paper/distillation stack
  but without the broad local methodology library, legacy paper cache,
  HEP providers, or unrelated CS venue groups.
- Define a five-year target venue matrix for systems, networking, ML
  systems, and databases:
  - Systems/networking: SOSP, OSDI, NSDI, SIGCOMM, HotNets, CoNEXT,
    EuroSys, USENIX ATC, SoCC, MLSys.
  - Databases: SIGMOD, VLDB/PVLDB, PODS, CIDR, ICDE, EDBT.
- Use DBLP as the authoritative venue/year enumerator, then enrich from
  Crossref, OpenAlex, Semantic Scholar, OpenReview, and arXiv only when
  they match the target paper set.
- Add a venue-scoped full-text acquisition path that downloads only
  lawful open PDFs or operator-supplied PDFs, checkpoints progress, and
  emits parsed `paper -> document -> document_chunk` evidence.
- Reuse the proven `af_pubs` full-text patterns where appropriate:
  cached PDF assets, bounded downloads, transient-error backoff,
  parser-version fingerprints, PDF-to-text extraction, page/line text
  indexes, section extraction, and section-window chunking.
- Add a host-governed acquisition policy for MIT-network operation:
  per-host concurrency/rate limits, contactful user-agent, conditional
  requests where supported, Retry-After/backoff handling, checkpointed
  pause/resume state, and explicit skip/DLQ reasons. The downloader must
  cache-first and must not hammer ACM, IEEE, USENIX, VLDB, arXiv,
  OpenReview, publisher CDNs, author pages, or lab/blog hosts.
- Define a document normalization path for PDFs, HTML, Markdown, and
  plain text so future all-papers/blog-post ingestion can land in the
  same `document`/`document_section`/`document_chunk` evidence model.
- Add a corpus expansion contract with named source packs, priorities,
  lawful access basis, host policy, parser/chunker requirements,
  coverage metrics, and enable/disable flags so the deployment can grow
  from the first systems/database slice to historical papers, adjacent
  CS venues, technical reports, standards/protocols, project docs, and
  curated research/engineering blogs without changing graph identity.
- Keep the deployment fast by minimizing source scope, using
  `ProgressMarker`/source-progress fingerprints, avoiding broad
  metadata scans on every refresh, and publishing against its own DB.
- Make the execution model DBOS-compatible: deterministic workflow ids,
  deterministic step ids, serializable step outputs, durable
  checkpoints, queue/rate-limit boundaries around external I/O, and
  observable retries/DLQ. The first implementation can stay on the
  substrate job queue, but the boundaries must be clean enough for DBOS
  to wrap acquisition, parsing, and distillation workflows later.
- Define a proper LinkML/catalog ontology for literature, full-text
  assets, evidence, and distillation instead of relying on ad hoc attrs.
  Extension modules must compose through catalog narrowings and
  invariants.
- Ship collaborator extension contracts and examples for adding venues,
  ontology modules, data sources, parsers/chunkers, extractors, and
  distillation methods without changing core substrate code.
- Ship an MCP context packet and audit questions for an autonomous
  systems researcher: paper lookup, evidence trails, literature survey,
  design-principle extraction, trade-off maps, and coverage diagnostics.
- Ship an Engram agent tool contract that exposes a bounded subset of
  the regular OKG/MCP retrieval interface by pinned generation:
  `search`, `get_node`, `list_neighbors`, `traverse_path`, and named
  query recipes/context packets. Engram should not get raw database
  access, unbounded `run_sql`, or broad graph scans by default.
- Add an Engram workspace indexing source that incrementally ingests
  archived Engram runs, research journals, experiment scores,
  candidate implementations, result files, and failure diagnoses as
  research artifacts linked to the literature/evidence graph.

## Impact

- Affected specs: new Engram-owned `memex-sr-deployment` planning spec
  under `deployments/memex-sr/spec/`
- Affected code:
  - new Engram external OKG deployment under `deployments/memex-sr/`
  - OKG substrate dependency tracked through `external/okg` on the OKG
    `dev` branch
  - new `tests/memex_sr/`
  - possible shared helpers extracted from `deployments/memex/`
  - possible shared helpers extracted from `deployments/af_pubs/`
  - new Engram workspace source and ontology bridge under
    `deployments/memex-sr/`
  - extension docs/templates under the memex-sr deployment
  - optional docs updates for MCP setup, Engram tool setup, and
    deployment index
- Builds on:
  - completed `revamp-memex-cs-literature`
  - completed `align-memex-cs-textbook`
  - completed source-sync/progress work in the substrate
  - reusable full-text/cache/chunking work in `deployments/af_pubs`
- Out of scope:
  - Full all-CS ingestion in the first publish. The architecture and
    corpus-pack contract should support it, but the accepted deployment
    starts with the selected systems/database venue-year slice.
  - Unbounded blog crawling. Blog/report ingestion starts from curated
    manifests and explicit host policy.
  - Paywalled publisher PDF scraping without explicit local access or
    license evidence.
  - HEP/genetics/general science expansion.
  - Replacing the substrate jobs/publish system with DBOS runtime code
    in this first fork. The alignment is through DBOS-style durable
    workflow properties: idempotent steps, checkpoints, replayability,
    scoped deltas, and explicit failure states.
  - Letting Engram agents write directly into the OKG database. Engram
    work enters the graph through audited workspace artifacts and a
    normal source/publish cycle.
  - Exposing unbounded SQL or broad graph scans as default Engram tools.
    Raw SQL can remain an operator/debug path; the normal Engram subset
    should preserve OKG semantics while enforcing budgets and allowed
    routes.
