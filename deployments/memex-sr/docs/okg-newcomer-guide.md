# OKG Newcomer Guide

This guide is for a reader who has not worked with OKG before and wants
to understand what Memex-SR is, what is currently in the graph, and how
to extend it without touching substrate internals.

## What OKG Is

OKG is a typed, versioned knowledge graph backed by Postgres. Sources
emit facts, the substrate validates those facts against an ontology,
publishes a generation, and exposes the graph to agents through MCP and
CLI tools.

For Memex-SR, the graph is intended to become an autonomous systems
research memory:

- papers, reports, standards, blogs, and local documents enter as
  source records;
- metadata and full text become graph nodes and edges;
- document chunks become evidence;
- later distillation jobs turn evidence into principles, mechanisms,
  trade-offs, failure modes, and open problems;
- Engram agents query the graph for context before or during a research
  run.

The important constraint is that collaborators should not write directly
to live graph tables. New information enters through a source, a catalog
ontology, and a publish cycle.

## Mental Model

```mermaid
flowchart LR
    Source["Source adapter or manifest"]
    Facts["Node/edge facts"]
    Catalog["Ontology and edge narrowings"]
    Publish["Publish cycle"]
    Generation["Published generation"]
    Tools["MCP / CLI / SQL reads"]

    Source --> Facts
    Facts --> Catalog
    Catalog --> Publish
    Publish --> Generation
    Generation --> Tools
```

The core terms:

| Term | Meaning |
| --- | --- |
| Source | Code or a manifest that emits graph facts. Examples: `paper-cut`, `doc-corpus`. |
| Node | An entity in the graph, such as a `paper`, `person`, `venue`, or `document_chunk`. |
| Edge | A relationship, such as `paper -> authored_by -> person`. |
| Ontology | The allowed node types and required attributes. In this deployment it lives under `schemas/`. |
| Narrowing | The allowed edge route, such as `Paper authored_by Person`. If the route is missing, the edge is rejected. |
| Publish | The transaction that projects source facts into live graph rows and creates a new generation. |
| Generation | A stable snapshot. MCP sessions pin to one generation so answers are reproducible. |
| Manifest | A local file that records source output or acquisition state. Publish should read manifests, not make live network calls. |

## What Memex-SR Is

Memex-SR is the Engram-owned OKG deployment for autonomous systems
research. It lives in this repository under:

```text
deployments/memex-sr/
```

The OKG substrate implementation is a git submodule at:

```text
external/okg/
```

The Engram repo owns the deployment-specific pieces:

| Path | Purpose |
| --- | --- |
| `deployment.yaml` | Declares the Memex-SR deployment and loaded ontology modules. |
| `source_registry.yaml` | Lists runnable graph sources and their sync policy. |
| `schemas/` | Deployment-owned node types. |
| `schemas/bridges/` | Edge narrowings that connect node types. |
| `sources/` | Deployment-owned source adapters. |
| `scripts/` | Source sampling, paper-cut collection, and later reports/acquisition utilities. |
| `manifests/` | Generated or curated input manifests for publish. |
| `docs/` | Operator and collaborator guidance. |
| `spec/` | Proposal, design, requirements, and task tracking. |

The `doc-corpus` source intentionally indexes stable design/context
documents, not live-count handoff docs. This avoids a self-referential
loop where updating "latest generation" prose creates new graph facts on
every publish.

## What Is In The Current Graph

The current verified local graph is generation `5` in the local
database:

```text
postgres://postgres:okg@127.0.0.1:5433/engram_memex_sr_phase0
```

Generation `5` contains metadata and URL hints. It does not yet contain
parsed paper full text.

Current graph counts:

| Subtype | Count |
| --- | ---: |
| `person` | 13,499 |
| `document_asset` | 7,310 |
| `paper` | 4,782 |
| `document_chunk` | 96 |
| `entity_mention` | 76 |
| `venue_edition` | 24 |
| `publication_series` | 16 |
| `venue` | 16 |
| `document` | 6 |
| `corpus_coverage_snapshot` | 1 |
| `corpus_pack` | 1 |

Current paper sources:

| Provider | Source Records |
| --- | ---: |
| USENIX | 1,180 |
| PVLDB | 1,787 |
| OpenAlex | 2,978 |

Those source records dedupe to `4,782` paper nodes. DBLP is planned as
the authoritative venue/year enumerator, but local shell access to DBLP
currently resets or times out, so DBLP is not yet the active source.

Current paper coverage by venue:

| Venue | Papers |
| --- | ---: |
| `pvldb` | 2,291 |
| `sigmod` | 985 |
| `nsdi` | 520 |
| `osdi` | 348 |
| `icde` | 326 |
| `usenix_atc` | 312 |

Current known gaps before full text:

- missing or weak target coverage for `sosp`, `sigcomm`, `hotnets`,
  `conext`, `eurosys`, `socc`, `mlsys`, `pods`, `cidr`, and `edbt`;
- OpenAlex records need a quality audit before they are treated as
  main-track venue truth;
- `document_asset` nodes are URL hints, not verified local files;
- no parsed PDF text, paper sections, paper chunks, evidence slices, or
  distilled textbook sections have been published yet.

See `docs/pre-full-text-readiness.md` for the detailed graph counts,
venue/year table, and pre-full-text gates.

## How To Query It

For operators, the fastest local checks are CLI and pinned SQL.

CLI status:

```bash
external/okg/.venv/bin/okg status \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

Generation check:

```bash
external/okg/.venv/bin/okg generation describe 5 \
  --deployment memex-sr \
  --dsn "$MEMEX_SR_OKG_DSN" \
  --json
