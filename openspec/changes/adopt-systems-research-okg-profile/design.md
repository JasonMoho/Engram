## Context

OKG now owns the reusable systems-research deployment archetype. The new
`systems-research` profile composes shared ontology modules, source
defaults, invariants, dashboards, and profile metadata. It also ships
the `systems_research` and `engram_runs` ontology/source modules that
Engram previously had to approximate locally.

Engram should become a consumer of that profile rather than a fork of
deployment logic. Engram still owns benchmark-specific configuration,
run locations, local paper-cut and venue overrides, collaborator docs,
and benchmark harness integration.

## Goals / Non-Goals

**Goals:**

- Use the OKG `systems-research` profile as the source of truth for the
  Memex-SR deployment shape.
- Keep the old deployment available as `deployments/memex-sr.old/` until
  diffs and first publish are verified.
- Add Engram run ingestion through profile overrides rather than local
  source implementations.
- Preserve local paper-cut and venue inputs.
- Update handoff docs so collaborators can bootstrap with one profile
  command.

**Non-Goals:**

- Do not modify OKG substrate code from Engram.
- Do not reimplement OKG's `systems_research`, `engram_runs`, or
  `context_packet` modules locally.
- Do not require a full publish if local Postgres is unavailable during
  the repo migration. Record the exact deferred commands instead.

## Decisions

1. **Pin, do not vendor.**

   Engram pins `external/okg` to commit `06408507` or the requested
   branch tip. The shared profile and ontology/source implementations
   remain in OKG.

2. **Archive before replacing.**

   Move the existing hand-rolled deployment to
   `deployments/memex-sr.old/`. This keeps local docs, manifests,
   scripts, and reports available for diffing and for any follow-on
   migration of useful Engram-only artifacts.

3. **Use profile-init as the source of truth, with a temporary CLI
   workaround.**

   The intended command is:

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

   At OKG commit `06408507`, the public CLI path has an argparse
   collision on the profile's `deployment_name` question and crashes
   before it can parse arguments. Engram therefore scaffolds the same
   profile through OKG's `profile_init` library shim until the upstream
   CLI collision fix lands.

4. **Use overrides for Engram-specific run ingestion.**

   The profile stays general. The current OKG manifest loader does not
   consume `modules_extra` or `source_registry_extra`, so Engram applies
   the override directly in the generated files: append `engram_runs` to
   `deployment.yaml.modules` and add the five Engram run artifact
   adapters to `source_registry.yaml`, with `runs_dir` pointing at
   Engram results.

5. **Keep publish offline.**

   The profile's OpenAlex default is retained only as a registry note in
   Engram. Publish reads the local paper-cut manifest and local docs; it
   must not make live OpenAlex or publisher requests.

6. **Context packets come from MCP.**

   Agent integration should move from file-read packet injection to the
   OKG MCP `generate_context_packet` tool once the deployment is live.
   The generated markdown still carries pinned-generation provenance and
   evidence ids.

## Risks / Trade-offs

- Profile drift -> Pin the submodule and record the commit in docs.
- Local overrides lost -> Keep `memex-sr.old` for diffing until first
  publish and Engram run ingestion are verified.
- Publish not available locally -> Treat `okg init` and catalog compile
  as repo migration verification; leave migrate/publish commands in
  handoff docs for the target machine.
- Old phase0 DB migration may fail -> OKG commit `06408507` does not
  create default branch rows for existing `graph_generations` before it
  promotes `branch_id` to NOT NULL. Verify against a fresh DB and record
  the old-DB backfill blocker in the handoff.
- Derived-artifact registration gap -> Document the known OKG follow-on;
  the MCP tool can render directly until catalog-apply registers the
  persistent definition.
