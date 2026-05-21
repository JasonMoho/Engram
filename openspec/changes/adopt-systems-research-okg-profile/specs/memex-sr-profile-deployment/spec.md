## ADDED Requirements

### Requirement: Profile-Driven Memex-SR Deployment

Engram SHALL consume OKG's `systems-research` profile for the Memex-SR
deployment instead of maintaining an equivalent hand-rolled deployment
composition.

#### Scenario: OKG submodule is pinned to profile-capable substrate
- **WHEN** the Memex-SR deployment is prepared
- **THEN** `external/okg` SHALL be pinned to an OKG commit that contains
  `okg init --profile systems-research`, module manifests, subtype
  refinement, the `systems_research` ontology module, the `engram_runs`
  module, and the context-packet MCP tool.

#### Scenario: Deployment is initialized from profile
- **WHEN** a fresh Memex-SR deployment is generated
- **THEN** it SHALL use OKG's `systems-research` profile with the
  Engram paper-cut manifest, venues file, Postgres DSN, and MCP port
  recorded in the deployment profile reference metadata.
- **AND** if the pinned OKG CLI cannot parse `okg init --profile
  systems-research`, the handoff SHALL document the exact blocker and
  provide an Engram shim that calls the same OKG profile-init library.

#### Scenario: Old deployment is retained for migration diff
- **WHEN** the profile-driven deployment replaces the hand-rolled
  deployment
- **THEN** the previous deployment SHALL be retained as
  `deployments/memex-sr.old/` until first publish, profile diagnostics,
  and Engram run ingestion are verified.

### Requirement: Engram Run Ingestion Overrides

Engram SHALL add its run-artifact ingestion as profile overrides rather
than as local ontology/source forks.

#### Scenario: Engram run module is loaded
- **WHEN** Memex-SR catalog composition is configured
- **THEN** the deployment SHALL include `engram_runs` in the effective
  module list consumed by OKG catalog composition.

#### Scenario: Engram run source adapters are configured
- **WHEN** Memex-SR source registry is configured
- **THEN** it SHALL include source entries for research digest,
  experiment result, candidate solution, final result, and agent summary
  ingestion, all pointing at the configured Engram results directory.

### Requirement: Context Packet MCP Handoff

Engram SHALL treat OKG's generated context packet as an MCP-derived
artifact once the profile-driven deployment is live.

#### Scenario: Agent context packet is generated through OKG MCP
- **WHEN** an Engram agent needs systems-research context for a problem
- **THEN** the integration docs SHALL describe calling
  `generate_context_packet` with problem name, domain, topic slugs,
  evidence budget, token budget, and optional generation id.

#### Scenario: Evidence ids are inspectable
- **WHEN** a context packet includes evidence ids
- **THEN** the docs SHALL state that each id resolves to a live OKG node
  in the pinned generation and can be inspected with MCP `get_node`.
