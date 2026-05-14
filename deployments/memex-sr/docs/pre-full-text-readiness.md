# Pre-Full-Text Readiness

This document records the current Memex-SR local cut and the gates we
should pass before spending time on PDF/full-text acquisition.

## Current Local Graph Cut

Local database:

```text
postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
```

Latest verified generation:

```text
generation: 5
status: published
published_at: 2026-05-14T18:47:59.671645+00:00
catalog_version: 3
nodes_live: 25,827
edges_live: 39,561
source_sync_dlq: 0
```

Live node counts:

| Subtype | Count |
| --- | ---: |
| `person` | 13,499 |
| `document_asset` | 7,310 |
| `paper` | 4,782 |
| `document_chunk` | 96 |
| `entity_mention` | 76 |
| `venue_edition` | 24 |
| `venue` | 16 |
| `publication_series` | 16 |
| `document` | 6 |
| `corpus_coverage_snapshot` | 1 |
| `corpus_pack` | 1 |

Live edge counts:

| Edge Type | Count |
| --- | ---: |
| `authored_by` | 27,120 |
| `contains` | 7,446 |
| `published_in` | 4,782 |
| `member_of` | 188 |
| `mentions` | 24 |
| `references` | 1 |

The current manifest-backed paper cut is:

```text
deployments/memex-sr/manifests/paper_cut.json
papers: 4,782
source records:
  usenix: 1,180
  pvldb: 1,787
  openalex: 2,978
manifest size: about 15 MB
```

Current paper coverage by venue/year:

| Venue | 2022 | 2023 | 2024 | 2025 | 2026 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `icde` | 326 | 0 | 0 | 0 | 0 | 326 |
| `nsdi` | 78 | 96 | 112 | 83 | 151 | 520 |
| `osdi` | 49 | 55 | 53 | 53 | 138 | 348 |
| `pvldb` | 605 | 467 | 538 | 574 | 107 | 2,291 |
| `sigmod` | 0 | 271 | 252 | 364 | 98 | 985 |
| `usenix_atc` | 67 | 66 | 78 | 101 | 0 | 312 |

Current cut limitations:

- DBLP is not yet usable from the local shell; HTTPS requests reset or
  time out. The current cut therefore uses USENIX, PVLDB, and OpenAlex.
- The current graph has metadata and `document_asset` URL hints, not
  parsed full text.
- The target matrix still has missing or weak venue coverage:
  `sosp`, `sigcomm`, `hotnets`, `conext`, `eurosys`, `socc`,
  `mlsys`, `pods`, `cidr`, and `edbt`.
- OpenAlex-derived records may include demos, tutorials, non-main-track
  papers, or source-scope noise. Treat them as a candidate cut until the
  coverage and quality audits pass.

## Local Test Loop

From the Engram repo root:

```bash
export REPO_ROOT="$(pwd)"
export MEMEX_SR_OKG_DSN=postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT=1
```

Regenerate the source samples:

```bash
external/okg/.venv/bin/python deployments/memex-sr/scripts/sample_data_sources.py \
  --config deployments/memex-sr/data_sources.yaml \
  --timeout 15
```

Regenerate the paper cut:

```bash
external/okg/.venv/bin/python deployments/memex-sr/scripts/collect_paper_cut.py
```

Load the catalog:

```bash
external/okg/.venv/bin/okg catalog load \
  --deployment "$REPO_ROOT/deployments/memex-sr" \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json
```

Publish the paper cut:

```bash
OKG_DEPLOYMENTS_DIR="$OKG_DEPLOYMENTS_DIR" \
external/okg/.venv/bin/okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --include paper-cut \
  --mode scope_complete \
  --progress \
  --json
```

Verify the published generation:

```bash
external/okg/.venv/bin/okg generation describe 5 \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

external/okg/.venv/bin/okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

external/okg/.venv/bin/okg doctor \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

external/okg/.venv/bin/okg metrics \
  --source-sync \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

Verify unchanged reruns are incremental:

```bash
OKG_DEPLOYMENTS_DIR="$OKG_DEPLOYMENTS_DIR" \
external/okg/.venv/bin/okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --include paper-cut \
  --mode scope_complete \
  --no-publish \
  --json
```

Expected no-op result:

```text
nodes_appended: 0
edges_appended: 0
retract_n: 0
retract_e: 0
```

If an MCP client was connected before generation 5, reconnect it so the
session pins the latest generation.

## Pre-Full-Text Gates

### 1. Corpus Coverage Audit

Before downloading PDFs, produce a coverage report for every target
venue/year in `venues.yaml`.

Minimum checks:

- expected venue-years versus landed venue-years;
- landed paper count by venue/year;
- source provider distribution by venue/year;
- source status for DBLP, USENIX, PVLDB, OpenAlex, OpenReview, arXiv,
  Crossref, and Semantic Scholar;
- missing target venues and years;
- suspicious venue-years with obvious over/under counts.

Current missing or weak target coverage:

```text
sosp, sigcomm, hotnets, conext, eurosys, socc, mlsys, pods, cidr, edbt
```

### 2. Paper Quality Audit

Before full-text acquisition, run checks over `paper` nodes and the
manifest:

- duplicate DOI;
- duplicate normalized title in the same venue/year;
- missing title, year, or venue id;
- missing `published_in` edge;
- missing authors;
- missing source records;
- missing DOI/OpenAlex ID where expected;
- 2026 records that are future, incomplete, or venue-page placeholders;
- OpenAlex records that are not main-track research papers.

The output should be a committed report under
`deployments/memex-sr/reports/` and should distinguish hard blockers
from known warning classes.

### 3. Asset URL Audit

Classify every `document_asset` before download:

- direct PDF URL verified by `HEAD` or bounded `GET`;
- landing page only;
- inferred URL that still needs verification;
- DOI/publisher landing page only;
- blocked or needs operator-supplied copy.

Do not let the downloader chase unverified inferred URLs. The
downloader input should be a manifest with terminal states such as
`verified_pdf`, `landing_only`, `blocked`, `needs_operator_asset`, or
`failed_retryable`.

### 4. Guardrail Invariants

Add deployment invariants before full text:

- every `paper` has title, year, venue id, and `published_in`;
- every `paper` has at least one source record;
- DOI is unique when present;
- every `document_asset` belongs to exactly one paper unless explicitly
  marked shared;
- no live network call is required during publish;
- full-text documents must come from local manifest assets;
- parsed chunks must be parent-scoped to avoid collapsing shared
  boilerplate across papers.

These invariants should block or degrade publish before a bad full-text
run creates thousands of wrong chunks.

## Repo Readiness

Before opening this to collaborators:

- Keep `external/okg` pinned to the intended OKG `dev` commit.
- Confirm `deployments/memex-sr/` contains everything needed to rebuild
  the local cut from a clean clone: config, source adapters, schemas,
  scripts, manifest, and docs.
- Decide whether `paper_cut.json` stays committed. It is about 15 MB,
  which is acceptable for GitHub but still generated data. If we move it
  out of git later, replace it with an artifact download command and a
  checksum.
- Add a clean-room setup note for collaborators who do not have the
  local `okg-pg` container.
- Add contributor examples for extending venues, sources, schema
  modules, parsers, and reports.
- Run a fresh local rebuild from an empty database before opening a PR.

The next implementation step should be the coverage and quality audit
reports, not full-text download.
