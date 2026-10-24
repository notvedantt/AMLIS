# ADR-0001: Branching model and tier gates

- Status: accepted
- Deciders: Vedant, Aditya, Rushikesh

## Context
Three contributors, nine build tiers, strict leakage and audit requirements.

## Decision
`main` (releases, tags per tier) <- `develop` (integration) <- short-lived task branches named
`<type>/<task-id>-<slug>`. Squash-merge into develop, merge-commit develop into main. Tier N+1 service
code starts only after Tier N exit criteria pass (see docs/TIERS.md).

## Consequences
Simple history, every commit traceable to a task ID, and an unambiguous definition of "done" per tier.
