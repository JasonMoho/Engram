#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash deployments/memex-sr/scripts/bootstrap_local.sh [options]

Options:
  --check-only    Check prerequisites and exit.
  --install-uv    Install uv into ~/.local/bin if uv is missing.
  --skip-docker   Do not start local Docker Postgres. Use MEMEX_SR_OKG_DSN
                  as an already-running Postgres with OKG extensions.
  -h, --help      Show this help.

Environment:
  MEMEX_SR_OKG_DSN   Default:
                     postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
  MEMEX_SR_OKG_DB    Database name for the local Docker Postgres path.
  OKG_AGENT          Defaults to 1.
EOF
}

CHECK_ONLY=0
INSTALL_UV=0
USE_DOCKER=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=1
      ;;
    --install-uv)
      INSTALL_UV=1
      ;;
    --skip-docker)
      USE_DOCKER=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
OKG_DIR="$REPO_ROOT/external/okg"
DB_NAME="${MEMEX_SR_OKG_DB:-engram_memex_sr_phase0}"
export MEMEX_SR_OKG_DSN="${MEMEX_SR_OKG_DSN:-postgres://postgres:okg@127.0.0.1:5433/$DB_NAME}"
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT="${OKG_AGENT:-1}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

have() {
  command -v "$1" >/dev/null 2>&1
}

if [[ -f "$HOME/.local/bin/env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.local/bin/env"
else
  export PATH="$HOME/.local/bin:$PATH"
fi

install_uv() {
  if have curl; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif have python3; then
    python3 -m pip install --user uv
  else
    die "cannot install uv automatically: neither curl nor python3 is available"
  fi

  if [[ -f "$HOME/.local/bin/env" ]]; then
    # shellcheck disable=SC1091
    source "$HOME/.local/bin/env"
  fi
  export PATH="$HOME/.local/bin:$PATH"
}

if [[ ! -d "$OKG_DIR/src/okg" ]]; then
  die "OKG submodule is missing. Run: git submodule update --init --recursive"
fi

if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]]; then
  die "MEMEX_SR_OKG_DB must contain only letters, numbers, and underscores; got: $DB_NAME"
fi

if ! have uv; then
  if [[ "$INSTALL_UV" -eq 1 ]]; then
    echo "uv is missing; installing into ~/.local/bin..."
    install_uv
  else
    cat >&2 <<'EOF'
ERROR: uv is required to run the OKG CLI from external/okg.

Install it with one of:
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.local/bin/env"

or rerun this script with:
  bash deployments/memex-sr/scripts/bootstrap_local.sh --install-uv
EOF
    exit 1
  fi
fi

if [[ "$USE_DOCKER" -eq 1 ]]; then
  if ! have docker; then
    cat >&2 <<'EOF'
ERROR: docker is required for the default local OKG Postgres stack.

Options:
  1. Install Docker / ask an admin to make Docker available.
  2. Use an existing Postgres with OKG extensions and rerun with --skip-docker:
       MEMEX_SR_OKG_DSN=postgres://USER:PASS@HOST:PORT/DB \
         bash deployments/memex-sr/scripts/bootstrap_local.sh --skip-docker
EOF
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    cat >&2 <<EOF
ERROR: docker is installed, but this user cannot talk to the Docker daemon.

Current user:
  $(id)

Fix options:
  1. Ask an admin to add you to the docker group, then log out and back in:
       sudo usermod -aG docker "$USER"

  2. Run against an existing Postgres with the required OKG extensions:
       MEMEX_SR_OKG_DSN=postgres://USER:PASS@HOST:PORT/DB \\
         bash deployments/memex-sr/scripts/bootstrap_local.sh --skip-docker

The required extensions are:
  btree_gist, fuzzystrmatch, pg_textsearch, pg_trgm, timescaledb, vector
EOF
    exit 1
  fi

  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "Preflight checks passed."
    exit 0
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
    die "Postgres did not become ready within 120 seconds"
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
else
  cat <<EOF
Skipping Docker. Using existing Postgres:
  $MEMEX_SR_OKG_DSN

The target database must already exist and have these extensions:
  btree_gist, fuzzystrmatch, pg_textsearch, pg_trgm, timescaledb, vector
EOF
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "Preflight checks passed."
    exit 0
  fi
fi

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
