# Memex-SR Source Sample Coverage

Generated: `2026-05-14T17:05:13+00:00`
Config: `deployments/memex-sr/data_sources.yaml`

## Source Status

| Source | Kind | Status | Items | Ontology Hits | Notes |
| --- | --- | --- | ---: | --- | --- |
| `memex-sr-corpus-configs` | `yaml_config` | `ok` | 5 | CorpusPack, CorpusCoverageSnapshot, Venue, VenueEdition, PublicationSeries | - |
| `local-memex-sr-design-corpus` | `local_glob` | `ok` | 5 | Document, DocumentSection, DocumentChunk, EvidenceSlice, Claim, ResearchProblem, DistillationSection | - |
| `dblp-osdi-2023-toc` | `dblp_toc_html` | `network_error` | 0 | - | Local shell probes reset/timed out on 2026-05-14, but browser access to the DBLP page succeeded. |
| `usenix-osdi23-technical-sessions` | `usenix_technical_sessions` | `ok` | 5 | Paper, Person, Venue, VenueEdition, PublicationSeries, DocumentAsset | pdf_hint_count=6; PDF links are counted but not downloaded by the sampler. |
| `pvldb-volume-16` | `vldb_volume` | `ok` | 5 | Paper, Person, Venue, VenueEdition, PublicationSeries, DocumentAsset, Document | - |
| `openalex-scalene-search` | `openalex_search` | `ok` | 3 | Paper, Person, Venue, VenueEdition, PublicationSeries, Organization, Software | - |
| `crossref-scalene-title-query` | `crossref_query_title` | `ok` | 3 | - | Expected to be noisy unless constrained by DOI or target-set identity.; diagnostic_only_source_not_counted_for_coverage |
| `systems-artifact-manifest-fixture` | `yaml_config` | `ok` | 1 | Dataset, Software, Benchmark, Paper, DocumentAsset | - |
| `semantic-scholar-scalene-search` | `semantic_scholar_search` | `rate_limited` | 0 | - | Semantic Scholar should be used with API-key-aware rate handling in production. |
| `openreview-mlsys-2024-notes` | `openreview_notes` | `empty` | 0 | - | Initial venueid probe returned zero notes; source needs venue-id refinement.; OpenReview source may need invitation/venue-id discovery before production. |
| `rfc-editor-rfc9000` | `rfc_text` | `ok` | 1 | Organization, DocumentAsset, Document, DocumentSection, DocumentChunk, EvidenceSlice, Claim | Sampler stores metadata only; production parser should chunk local fetched text. |
| `arxiv-scalene-title-query` | `arxiv_query` | `timeout` | 0 | - | Local probe timed out on 2026-05-14; keep sampled but non-blocking. |
| `engram-workspace-fixture` | `engram_workspace_fixture` | `ok` | 5 | ResearchRun, AgentAttempt, Experiment, CandidateImplementation, MetricObservation, FailureDiagnosis, ResearchNote, WorkspaceArtifact | - |

## Ontology Coverage

| Ontology Target | Covered By Successful Samples |
| --- | --- |
| `AgentAttempt` | `engram-workspace-fixture` |
| `Benchmark` | `systems-artifact-manifest-fixture` |
| `CandidateImplementation` | `engram-workspace-fixture` |
| `Claim` | `local-memex-sr-design-corpus`, `rfc-editor-rfc9000` |
| `CorpusCoverageSnapshot` | `memex-sr-corpus-configs` |
| `CorpusPack` | `memex-sr-corpus-configs` |
| `Dataset` | `systems-artifact-manifest-fixture` |
| `DistillationSection` | `local-memex-sr-design-corpus` |
| `Document` | `local-memex-sr-design-corpus`, `pvldb-volume-16`, `rfc-editor-rfc9000` |
| `DocumentAsset` | `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `systems-artifact-manifest-fixture`, `rfc-editor-rfc9000` |
| `DocumentChunk` | `local-memex-sr-design-corpus`, `rfc-editor-rfc9000` |
| `DocumentSection` | `local-memex-sr-design-corpus`, `rfc-editor-rfc9000` |
| `EvidenceSlice` | `local-memex-sr-design-corpus`, `rfc-editor-rfc9000` |
| `Experiment` | `engram-workspace-fixture` |
| `FailureDiagnosis` | `engram-workspace-fixture` |
| `MetricObservation` | `engram-workspace-fixture` |
| `Organization` | `openalex-scalene-search`, `rfc-editor-rfc9000` |
| `Paper` | `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `openalex-scalene-search`, `systems-artifact-manifest-fixture` |
| `Person` | `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `openalex-scalene-search` |
| `PublicationSeries` | `memex-sr-corpus-configs`, `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `openalex-scalene-search` |
| `ResearchNote` | `engram-workspace-fixture` |
| `ResearchProblem` | `local-memex-sr-design-corpus` |
| `ResearchRun` | `engram-workspace-fixture` |
| `Software` | `openalex-scalene-search`, `systems-artifact-manifest-fixture` |
| `Venue` | `memex-sr-corpus-configs`, `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `openalex-scalene-search` |
| `VenueEdition` | `memex-sr-corpus-configs`, `usenix-osdi23-technical-sessions`, `pvldb-volume-16`, `openalex-scalene-search` |
| `WorkspaceArtifact` | `engram-workspace-fixture` |

## Current Gaps

- None

## Operational Findings

- `dblp-osdi-2023-toc` returned `network_error`: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
- `semantic-scholar-scalene-search` returned `rate_limited`: Semantic Scholar should be used with API-key-aware rate handling in production.
- `openreview-mlsys-2024-notes` returned `empty`: Initial venueid probe returned zero notes; source needs venue-id refinement.; OpenReview source may need invitation/venue-id discovery before production.
- `arxiv-scalene-title-query` returned `timeout`: HTTPSConnectionPool(host='export.arxiv.org', port=443): Read timed out. (read timeout=20)
