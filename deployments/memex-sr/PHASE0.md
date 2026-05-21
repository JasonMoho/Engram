# Memex-SR Local Setup

This setup runs Memex-SR as an external OKG deployment owned by Engram.
It uses the OKG submodule under `external/okg` and a local Postgres
database named `engram_memex_sr_phase0`. The current local cut indexes
both the Memex-SR design corpus and a manifest-backed paper metadata
cut. Parsed full text is not in the graph yet.

Run all commands from the Engram repo root.

## One-Command Bootstrap

```bash
git submodule update --init --recursive
bash deployments/memex-sr/scripts/bootstrap_local.sh
```

The script starts the OKG local Postgres compose stack, creates the
Memex-SR database if needed, loads extensions, migrates schema, loads
the catalog, publishes the committed local cut, and prints deployment
status.

Preflight only:

```bash
bash deployments/memex-sr/scripts/bootstrap_local.sh --check-only
```

If `uv` is missing:

```bash
bash deployments/memex-sr/scripts/bootstrap_local.sh --install-uv
```

If Docker is installed but your user cannot access the Docker daemon,
ask an admin to add you to the `docker` group and then log out and back
in:

```bash
sudo usermod -aG docker "$USER"
```

If you need to use an existing Postgres instead of local Docker, create
a database with the required OKG extensions and run:

```bash
export MEMEX_SR_OKG_DSN=postgres://USER:PASS@HOST:PORT/DB
bash deployments/memex-sr/scripts/bootstrap_local.sh --skip-docker
```

## Environment

```bash
export REPO_ROOT="$(pwd)"
export MEMEX_SR_OKG_DSN=postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT=1
```

## Manual Build

```bash
export REPO_ROOT="$(pwd)"
docker compose -f "$REPO_ROOT/external/okg/ops/pg/docker-compose.yaml" up -d --build
docker exec okg-pg createdb -U postgres engram_memex_sr_phase0 2>/dev/null || true
docker exec okg-pg psql -U postgres -d engram_memex_sr_phase0 -v ON_ERROR_STOP=1 \
  -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;' \
  -c 'CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;' \
  -c 'CREATE EXTENSION IF NOT EXISTS pg_textsearch;' \
  -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' \
  -c 'CREATE EXTENSION IF NOT EXISTS timescaledb;' \
  -c 'CREATE EXTENSION IF NOT EXISTS vector;'
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg migrate \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg catalog load \
  --deployment "$REPO_ROOT/deployments/memex-sr" \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg doctor \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --check sources \
  --json
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --inline \
  --progress \
  --json
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

To regenerate and publish the paper cut explicitly:

```bash
uv --directory "$REPO_ROOT/external/okg" run --extra mcp \
  python "$REPO_ROOT/deployments/memex-sr/scripts/collect_paper_cut.py"
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg catalog load \
  --deployment "$REPO_ROOT/deployments/memex-sr" \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json
uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --include paper_cut \
  --mode scope_complete \
  --inline \
  --progress \
  --json
```

The verified local generation-5 cut contains 4,782 paper nodes. A clean
rebuild may publish a different generation id, but the paper count
should match unless the manifest changed. See
[`docs/pre-full-text-readiness.md`](docs/pre-full-text-readiness.md)
for the current graph counts, coverage gaps, no-op incremental check,
and the work that must happen before full-text acquisition.

## Codex CLI MCP

Register the server with Codex CLI:

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

From a Codex CLI session opened in this repository, query the server with:

```text
Use the okg-memex-sr MCP server. Call describe_graph, then search for
"systems researcher", "corpus packs", and "Engram agent".
```

The MCP server is stdio-based; Codex CLI starts it on demand from the
registered `codex mcp` command.
