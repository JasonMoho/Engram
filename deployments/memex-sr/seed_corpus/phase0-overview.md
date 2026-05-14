# Memex-SR Phase 0 Overview

Memex-SR is the systems-research fork of the broader memex deployment.
Its first goal is to build a fast, inspectable OKG deployment that can
ground an autonomous systems researcher in the recent systems and
database literature.

The initial corpus target is full-text papers from the last five years
of systems and database venues: SOSP, OSDI, NSDI, SIGCOMM, HotNets,
EuroSys, CoNEXT, SIGMOD, VLDB, CIDR, PODS, and MLSys. The deployment
must expand through corpus packs rather than one-off scripts so future
collaborators can add venues, years, standards, technical reports,
books, course material, code repositories, and curated research blogs.

The deployment is meant to distill research knowledge into reusable
principles, lessons, trade-off maps, and methodological guidance. The
consumer is both a human collaborator and an Engram agent doing
scientific discovery. The graph should preserve provenance back to the
paper, section, chunk, venue, artifact, and extraction run so generated
textbook-style summaries can be audited.

Phase 0 indexes the deployment's own design documents and seed notes.
This proves the local external-deployment loop: source discovery,
document parsing, chunking, publication, and MCP query access from a
Codex CLI session.
