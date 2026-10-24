# Contributing

## Branch model
| Branch | Purpose | Who can push |
|---|---|---|
| `main` | Tier releases only. Always green. Tagged `tier-N-done`. | Nobody directly. PR from `develop` after the tier gate passes. |
| `develop` | Integration. Always green. | Nobody directly. Squash-merge PRs only. |
| `<type>/<task-id>-<slug>` | One task, one branch, lives at most a few days. | The task owner. |

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `exp`.
Examples: `feat/T0.6-integrity-gate`, `docs/T0.12-adr-asset-class`, `exp/T4.1-reward-shaping`.
`exp/*` branches are for research experiments. They are never merged into `develop` as-is; port the useful
result into a proper `feat/*` branch with tests.

## Workflow
1. Pick a task from `docs/TASKS.md` (only your own, or one you were reassigned). Open an issue from the Task template.
2. `git switch develop && git pull && git switch -c feat/T0.6-integrity-gate`
3. Commit small and often. Rebase on `develop` before opening a PR (`git pull --rebase origin develop`).
4. Run `make check`. Open a PR into `develop` using the template, one task per PR, ideally under 400 changed lines.
5. Get the required review (below). CI must be green. Squash-merge, delete the branch.
6. Never force-push to `main` or `develop`. Force-pushing your own task branch is fine.

## Commit messages (Conventional Commits)
`<type>(<service>): <summary> [T0.6]`
Example: `feat(data_plane): reject stale quotes older than configured limit [T0.6]`

## Review rules
- Every PR needs 1 approval from someone else. Vedant and Aditya review each other.
- Rushikesh's PRs are reviewed by Aditya or Vedant (the service's second reviewer in CODEOWNERS). Rushikesh also reviews docs PRs.
- Changes to `libs/contracts`, `tests/leakage`, `.github` or any gate (`risk_gate`, `compliance_gate`) need approval from **both** Vedant and Aditya.
- Reviewers answer within 24 hours. If blocked, say so in the team chat instead of waiting.

## Hard rules (CI enforces most of these)
1. No model places a live order. Only `risk_gate` then `compliance_gate` can approve, and `LIVE` mode is blocked in this repo.
2. Point-in-time always: every record carries `knowable_at`; use `libs.common.pit.assert_point_in_time`.
3. Services never import each other's internals (import-linter). Talk through `libs.contracts`.
4. No raw dicts between planes. Typed contracts only.
5. Nothing counts as built without a test. Anything touching data or features also adds a leakage test.
6. No secrets, datasets, or model weights in git. Use `.env` locally; weights live outside git and are referenced by hash in the model registry.
7. Every reported number states its window, cost model and out-of-sample boundary.
8. Every design decision that is hard to reverse gets an ADR in `docs/adr/`.

## GitHub settings to switch on (T0.2)
- Protect `main` and `develop`: require PR, 1 approval, CODEOWNERS review, status check `check`, up-to-date branch, no force-push, no deletion.
- Allow squash merge on `develop`; allow merge commits on `main`; delete head branches after merge.