```

Pinned SQL example:

```bash
psql "$MEMEX_SR_OKG_DSN" -Atc "
begin;
set local okg.pin_generation='3';
select subtype, count(*)
from okg.v_nodes
group by subtype
order by count(*) desc;
commit;"
```

For agents, use the Memex-SR MCP server. The default read flow is:

1. `describe_graph` to understand available node and edge types.
2. `search` for a topic, paper title, venue, or design term.
3. `get_node` for full node attrs.
4. `list_neighbors` or `traverse_path` to follow evidence paths.

MCP sessions are pinned to a generation. Reconnect after a new publish
if you need the latest graph.

## How To Extend The Graph

Every extension should follow this pattern:

1. Decide what new information should exist in the graph.
2. Check whether existing node types and edges can represent it.
3. If not, add ontology classes or bridge narrowings.
4. Add or update a source that emits facts.
5. Run a publish.
6. Verify live rows changed in the expected generation.
7. Add a no-op rerun check when the source is high volume.

Do not skip step 6. If counts do not change, the source likely did not
emit facts, the edge route was rejected by narrowings, or projection did
not run.

### Add A Venue Or Year

Edit:

```text
deployments/memex-sr/venues.yaml
```

Then update source collection logic or provider configuration so the
venue/year can actually emit paper records. A venue entry alone does not
create graph nodes.

Minimum verification:

- regenerated manifest includes the venue/year;
- publish creates `paper` nodes for that venue/year;
- every new paper has a `published_in` edge;
- no-op rerun appends zero facts.

### Add A Data Source

Use this when adding DBLP, OpenReview, arXiv, Crossref enrichment,
Semantic Scholar enrichment, a blog manifest, or an operator-supplied
asset directory.

Edit or add:

```text
deployments/memex-sr/sources/<source_name>.py
deployments/memex-sr/source_registry.yaml
deployments/memex-sr/download_host_policy.yaml
deployments/memex-sr/data_sources.yaml
```

The source adapter should emit `NodeFact` and `EdgeFact` objects, or it
should write a manifest consumed by a publish-time source. Network calls
belong in collection/acquisition steps, not in deterministic full-text
publish.

Minimum verification:

- source registry validates;
- source run appends expected node and edge facts;
- generation publishes and is not blocked;
- `okg status` shows the source cursor;
- `okg metrics --source-sync` has DLQ `0`;
- unchanged rerun appends zero facts.

### Add A Node Type Or Edge

Use this when existing ontology cannot represent the information.

Edit:

```text
deployments/memex-sr/schemas/*.yaml
deployments/memex-sr/schemas/bridges/*.yaml
```

Rules:

- node classes need an `archetype` annotation or they will not become
  graph subtypes;
- searchable nodes should declare `okg_searchable_text_fields`;
- aliases should declare `okg_alias_fields`;
- every emitted edge must have a bridge narrowing;
- high-cardinality labels should usually stay attrs, not nodes.

Minimum verification:

- `okg catalog load --apply` succeeds;
- `narrowing_count` increases when a new route was added;
- a fixture or real source emits at least one node/edge using the new
  type;
- the next generation publishes with no narrowing violations.

### Add Full-Text Acquisition

Full text should be a two-stage flow:

1. Acquisition downloads or records local assets into a manifest.
2. Publish reads only local manifest assets and emits `document`,
   section, chunk, and evidence facts.

Before downloading at scale, run the gates in
`docs/pre-full-text-readiness.md`:

- corpus coverage audit;
- paper quality audit;
- asset URL audit;
- guardrail invariants.

Minimum verification:

- downloader is cache-first and host-policy governed;
- manifest records terminal state for every candidate asset;
- publish does not make live network calls;
- parsed chunks are parent-scoped to the paper/document;
- no-op rerun reparses nothing unchanged.

### Add Distillation

Distillation should not be free-floating prose. It should produce graph
nodes backed by evidence ids:

- `EvidenceSlice` from paper chunks;
- `Claim` for mechanisms, lessons, and trade-offs;
- `ResearchProblem` for open problems and limitations;
- `DistillationSection` for textbook-like generated sections.

Minimum verification:

- every claim or section has support edges to evidence;
- output records source generation and evidence watermark;
- stale sections can be detected when evidence changes.

### Add Engram Workspace Indexing

Engram outputs should enter OKG as source facts after a run finishes.
The graph should remember experiments, code snapshots, metrics,
failures, and research notes.

Planned node types:

- `ResearchRun`
- `AgentAttempt`
- `Experiment`
- `CandidateImplementation`
- `MetricObservation`
- `FailureDiagnosis`
- `ResearchNote`
- `WorkspaceArtifact`

Minimum verification:

- indexing the same archive twice appends zero facts;
- changing one score or snapshot scopes downstream work to that
  artifact;
- support/refute edges require explicit summary evidence, not merely
  the fact that an agent read a paper.

## Definition Of Done For Any Extension

An extension is not done when code compiles. It is done when a published
generation proves the intended graph changed.

Checklist:

- config and source files are committed or staged;
- catalog load succeeds if ontology changed;
- source run completes;
- generation publishes;
- expected node/edge counts appear in `okg.v_nodes` and `okg.v_edges`;
- source-sync metrics have DLQ `0`;
- unchanged rerun appends zero facts for high-volume sources;
- docs explain what was added and how to reproduce it.

## What Not To Do

- Do not write directly to `okg.nodes_live` or `okg.edges_live`.
- Do not add edges without bridge narrowings.
- Do not treat source sampling as ingestion; samples are diagnostics.
- Do not make live network calls inside full-text publish.
- Do not bulk-crawl the open web. Use explicit source packs and host
  policy.
- Do not expose raw SQL to Engram agents by default.
- Do not claim full-text coverage when only URL hints exist.
