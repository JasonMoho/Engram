# Memex-SR Handoff

This is the clean handoff path for collaborators who need to deploy,
query, or extend the Memex-SR OKG without already knowing OKG.

## What This Is

Memex-SR is an Engram-owned OKG deployment for an autonomous systems
researcher. It is meant to become a literature and experiment memory
for systems/database research:

- ingest papers, reports, standards, blogs, and Engram run artifacts;
- preserve provenance, full text, chunks, and evidence ids;
- distill evidence into principles, mechanisms, trade-offs, failure
  modes, and open problems;
- serve bounded context to Engram agents through MCP or generated
  context packets.

The OKG substrate code lives in the `external/okg` submodule. The
deployment-specific work lives in `deployments/memex-sr`.

## Current Verified State

The latest verified local graph cut was published on May 14, 2026 as
generation `5` in:

```text
postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
```

That cut contains:

- 25,827 nodes and 39,561 edges;
- 4,782 paper nodes;
- paper metadata and asset URL hints from USENIX, PVLDB, and OpenAlex;
- the local Memex-SR design corpus.

It does not yet contain parsed paper full text, evidence slices, or
distilled textbook-style sections. A fresh rebuild may produce a
different generation id; use paper/node/edge counts and source health as
the stable verification signals.

## Start Here

Read in this order:

1. [`docs/okg-newcomer-guide.md`](docs/okg-newcomer-guide.md) for the
   OKG mental model, current graph contents, and extension workflow.
2. [`PHASE0.md`](PHASE0.md) for local setup and MCP registration.
3. [`docs/pre-full-text-readiness.md`](docs/pre-full-text-readiness.md)
   for current graph counts, known corpus gaps, and the gates before PDF
   acquisition.
4. [`spec/source-ingestion-proposal.md`](spec/source-ingestion-proposal.md)
   for the source-ingestion proposal and implementation phases.
5. [`spec/source-ingestion-tasks.md`](spec/source-ingestion-tasks.md)
   for the concrete work plan and acceptance checks.
6. [`docs/source-acquisition.md`](docs/source-acquisition.md) for the
   allowed acquisition lanes for open PDFs, MIT-authenticated material,
   textbooks, and operator-supplied local assets.
7. [`docs/chunky-deployment.md`](docs/chunky-deployment.md) for the
   lower-friction CSAIL chunky login/bootstrap workflow.
8. [`spec/design.md`](spec/design.md) for the longer-term deployment
   architecture.

## Clean Local Bootstrap

From a clean clone:

```bash
git clone --recurse-submodules https://github.com/mit-nms/Engram.git
cd Engram
git submodule update --init --recursive
bash deployments/memex-sr/scripts/bootstrap_local.sh
```

The bootstrap script expects:

- Docker;
- `uv`;
- local access to port `5433`;
- the committed `deployments/memex-sr/manifests/paper_cut.json`.

The script starts the OKG Postgres compose stack, creates the Memex-SR
database, installs extensions, migrates OKG schema, loads the
Memex-SR catalog, publishes the committed local cut, and prints status.
Run `bash deployments/memex-sr/scripts/bootstrap_local.sh --check-only`
to check prerequisites without starting Postgres. If `uv` is missing,
rerun with `--install-uv`. If Docker daemon access is not available,
either ask an admin to add the user to the `docker` group or provide an
existing Postgres DSN and rerun with `--skip-docker`.

On `chunky.csail.mit.edu`, prefer:

```bash
tmux new -A -s memex-sr
bash deployments/memex-sr/scripts/bootstrap_chunky.sh --install-uv
```

That wrapper refreshes Kerberos/AFS credentials only when needed,
updates submodules, and then calls the normal local bootstrap.

## Manual Verification

Set the environment:

```bash
export REPO_ROOT="$(pwd)"
export MEMEX_SR_OKG_DSN=postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT=1
```

Check deployment health:

