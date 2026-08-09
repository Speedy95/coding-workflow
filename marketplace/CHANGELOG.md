# Changelog — sdlc plugin

## 1.1.0 (2026-08-03) — OKF-aligned lessons + async review questionnaires

- **Lessons are now OKF-aligned** (Google's Open Knowledge Format, v0.1):
  frontmatter gains `type: lesson` (OKF's one required field), `tags`
  (grouping — tags before folders), `source` (originating feature) and
  `verified` (last confirmation date, the staleness signal for compaction);
  related lessons cross-link with standard markdown links, forming the
  knowledge graph. Existing `inclusion`/`match` fields are unchanged
  (OKF permits producer-defined fields).
- **Async review questionnaires**: unattended runs stopping at a human gate
  now write `specs/<slug>/REVIEW.md` — the approval checklist as answerable
  questions ending in `Approve this <spec|plan>? (yes/no):`. A later session
  finding an explicit written yes records the gate normally, addresses the
  other answers, and deletes the file. The SessionStart hook flags pending
  questionnaires (+1 test, 36 total).
- Evaluated but deferred: full OKF bundle structure (typed subdirs/log.md —
  ceremony at lessons scale), a grilling-style deep-interview exploration
  mode (future minor version).

## 1.0.2 (2026-08-03) — standing approval directives

From e2e run 003 (full track): repeated gate questions fatigue a present
user driving multiple features. The gate contract now supports an explicit
**standing approval directive** ("stop asking for approvals"): artifacts and
checklists are still presented, gates are recorded as
`by: "<user> (standing directive)"` without a blocking question, but genuine
forks (open questions, revised artifacts, destructive scope changes) still
ask. Momentum still never counts; unattended runs still never self-approve
(a standing directive does not carry into them).

## 1.0.1 (2026-08-03) — quick-track fixes from e2e run 002

Findings from the first live quick-track run (demo-app 002-list-all-done-last):

- **Quick-track scope gap closed**: the edit gate scoped only via plan.md, so
  quick-track features (mini-plan in spec.md, no plan.md) silently unlocked
  the whole repo. The gate now falls back to the spec mini-plan's
  `Affected files:` line (backticked paths, single line); writing-specs
  documents the format as load-bearing. +3 gate tests (35 total).
- tdd-loop: quick track has no plan.md checkboxes — status.json's task mirror
  is the task record; scope additions go to the mini-plan line.
- verification: defined `coverage` for quick track (% of FRs "met" with a
  named test) — it was only defined via the full-track coherence check.
- sdlc-state: documented the quick-track convention
  `artifacts.plan = "spec.md#mini-plan"`.

## 1.0.0 (2026-08-03) — production hardening

Enforcement:
- Gate hook derives the SDLC root from the **edited file's path** (fix: a
  session rooted outside the repo could bypass the gate).
- Gate now covers NotebookEdit and screens Bash/PowerShell commands for write
  patterns (redirects, tee, sed -i, Out-File/Set-Content) with quote-aware
  false-positive protection. Residual gap (documented): writes hidden inside
  quoted inline code (e.g. `python -c "..."`) are not caught.
- **Feature-scoped unlock**: with an approved plan, edits are limited to the
  plan's `## Affected files` (exact file / same dir / listed dir). Fails open
  when the section is missing or unparseable.
- New PostToolUse hook validates every `specs/*/status.json` write against
  `schema/status.schema.json` (now the authoritative schema).
- New SessionStart hook injects the board state into any session opened in an
  SDLC repo ("001-x: implement 3/5 — resume with /sdlc:implement 001-x").
- 32-case pytest suite for the hooks and dashboard generator; CI workflow.

Workflow:
- **Tracks**: `quick` folds planning into the spec gate (mini-plan in the
  spec, one approval) for small/low-risk work and bugfixes; `full` unchanged.
- **Checklist gates**: requirements/plan end with 5–8 targeted review items —
  the gate means answering them, not cold-reading documents. Hard length
  budgets on spec (≤2 pages) and plan (≤1.5).
- **Traceability**: FR-IDs on requirements, EARS acceptance criteria, plan
  tasks cite FR-IDs, verification reports a per-FR verdict table; plan phase
  runs a coherence check (two-way coverage + %, ambiguity, terminology,
  budgets) before approval.
- Optional `specs/constitution.md` (normative principles, loaded at plan +
  verify; conflicts are CRITICAL — adjust the change, never the principle).
- **Reconcile-on-document**: spec.md is folded into line with what actually
  shipped (+ Amendments note) — spec-anchored, not spec-first.
- verifyAttempts recorded (auto-loop hard-stops after 2 failed passes even
  across sessions); vacuous-red detection in the TDD loop; task progress
  mirrored to status.json; lessons get inclusion frontmatter
  (always/fileMatch/manual) + a compaction cadence; specs/archive/ convention.
- `[P]` parallel task markers + worktree isolation guidance; implementer runs
  acceptEdits; adversarial reviewer must return per-FR verdicts (re-dispatched
  once if not) and checks the constitution; risk-scaled second lens on high.
- New `/sdlc:init` scaffold command. Eval cases under `evals/` (experimental).

Dashboard:
- Template extracted to `dashboard/template.html` (same zero-dependency
  output); task progress ("implementing · 3/5 tasks") and quick-track badge;
  `ci-github-pages.yml` example shipped.

### Deferred by design (not omissions)
- **Statusline**: users often have their own; a snippet belongs in docs, not
  a forced override.
- **Blocking Stop hook** ("suite is red, don't stop"): fights the user;
  SessionStart injection covers resume safety instead.
- **UserPromptSubmit context injection**: per-prompt cost; SessionStart
  already carries the state.
- **Approve-from-board**: changes the gate's trust model; separate decision.
- **MCP server for workflow state / LSP spec linting / cloud routines**:
  future tiers; checklist + coherence check cover linting needs today.
- **Automatic git branching/committing**: policy belongs to the target repo;
  documented as an opt-in pattern in the README instead.

## 0.7.0 — conversational gates (no approve command), auto-continuing phases
## 0.6.x — single-list status-first board, recency ordering, contrast pass
## 0.5.0 — Onyx/Dignitas design schema
## 0.4.x — dossier board: artifact reader (md), lessons tab, --serve live mode
## 0.3.0 — signal-box gate rail design
## 0.2.0 — dashboard generator
## 0.1.0 — initial gated workflow (commands, skills, agents, edit gate)
