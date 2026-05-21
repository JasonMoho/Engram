# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always use OpenSpec when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, architecture shifts, benchmark methodology,
  data-model changes, or performance/security work
- Sounds ambiguous and you need the authoritative project contract before
  coding

Use `openspec/` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Workflow:
- Check active changes with `openspec list`.
- Check current specs with `openspec list --specs`.
- Create changes under `openspec/changes/<change-id>/`.
- Each change should include `proposal.md`, `design.md` when useful,
  `tasks.md`, and one delta spec per affected capability.
- Validate with `openspec validate <change-id> --strict` before
  implementation.

# Project Working Notes

Engram owns the autonomous systems-researcher application, benchmark
integration, Memex-SR deployment files, and experiment harnesses.
`external/okg` is a submodule and has its own OpenSpec workspace for
substrate changes. Use Engram OpenSpec for Engram/Memex-SR deployment
work. Use `external/okg/openspec` only when the OKG substrate itself
needs a new capability or behavioral change.

Do not implement nontrivial proposal work before the relevant OpenSpec
change is written and approved.
