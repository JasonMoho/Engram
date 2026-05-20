#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash deployments/memex-sr/scripts/chunky_auth.sh [options]

Refresh CSAIL Kerberos and AFS credentials for work on chunky.

Options:
  --principal NAME   Kerberos principal. Default: $MEMEX_SR_KRB_PRINCIPAL
                     or "$USER@CSAIL.MIT.EDU".
  --check-only       Report current credential state without prompting.
  -h, --help         Show this help.

Notes:
  This does not bypass Duo, Kerberos, or CSAIL policy. It only avoids
  repeated manual kinit/aklog commands once you are logged in.
EOF
}

CHECK_ONLY=0
PRINCIPAL="${MEMEX_SR_KRB_PRINCIPAL:-${USER:-$(id -un)}@CSAIL.MIT.EDU}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --principal)
      [[ $# -ge 2 ]] || { echo "ERROR: --principal requires a value" >&2; exit 2; }
      PRINCIPAL="$2"
      shift
      ;;
    --check-only)
      CHECK_ONLY=1
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

have() {
  command -v "$1" >/dev/null 2>&1
}

if ! have klist || ! have kinit; then
  echo "WARN: klist/kinit not found; Kerberos preflight skipped." >&2
else
  if klist -s; then
    echo "Kerberos ticket is present."
  elif [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "ERROR: no Kerberos ticket. Run: kinit $PRINCIPAL" >&2
    exit 1
  else
    echo "No Kerberos ticket found; running kinit for $PRINCIPAL"
    kinit "$PRINCIPAL"
  fi
fi

if have aklog; then
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    if have tokens; then
      tokens || true
    fi
  else
    echo "Refreshing AFS token for csail.mit.edu..."
    aklog csail.mit.edu
    if have tokens; then
      tokens || true
    fi
  fi
else
  echo "WARN: aklog not found; AFS token refresh skipped." >&2
fi

if [[ "${HOME:-}" == /afs/* ]]; then
  probe="$HOME/.memex-sr-afs-probe.$$"
  if mkdir "$probe" 2>/dev/null; then
    rmdir "$probe"
    echo "AFS home is writable."
  else
    cat >&2 <<EOF
ERROR: AFS home is not writable.

This usually means you have no valid AFS token. Run:
  kinit $PRINCIPAL
  aklog csail.mit.edu

Then retry this script.
EOF
    exit 1
  fi
fi

echo "CSAIL auth preflight passed."
