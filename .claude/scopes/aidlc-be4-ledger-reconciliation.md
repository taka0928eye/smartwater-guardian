---
name: be4-ledger-reconciliation
depth: Minimal
keywords: []
description: Implement BE-4 pipe-ledger reconciliation service (ledger.py)
skeleton: on
review_cap: advisory
---

# be4-ledger-reconciliation scope

Minimal depth aimed at shipping a fully-specified backend module fast. The
GitHub Issue already pins the files, function signatures, validations, and
acceptance criteria, so almost everything except the lean path to running,
tested code is skipped: capture the few remaining assumptions, hand off,
then generate and build. No discovery ceremony, no design ceremony, no
operations.

## Why these stages, why skip those

This scope exists because the work is already specified to engineering
grade. Intent-capture is kept (at Minimal depth) only to resolve the three
open assumptions the Issue leaves implicit — the BE-6 wiring scope, the
current-year basis for pipe age, and the empty-data edge of the Haversine
fallback. Approval-handoff keeps the ideation-to-inception gate per the
human-in-the-loop rule. Code-generation and build-and-test are the spine:
TDD tests plus the four new files (pipes.json, pipe.py, ledger.py,
check_ledger.py), closed by the acceptance command and the 80% coverage
floor. Everything else is discarded because it has no consumer here:
market-research (internal module), feasibility (standard JSON-load +
hash-lookup + Haversine pattern), scope-definition and requirements-analysis
(the Issue *is* the scope and requirements), reverse-engineering and
application-design (new files in one known package, and alerts.py already
carries the PipeInfo placeholder to wire into), units-generation and
delivery-planning (one logical unit), and the whole operation phase.

## Membership

Keyword triggers: none — `keywords` is empty, so this scope resolves only by
explicit name (`--scope be4-ledger-reconciliation`), never by inference.
Initialization plus intent-capture, the approval gate, and the
generate-and-test spine execute; the other 25 stages are SKIP.
