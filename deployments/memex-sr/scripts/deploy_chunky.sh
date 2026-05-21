#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash deployments/memex-sr/scripts/deploy_chunky.sh [options]

One-command Memex-SR deployment/update path for chunky.csail.mit.edu.

Default behavior:
  1. Ensure the checkout lives on local disk.
  2. Fetch/switch/pull the configured Engram branch.
  3. Update submodules.
  4. Refresh CSAIL Kerberos/AFS credentials.
  5. Bootstrap/migrate/catalog-load/publish Memex-SR.
  6. Generate a Cloudcast context packet from the latest generation.

Options:
  --checkout-dir PATH      Default: /data1/$USER/projects/mit/Engram
  --branch NAME            Default: codex/systems-researcher-okg
  --origin-url URL         Default: https://github.com/mit-nms/Engram.git
  --fork-url URL           Default: https://github.com/JasonMoho/Engram.git
  --remote NAME            Remote to pull the branch from. Default: fork
  --db-name NAME           Default: engram_memex_sr_phase0
  --dsn DSN                Override MEMEX_SR_OKG_DSN.
  --check-only             Run auth/dependency preflight only.
  --install-uv             Install uv into ~/.local/bin if missing.
  --skip-auth              Skip kinit/aklog preflight.
  --skip-docker            Use an existing Postgres from --dsn/MEMEX_SR_OKG_DSN.
  --no-update              Do not fetch/switch/pull the checkout.
  --no-relocate            Run in the current checkout even if not on local disk.
  --no-packet              Skip Cloudcast context-packet generation.
  -h, --help               Show this help.

Examples:
  bash deployments/memex-sr/scripts/deploy_chunky.sh --install-uv
  bash deployments/memex-sr/scripts/deploy_chunky.sh --check-only
EOF
}

