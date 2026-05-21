## 1. Profile Pin And Init

- [x] 1.1 Pin `external/okg` to `06408507`. Verification: `git
  submodule status external/okg` reports the pinned commit.
- [x] 1.2 Archive the old hand-rolled deployment. Verification:
  `deployments/memex-sr.old/deployment.yaml`,
  `deployments/memex-sr.old/source_registry.yaml`,
  `deployments/memex-sr.old/manifests/paper_cut.json`, and
  `deployments/memex-sr.old/venues.yaml` exist.
- [x] 1.3 Generate the deployment from the `systems-research` profile
  with the paper cut and venues overrides. Use `okg init --profile
  systems-research` once the OKG CLI collision is fixed; until then use
  the Engram profile-init shim. Verification: new
  `deployments/memex-sr/deployment.yaml`,
  `deployments/memex-sr/source_registry.yaml`,
  `deployments/memex-sr/invariants.yaml`, and
  `deployments/memex-sr/dashboards/` exist.

## 2. Engram Overrides

- [x] 2.1 Add `engram_runs` as an Engram-specific module override.
  Verification: the generated deployment includes `engram_runs` in the
  effective `modules:` list consumed by OKG catalog composition.
- [x] 2.2 Add the five Engram run artifact source overrides.
  Verification: `source_registry.yaml` references research digest,
  experiment result, candidate solution, final result, and agent summary
  adapters with the configured `runs_dir`.

## 3. Docs And Context Packet Handoff

- [x] 3.1 Replace the old multi-step `HANDOFF.md` bootstrap section with
  the profile-driven `okg init` flow. Verification: a fresh reader can
  find the one-command init path, migrate/catalog/publish commands,
  profile diagnostics expectations, and extension guidance.
- [x] 3.2 Update context-packet integration docs to reference the MCP
  `generate_context_packet` tool. Verification: docs show the tool
  arguments and explain that evidence ids resolve through OKG MCP
  `get_node`.

## 4. Verification

- [x] 4.1 Validate the Engram OpenSpec change. Verification:
  `openspec validate adopt-systems-research-okg-profile --strict`
  passes.
- [x] 4.2 Run available profile setup checks. Verification: `okg init`
  completes locally, or any blocker is recorded with the exact failing
  command and preserved generated/old files.
- [x] 4.3 Leave publish verification commands for the deployment machine.
  Verification: `HANDOFF.md` includes `okg migrate`, `okg catalog
  load --apply`, `okg ingest`, `okg doctor`, `okg metrics`, and MCP
  `generate_context_packet` checks.
