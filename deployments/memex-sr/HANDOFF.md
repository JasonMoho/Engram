# Memex-SR Handoff

Memex-SR is Engram's OKG deployment for an autonomous systems
researcher. It consumes OKG's upstream `systems-research` profile and
adds Engram-specific run ingestion.

## What Is In This Deployment

- Systems/database paper metadata from the committed paper-cut manifest.
- Local Memex-SR design, source-ingestion, Cloudcast, and handoff docs.
- The `systems_research` ontology: `DesignPrinciple`, `Mechanism`,
  `TradeOff`, and `AntiPattern`.
- The `engram_runs` ontology and five run-artifact sources for
  `research_journal.md`, `score.txt`, `snapshot.*`,
  `final_result.json`, and `agent_*_summary.json`.
- A context-packet MCP path via OKG's `generate_context_packet` tool.

The previous hand-rolled deployment is preserved at
`deployments/memex-sr.old/` for diff reference until the migration is
fully verified.

## Fresh Setup

From the Engram repo root:

```bash
git submodule update --init --recursive
cd external/okg
git fetch origin
git checkout 06408507
cd ../..
```

The deployment has already been scaffolded from the profile. To recreate
it after OKG fixes the profile CLI collision, the intended command is:

```bash
uv --directory external/okg run --extra mcp okg init \
  --profile systems-research \
  --deployment-name memex-sr \
  --postgres-dsn postgres://postgres:okg@localhost:5433/engram_memex_sr_phase0 \
  --paper-cut-manifest "$(pwd)/deployments/memex-sr/manifests/paper_cut.json" \
  --venues-file "$(pwd)/deployments/memex-sr/venues.yaml" \
  --mcp-port 5430 \
  --no-publish
```

At OKG commit `06408507`, that exact CLI path crashes because the
dynamic profile-flag injector collides on `--deployment-name`. Until
that upstream fix lands, use the Engram shim, which calls the same OKG
profile-init library:

```bash
uv --directory external/okg run --extra mcp \
  python ../deployments/memex-sr/scripts/init_systems_research_profile.py \
  --force
```

After regeneration, reapply the Engram hardening in this checkout:
`engram_runs` in `deployment.yaml`, the five Engram run sources in
`source_registry.yaml`, local `paper_cut` paths, `doc_corpus`
`repo_root` / `extractors_dir`, and OpenAlex as `registry_only`.

## Local Publish

Set the local DSN:

```bash
export REPO_ROOT="$(pwd)"
export MEMEX_SR_OKG_DSN=postgres://postgres:okg@localhost:5433/engram_memex_sr_phase0
export OKG_DSN="$MEMEX_SR_OKG_DSN"
export OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments"
export OKG_AGENT=1
```

Then run:

```bash
uv --directory external/okg run --extra mcp okg migrate \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply

uv --directory external/okg run --extra mcp okg catalog load \
  --deployment deployments/memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --apply

uv --directory external/okg run --extra mcp okg ingest \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --inline \
  --progress
```

`okg ingest` runs the configured sources and publishes between source
dependency groups. `okg run --once` alone only publishes already-staged
facts, so it is expected to return `no_op` on a fresh database before
source ingestion. Publish must consume local files only. OpenAlex is
intentionally registry-only here; the offline manifest builder can
refresh `manifests/paper_cut.json`, but OKG publish should not hit live
literature services.

## Verification

```bash
uv --directory external/okg run --extra mcp okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

uv --directory external/okg run --extra mcp okg doctor \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json

uv --directory external/okg run --extra mcp okg metrics \
  --source-sync \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

Expected shape:

- a published generation;
- nonzero `paper` nodes from the paper cut;
- no RED doctor findings;
- source-sync DLQ at `0`;
- after Engram writes runs under `results/`, nonzero
  `ResearchDigest`, `ExperimentResult`, `CandidateSolution`,
  `FinalResult`, and `AgentSummary` nodes.

## Known OKG Gaps At 06408507

- `okg init --profile systems-research` has a profile flag collision on
  `--deployment-name`; use the shim above until OKG fixes the CLI.
- Migrating an older pre-branch database can fail with
  `graph_generations.branch_id contains null values`. A fresh database
  works. Existing databases need the OKG branch-backfill fix or a manual
  default-branch backfill before running `okg migrate`.
- `generate_context_packet` renders through MCP directly. Persistent
  derived-artifact catalog registration is an OKG follow-on.

## MCP

Register the graph for Codex:

```bash
codex mcp add okg-memex-sr \
  --env OKG_DSN="$MEMEX_SR_OKG_DSN" \
  --env OKG_DEPLOYMENTS_DIR="$REPO_ROOT/deployments" \
  --env OKG_AGENT=1 \
  -- uv --directory "$REPO_ROOT/external/okg" run --extra mcp okg mcp-serve \
    --dsn "$MEMEX_SR_OKG_DSN" \
    --deployment memex-sr
```

Smoke prompt:

```text
Use the okg-memex-sr MCP server. Call describe_graph, then generate a
context packet for problem_name=cloudcast, domain=networking,
topic_slugs=["multicast", "routing"], evidence_budget=20, token_budget=4000.
Pick one evidence id from the packet and resolve it with get_node.
```

## How To Extend

- New ontology that is generally useful belongs upstream in
  `external/okg/src/okg/substrate/library/ontologies/<module>/`.
- Engram-only source configuration belongs in this deployment's
  `source_registry.yaml`.
- New reusable source adapters belong upstream under
  `external/okg/src/okg/substrate/library/sources/<module>/`.
- New corpus inputs should enter through deterministic manifests or
  local caches, then publish through OKG source adapters.
- Do not write directly to OKG live tables, and do not add graph edges
  without catalog narrowings.