```bash
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg doctor \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg metrics \
  --source-sync \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

Expected shape:

- at least one published generation;
- source-sync DLQ is `0`;
- `paper` count is `4,782` for the committed paper cut;
- `document_asset` nodes exist, but parsed full-text document/chunk
  coverage for papers is not expected yet.

## MCP Setup

Register the local MCP server:

```bash
codex mcp add okg-memex-sr \
  --env OKG_DSN="$MEMEX_SR_OKG_DSN" \
  --env MEMEX_SR_OKG_DSN="$MEMEX_SR_OKG_DSN" \
  --env OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments" \
  --env OKG_AGENT=1 \
  -- uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg mcp-serve \
    --dsn "$MEMEX_SR_OKG_DSN" \
    --deployment memex-sr
```

Smoke prompt for a new Codex CLI session:

```text
Use the okg-memex-sr MCP server. Call describe_graph, then answer:
what is currently in the Memex-SR graph, what is missing before full
text, and show one example paper with its authors and venue.
```

The MCP server pins to a generation when the session starts. Reconnect
after a new publish if you need the latest graph.

## How To Extend It

Every extension should follow the same substrate path:

1. Add config or source code under `deployments/memex-sr`.
2. Add ontology classes or bridge narrowings only if the existing graph
   cannot represent the data.
3. Run collection/acquisition into a local manifest or cache.
4. Publish from deterministic local inputs.
5. Verify live node/edge rows in a published generation.
6. For high-volume sources, rerun unchanged input and verify zero new
   facts.

Do not write directly to OKG live tables. Do not add edges without
bridge narrowings. Do not let publish make live network calls for
full-text parsing.

Concrete extension recipes are in
[`docs/okg-newcomer-guide.md`](docs/okg-newcomer-guide.md).

## Immediate Next Work

Do this before full-text download:

1. Corpus coverage audit for every target venue/year in `venues.yaml`.
2. Paper quality audit over duplicate DOI/title, missing authors,
   missing `published_in`, missing source records, suspicious 2026
   records, and OpenAlex main-track noise.
3. Asset URL audit that classifies every `document_asset` as verified
   PDF, landing-only, inferred-needs-verification, publisher/DOI-only,
   blocked, or operator-supplied.
4. Guardrail invariants that block bad full-text publishes.
5. A fresh local rebuild from an empty database before opening this to a
   wider collaborator group.

For acquisition planning, run:

```bash
uv --project external/okg run \
  python "$PWD/deployments/memex-sr/scripts/plan_acquisition.py" \
    --include-textbooks \
    --out /tmp/memex-sr-acquisition-plan.json
```

The current committed cut produces 7,312 plan records when enabled
textbooks are included: 2,969 `fetch_open`, 185 `queue_mit_manual`, and
4,158 `skip_metadata_only`. The next implementation step is
audit/reporting plus a downloader that consumes only `fetch_open`, not a
publisher or MIT proxy scraper.

## Known Corpus Gaps

The current paper cut has strong initial coverage for PVLDB, SIGMOD,
NSDI, OSDI, ICDE, and USENIX ATC, but weak or missing coverage for:

```text
sosp, sigcomm, hotnets, conext, eurosys, socc, mlsys, pods, cidr, edbt
```

DBLP is still planned as the authoritative venue/year enumerator, but
local shell access reset or timed out during the May 14, 2026 sampling
run. USENIX, PVLDB, and OpenAlex were used for the committed paper cut.

## Handoff Guardrails

- Treat generation `5` as the verified reference cut, not as a hardcoded
  permanent generation.
- Treat `document_asset` as URL/provenance hints, not local full text.
- Keep live-count/operator docs out of `doc-corpus`; the source indexes
  stable design/context docs so a publish does not chase its own
  generation numbers.
- Keep `external/okg` pinned to the intended `dev` commit.
- Keep source/network work outside publish; publish should consume
  manifests and local cached assets.
- Keep collaborator changes deployment-owned unless a real substrate
  change is needed.
