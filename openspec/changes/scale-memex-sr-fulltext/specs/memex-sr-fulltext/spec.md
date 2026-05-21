## ADDED Requirements

### Requirement: Memex-SR Full-Text Paper Projection

Memex-SR SHALL provide an operator-controlled path that turns reviewed
paper full-text assets into published OKG documents and chunks.

#### Scenario: Open PDF assets are cache-backed before publish

- **GIVEN** the existing Memex-SR paper cut contains open PDF URL hints
- **WHEN** an operator runs the paper full-text acquisition workflow
- **THEN** allowed open PDFs are written to a deterministic local cache
- **AND** the acquisition manifest records source URL, local path, byte
  count, content hash, paper id, venue, and year
- **AND** blocked, metadata-only, or authenticated records are not
  counted as ingested unless local bytes exist.

#### Scenario: Publish emits paper documents and chunks from local bytes

- **GIVEN** a paper full-text acquisition manifest with available local
  files
- **WHEN** the `paper_fulltext_documents` source is ingested and
  published
- **THEN** the published generation contains `document_asset`,
  `document`, and `document_chunk` nodes for the available files
- **AND** `document contains document_chunk` and `document_chunk member_of
  document` edges are live
- **AND** the source run reports parse failures rather than silently
  accepting empty text.

#### Scenario: No-change rerun is delta-proportional

- **GIVEN** no acquired file or manifest row changed after the previous
  publish
- **WHEN** the `paper_fulltext_documents` source is ingested again
- **THEN** the run appends zero new facts or skips publish with
  `no_source_work`.
