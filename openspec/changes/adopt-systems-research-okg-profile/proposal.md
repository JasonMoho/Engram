## Why

Why is this broken?

The current Memex-SR deployment is hand-rolled in Engram. Its setup
requires a multi-step local recipe, local ontology overlays, local source
registry wiring, and local documentation that duplicates OKG substrate
decisions. OKG now ships a portable `systems-research` profile with the
shared systems-research ontology, source defaults, profile diagnostics,
Engram run artifact sources, and context-packet rendering support.

The incomplete substrate stage is deployment composition: Engram is
still composing Memex-SR manually even though the canonical composition
now lives upstream in OKG.

## What Changes

- Pin `external/okg` to the portable Memex deployment implementation
  commit.
- Preserve the previous hand-rolled deployment as
  `deployments/memex-sr.old/` for comparison during migration.
- Recreate `deployments/memex-sr/` from `okg init --profile
  systems-research`.
- Add Engram-specific overrides for the upstream `engram_runs` module
  and source adapters.
- Replace collaborator setup docs with the profile-driven bootstrap
  path and updated extension guidance.
- Keep local paper-cut and venue overrides from the prior deployment.

## Capabilities

### New Capabilities

- `memex-sr-profile-deployment`: Defines Engram's profile-driven
  Memex-SR deployment contract.

### Modified Capabilities

- None. This is an Engram deployment packaging change over the OKG
  submodule; OKG substrate behavior remains owned upstream.

## Impact

- Affected deployment files:
  - `external/okg`
  - `deployments/memex-sr/`
  - `deployments/memex-sr.old/`
  - `deployments/memex-sr/HANDOFF.md`
  - `docs/okg-context-packet.md`
- Affected future workflow:
  - Memex-SR initialization becomes `okg init --profile
    systems-research` plus Engram run overrides.
  - New reusable ontology and source work should land in OKG and be
    consumed through the submodule pin.
- OKG substrate impact:
  - None in this Engram change. Follow-on substrate fixes, such as
    derived-artifact catalog-apply registration, belong in OKG.
