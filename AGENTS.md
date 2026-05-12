# AGENTS.md — Repository guardrails for AI coding agents

Any AI coding agent (Claude, Codex, Cursor, etc.) operating in this repository
MUST read and follow this file. The CI harness enforces these rules; running
outside CI does not exempt you.

The machine-readable version of these rules lives in `.ai-harness/policy.yml`.
The full prompt the CI harness injects is `.ai-harness/prompt.md`. This file is
the human-readable summary and the contract.

---

## Hard rules — never violate

- Branch name MUST start with `ai/<agent>/` (e.g. `ai/claude/issue-42-...`).
- Never push to `main`, `master`, or `release/*`.
- Never merge, approve, close, or re-open a PR.
- Never use `--no-verify`, `--force`, force-push, `git reset --hard` on shared
  branches, or any flag that bypasses hooks / CI.
- Never modify any of:
  - `.github/**` (workflows, templates, CODEOWNERS)
  - `.ai-harness/**` (this harness)
  - `AGENTS.md` itself
  - `infra/`, `terraform/`, `k8s/`, `helm/`
  - `secrets/`, `.env*`, `*.pem`, anything matching `*secret*`
  - `package-lock.json`, `pnpm-lock.yaml` (regenerate only via dependency tasks)
- Never commit secrets. If you find one, redact, do not commit, flag in PR body.
- Never invent requirements not in the ticket. If unclear → analysis only, no code.

## Allowed scope

You MAY read anything. You MAY only write to:

- `backend/` (source + tests under `backend/tests/`)
- `frontend/src/` (source + tests)
- `docs/` (including the mandatory `docs/ai-analysis/task-<id>.md`)

Touching anything outside Allowed scope requires opening a DRAFT PR labelled
`needs-human-author` that explains why — no code changes in that PR.

## High-risk areas — analysis only, no code changes

If the ticket touches any of these keywords, produce ONLY the analysis doc and
stop. Do not edit code:

`auth`, `authorization`, `authentication`, `payment`, `permission`, `encryption`,
`token`, `secret`, `password`, `database migration`, `production`, `deployment`.

## Change-size cap

- ≤ 12 files changed
- ≤ 600 lines added + deleted

If you can't fit the work in that budget, stop and request the human split the
ticket. Do not open the PR.

## Workflow you must follow

1. Read the ticket. Confirm acceptance criteria are present and unambiguous.
2. Read `.ai-harness/prompt.md` (the strict procedural rules).
3. Plan the minimal change. Note it in the analysis doc.
4. Implement only within Allowed scope.
5. Add or update tests for changed behaviour.
6. Run repo checks locally:
   - `ruff check backend && PYTHONPATH=. pytest backend/tests -q` (backend)
   - `cd frontend && npm ci && npm test && npm run build` (frontend)
7. Generate `docs/ai-analysis/task-<TICKET_ID>.md` from
   `.ai-harness/AI_DOCUMENT_TEMPLATE.md`. Fill every section — no empty rows.
8. The CI harness opens a DRAFT PR on your behalf. You do not run `gh pr create`.

## Definition of done

- [ ] All acceptance criteria from the ticket pass
- [ ] Tests added or updated for changed behaviour, and all pass locally
- [ ] No file outside Allowed scope changed
- [ ] Change ≤ 12 files / ≤ 600 lines
- [ ] `docs/ai-analysis/task-<TICKET_ID>.md` is complete (no empty sections)
- [ ] PR body references the issue with `Closes #<TICKET_ID>`

## If anything is unclear

Stop. Produce only the analysis document. State exactly:

- What is missing or contradictory in the ticket
- What clarification you need from a human
- Why making the change blindly would be unsafe

Do not guess. Do not partially implement. Do not skip the analysis doc.

## Core principle

You are not an autonomous developer. You are a controlled code generator inside
a safety harness. The harness reviews you, not the other way around. When in
doubt: stop, explain, do not guess.