CHECKOUT_DIR="${MEMEX_SR_CHECKOUT_DIR:-/data1/${USER:-$(id -un)}/projects/mit/Engram}"
BRANCH="${MEMEX_SR_BRANCH:-codex/systems-researcher-okg}"
ORIGIN_URL="${MEMEX_SR_ORIGIN_URL:-https://github.com/mit-nms/Engram.git}"
FORK_URL="${MEMEX_SR_FORK_URL:-https://github.com/JasonMoho/Engram.git}"
REMOTE="${MEMEX_SR_REMOTE:-fork}"
DB_NAME="${MEMEX_SR_OKG_DB:-engram_memex_sr_phase0}"
CHECK_ONLY=0
INSTALL_UV=0
SKIP_AUTH=0
SKIP_DOCKER=0
UPDATE=1
RELOCATE=1
GENERATE_PACKET=1
DSN_OVERRIDE="${MEMEX_SR_OKG_DSN:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --checkout-dir)
      [[ $# -ge 2 ]] || { echo "ERROR: --checkout-dir requires a value" >&2; exit 2; }
      CHECKOUT_DIR="$2"
      shift
      ;;
    --branch)
      [[ $# -ge 2 ]] || { echo "ERROR: --branch requires a value" >&2; exit 2; }
      BRANCH="$2"
      shift
      ;;
    --origin-url)
      [[ $# -ge 2 ]] || { echo "ERROR: --origin-url requires a value" >&2; exit 2; }
      ORIGIN_URL="$2"
      shift
      ;;
    --fork-url)
      [[ $# -ge 2 ]] || { echo "ERROR: --fork-url requires a value" >&2; exit 2; }
      FORK_URL="$2"
      shift
      ;;
    --remote)
      [[ $# -ge 2 ]] || { echo "ERROR: --remote requires a value" >&2; exit 2; }
      REMOTE="$2"
      shift
      ;;
    --db-name)
      [[ $# -ge 2 ]] || { echo "ERROR: --db-name requires a value" >&2; exit 2; }
      DB_NAME="$2"
      shift
      ;;
    --dsn)
      [[ $# -ge 2 ]] || { echo "ERROR: --dsn requires a value" >&2; exit 2; }
      DSN_OVERRIDE="$2"
      shift
      ;;
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
    --no-update)
      UPDATE=0
      ;;
    --no-relocate)
      RELOCATE=0
      ;;
    --no-packet)
      GENERATE_PACKET=0
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
CURRENT_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
CHECKOUT_DIR="$(python3 -c 'import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$CHECKOUT_DIR")"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

remote_exists() {
  git -C "$1" remote get-url "$2" >/dev/null 2>&1
}

ensure_checkout() {
  local target="$1"
  if [[ -d "$target/.git" ]]; then
    return
  fi
  if [[ -e "$target" ]]; then
    die "$target exists but is not a git checkout"
  fi
  mkdir -p "$(dirname "$target")"
  echo "Cloning Engram into $target"
  git clone --recurse-submodules "$ORIGIN_URL" "$target"
}

update_checkout() {
  local target="$1"

  if ! remote_exists "$target" origin; then
    git -C "$target" remote add origin "$ORIGIN_URL"
  fi
  if ! remote_exists "$target" fork; then
    git -C "$target" remote add fork "$FORK_URL"
  fi

  git -C "$target" fetch "$REMOTE" "$BRANCH"
  if git -C "$target" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
    git -C "$target" switch "$BRANCH"
  else
    git -C "$target" switch -c "$BRANCH" --track "$REMOTE/$BRANCH"
  fi
  git -C "$target" pull --ff-only "$REMOTE" "$BRANCH"
  git -C "$target" submodule update --init --recursive
}

forward_args=(
  --checkout-dir "$CHECKOUT_DIR"
  --branch "$BRANCH"
  --origin-url "$ORIGIN_URL"
  --fork-url "$FORK_URL"
  --remote "$REMOTE"
  --db-name "$DB_NAME"
  --no-relocate
)
[[ "$CHECK_ONLY" -eq 1 ]] && forward_args+=(--check-only)
[[ "$INSTALL_UV" -eq 1 ]] && forward_args+=(--install-uv)
[[ "$SKIP_AUTH" -eq 1 ]] && forward_args+=(--skip-auth)
[[ "$SKIP_DOCKER" -eq 1 ]] && forward_args+=(--skip-docker)
[[ "$UPDATE" -eq 0 ]] && forward_args+=(--no-update)
[[ "$GENERATE_PACKET" -eq 0 ]] && forward_args+=(--no-packet)
[[ -n "$DSN_OVERRIDE" ]] && forward_args+=(--dsn "$DSN_OVERRIDE")

if [[ "$RELOCATE" -eq 1 && "$CURRENT_ROOT" != "$CHECKOUT_DIR" ]]; then
  ensure_checkout "$CHECKOUT_DIR"
  if [[ "$UPDATE" -eq 1 ]]; then
    update_checkout "$CHECKOUT_DIR"
  fi
  echo "Continuing from local-disk checkout: $CHECKOUT_DIR"
  exec bash "$CHECKOUT_DIR/deployments/memex-sr/scripts/deploy_chunky.sh" "${forward_args[@]}"
fi

if [[ "$UPDATE" -eq 1 ]]; then
  update_checkout "$CURRENT_ROOT"
fi

export MEMEX_SR_OKG_DB="$DB_NAME"
if [[ -n "$DSN_OVERRIDE" ]]; then
  export MEMEX_SR_OKG_DSN="$DSN_OVERRIDE"
else
  export MEMEX_SR_OKG_DSN="${MEMEX_SR_OKG_DSN:-postgres://postgres:okg@127.0.0.1:5433/$DB_NAME}"
fi
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$CURRENT_ROOT/deployments"
export OKG_AGENT="${OKG_AGENT:-1}"

bootstrap_args=()
[[ "$CHECK_ONLY" -eq 1 ]] && bootstrap_args+=(--check-only)
[[ "$INSTALL_UV" -eq 1 ]] && bootstrap_args+=(--install-uv)
[[ "$SKIP_AUTH" -eq 1 ]] && bootstrap_args+=(--skip-auth)
[[ "$SKIP_DOCKER" -eq 1 ]] && bootstrap_args+=(--skip-docker)
bootstrap_args+=(--skip-submodules)

bash "$CURRENT_ROOT/deployments/memex-sr/scripts/bootstrap_chunky.sh" "${bootstrap_args[@]}"

if [[ "$CHECK_ONLY" -eq 1 || "$GENERATE_PACKET" -eq 0 ]]; then
  exit 0
fi

packet_dir="$CURRENT_ROOT/deployments/memex-sr/reports/cloudcast-ab"
packet_path="$packet_dir/context-packet-chunky.md"
metadata_path="$packet_dir/context-packet-chunky.metadata.json"
mkdir -p "$packet_dir"

echo "Generating Cloudcast context packet..."
uv --directory "$CURRENT_ROOT/external/okg" run --extra mcp python \
  "$CURRENT_ROOT/deployments/memex-sr/scripts/generate_cloudcast_context_packet.py" \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --output "$packet_path" \
  --metadata-output "$metadata_path"

cat <<EOF

Memex-SR chunky deployment is ready.

Checkout:
  $CURRENT_ROOT

Database:
  $MEMEX_SR_OKG_DSN

Cloudcast packet:
  $packet_path
  $metadata_path

Useful follow-up:
  cd "$CURRENT_ROOT"
  export MEMEX_SR_OKG_DSN="$MEMEX_SR_OKG_DSN"
  export OKG_DSN="\$MEMEX_SR_OKG_DSN"
  export OKG_DEPLOYMENTS_DIR="$CURRENT_ROOT/deployments"
EOF
