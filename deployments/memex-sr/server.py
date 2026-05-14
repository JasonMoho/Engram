from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OKG_SRC = REPO_ROOT / "external" / "okg" / "src"

if str(OKG_SRC) not in sys.path:
    sys.path.insert(0, str(OKG_SRC))

os.environ.setdefault("OKG_DEPLOYMENTS_DIR", str(REPO_ROOT / "deployments"))


def main() -> None:
    from okg.substrate.mcp.deployment_entry import run_for_deployment

    run_for_deployment("memex-sr")


if __name__ == "__main__":
    main()
