---
name: be8-kpi-summary
depth: Minimal
keywords: []
description: Implement BE-8 KPI estimated-cost-saving calculation and summary API (kpi.py)
skeleton: on
review_cap: advisory
---

# be8-kpi-summary scope

Minimal depth aimed at shipping a fully-specified backend module fast. The
GitHub Issue (ISSUE #18) already pins the files, constants, calculation
formula, response schema, and acceptance criteria, so almost everything
except the lean path to running, tested code is skipped: capture the few
remaining assumptions, hand off, then generate and build. No discovery
ceremony, no design ceremony, no operations.

## Why these stages, why skip those

This scope exists because the work is already specified to engineering
grade. Intent-capture is kept (at Minimal depth) only to resolve the open
assumptions the Issue leaves implicit — the `SeverityLevel` type source
(BE-3 `audio.py` is UNIMPLEMENTED, so the level type must come from the
existing alert schema), the alert/hydrant store wiring for
`build_kpi_summary`, and the empty-store 200-with-zeros edge. Approval-
handoff keeps the ideation-to-inception gate per the human-in-the-loop
rule. Code-generation and build-and-test are the spine: TDD tests plus the
four new files (services/kpi.py, schemas/kpi.py, routers/kpi.py,
tests/test_kpi.py) and the main.py router registration, closed by the
acceptance command and the 80% coverage floor. Everything else is
discarded because it has no consumer here: market-research (internal
module), feasibility (pure-function arithmetic + store aggregation
pattern), scope-definition and requirements-analysis (the Issue *is* the
scope and requirements), reverse-engineering and application-design (new
files in one known package, and the store/schema wiring is already
established by BE-6/BE-4), units-generation and delivery-planning (one
logical unit), and the whole operation phase.

## Membership

Keyword triggers: none — `keywords` is empty, so this scope resolves only by
explicit name (`--scope be8-kpi-summary`), never by inference.
Initialization plus intent-capture, the approval gate, and the
generate-and-test spine execute; the other 25 stages are SKIP.
