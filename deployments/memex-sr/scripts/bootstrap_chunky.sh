#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash deployments/memex-sr/scripts/bootstrap_chunky.sh [options]

CSAIL chunky wrapper around bootstrap_local.sh.

Options:
  --check-only    Check auth and prerequisites; do not start Postgres.
  --install-uv    Install uv into ~/.local/bin if uv is missing.
  --skip-auth     Do not run chunky_auth.sh first.
  --skip-docker   Use MEMEX_SR_OKG_DSN instead of local Docker Postgres.
  -h, --help      Show this help.

Environment:
  MEMEX_SR_KRB_PRINCIPAL  Kerberos principal for chunky_auth.sh.
  MEMEX_SR_OKG_DSN        Existing Postgres DSN when --skip-docker is used.
  MEMEX_SR_OKG_DB         Docker Postgres database name.
EOF
}

CHECK_ONLY=0
INSTALL_UV=0
SKIP_AUTH=0
SKIP_DOCKER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=1
      ;;
    --install-uv)
      INSTALL_UV=1
      ;;
    --skip-auth)
      SKIP_AUTH=1
      ;;
    --skip-docker)
      SKIP_DOCKER=1
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

if [[ "$SKIP_AUTH" -eq 0 ]]; then
  auth_args=()
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    auth_args+=(--check-only)
  fi
  bash "$SCRIPT_DIR/chunky_auth.sh" "${auth_args[@]}"
fi

if [[ "$REPO_ROOT" == /afs/* ]]; then
  cat >&2 <<EOF
WARN: this checkout is under AFS:
  $REPO_ROOT

For long Memex-SR runs, a local disk checkout is less painful:
  /data1/$USER/Engram

AFS is fine for small edits, but local disk avoids failed writes when
tokens expire during long downloads/parses.
EOF
fi

echo "Updating submodules..."
git -C "$REPO_ROOT" submodule update --init --recursive

bootstrap_args=()
if [[ "$CHECK_ONLY" -eq 1 ]]; then
  bootstrap_args+=(--check-only)
fi
if [[ "$INSTALL_UV" -eq 1 ]]; then
  bootstrap_args+=(--install-uv)
fi
if [[ "$SKIP_DOCKER" -eq 1 ]]; then
  bootstrap_args+=(--skip-docker)
fi

export MEMEX_SR_OKG_DB="${MEMEX_SR_OKG_DB:-engram_memex_sr_phase0}"
export OKG_AGENT="${OKG_AGENT:-1}"

bash "$SCRIPT_DIR/bootstrap_local.sh" "${bootstrap_args[@]}"
