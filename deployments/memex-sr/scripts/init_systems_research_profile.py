#!/usr/bin/env python3
"""Scaffold Memex-SR from OKG's systems-research profile.

This is a temporary Engram-side shim for OKG commit 06408507, where
`okg init --profile systems-research` has an argparse collision on
`--deployment-name`. It calls the same OKG profile-init library used by
the CLI and writes the same generated files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from okg.substrate.deployment_bootstrap.profile_init import (
    build_plan,
    discover_profile,
    scaffold_deployment,
)


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-name", default="memex-sr")
    parser.add_argument(
        "--postgres-dsn",
        default="postgres://postgres:okg@localhost:5433/engram_memex_sr_phase0",
    )
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--paper-cut-manifest", type=Path)
    parser.add_argument("--venues-file", type=Path)
    parser.add_argument("--mcp-port", type=int, default=5430)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    paper_cut_manifest = (
        args.paper_cut_manifest
        or repo_root / "deployments" / args.deployment_name / "manifests" / "paper_cut.json"
    )
    venues_file = (
        args.venues_file
        or repo_root / "deployments" / args.deployment_name / "venues.yaml"
    )

    profile = discover_profile("systems-research")
    plan = build_plan(
        profile=profile,
        deployment_name=args.deployment_name,
        deployments_root=repo_root / "deployments",
        raw_answers={
            "deployment_name": args.deployment_name,
            "postgres_dsn": args.postgres_dsn,
            "paper_cut_manifest": str(paper_cut_manifest),
            "venues_file": str(venues_file),
            "mcp_port": args.mcp_port,
        },
    )
    result = scaffold_deployment(plan, force=args.force)
    print(f"scaffolded {result.deployment_dir}")
    for path in result.files_written:
        print(path.relative_to(repo_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
