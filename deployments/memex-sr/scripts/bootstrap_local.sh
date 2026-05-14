#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
OKG_DIR="$REPO_ROOT/external/okg"
DB_NAME="${MEMEX_SR_OKG_DB:-engram_memex_sr_phase0}"
export MEMEX_SR_OKG_DSN="${MEMEX_SR_OKG_DSN:-postgres://postgres:okg@127.0.0.1:5433/$DB_NAME}"
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT="${OKG_AGENT:-1}"

if [[ ! -d "$OKG_DIR/src/okg" ]]; then
  echo "OKG submodule is missing. Run: git submodule update --init --recursive" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for the local OKG Postgres stack" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to run the OKG CLI from external/okg" >&2
  exit 1
fi

echo "Starting OKG local Postgres..."
docker compose -f "$OKG_DIR/ops/pg/docker-compose.yaml" up -d --build

echo "Waiting for Postgres..."
for _ in {1..60}; do
  if docker exec okg-pg pg_isready -U postgres -d okg >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! docker exec okg-pg pg_isready -U postgres -d okg >/dev/null 2>&1; then
  echo "Postgres did not become ready within 120 seconds" >&2
  exit 1
fi

echo "Creating database $DB_NAME if needed..."
if ! docker exec okg-pg psql -U postgres -d postgres -Atc \
  "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';" | grep -qx "1"; then
  docker exec okg-pg createdb -U postgres "$DB_NAME"
fi

echo "Installing per-database extensions..."
docker exec okg-pg psql -U postgres -d "$DB_NAME" -v ON_ERROR_STOP=1 \
  -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;' \
  -c 'CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;' \
  -c 'CREATE EXTENSION IF NOT EXISTS pg_textsearch;' \
  -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' \
  -c 'CREATE EXTENSION IF NOT EXISTS timescaledb;' \
  -c 'CREATE EXTENSION IF NOT EXISTS vector;'

echo "Migrating OKG schema..."
uv --directory "$OKG_DIR" run --extra mcp okg migrate \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json

echo "Loading Memex-SR catalog..."
uv --directory "$OKG_DIR" run --extra mcp okg catalog load \
  --deployment "$REPO_ROOT/deployments/memex-sr" \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply \
  --json

echo "Checking sources..."
uv --directory "$OKG_DIR" run --extra mcp okg doctor \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --check sources \
  --json

echo "Publishing committed local cut..."
uv --directory "$OKG_DIR" run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --inline \
  --progress \
  --json

echo "Current deployment status:"
uv --directory "$OKG_DIR" run --extra mcp okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

cat <<EOF

Memex-SR local OKG is ready.

Environment for follow-up commands:
  export MEMEX_SR_OKG_DSN="$MEMEX_SR_OKG_DSN"
  export OKG_DSN="\$MEMEX_SR_OKG_DSN"
  export OKG_DEPLOYMENTS_DIR="$OKG_DEPLOYMENTS_DIR"
  export OKG_AGENT=1
EOF
