# coding-workflow

A gated, self-improving SDLC workflow for Claude Code, packaged as a shareable
plugin, plus a demo repository. (Formerly `sdlc-workflow`.)

```
coding-workflow/       # this repo: program docs + specs (inner repos ignored)
├── marketplace/       # git repo: the shareable plugin marketplace (plugins/sdlc)
├── demo-app/          # git repo: taskler demo (three features shipped through the workflow)
├── specs/             # improvement-program specs (orchestrator + units A-D)
├── IMPROVEMENTS.md    # improvement review that produced v1.0.0
├── IMPROVEMENTS-2.md  # full analysis #2 (v1.1.0) that produced the unit specs
└── design-candidates/ # dashboard design exploration (reference)
```

## The workflow

Five phases with file-based state in the target repo's `specs/` and
deterministic gates. Kept deliberately light:

**One typed command per feature + two conversational approvals** (one on the
quick track). Phases auto-continue whenever their gate is open.

| Phase | Output | Gate |
|---|---|---|
| Requirements | `spec.md` — FR-IDs, EARS acceptance criteria, risk, track proposal | review checklist → say "approved" |
| Plan *(full track)* | `plan.md` — FR-traced tasks, affected files, coherence check | review checklist → say "approved" |
| Implement | code + tests, TDD task-by-task, progress mirrored to status.json | tasks done, suite green |
| Verify | `verification.md` — verbatim evidence + per-FR verdicts from a fresh adversarial reviewer | machine gate, 2-strike auto-loop |
| Document | reconciled spec, docs, lessons, metrics, plugin proposals | — |

- `track: quick` (small changes, bugfixes): the spec carries a ≤15-line
  mini-plan and ONE approval opens implementation.
- **The gate contract**: approval = an explicit "approved" to a direct
  question after seeing the artifact (checklist provided). Recorded in
  status.json (who/when). Momentum never counts; unattended runs never
  self-approve. Async works too: "approve the plan for 003" in any session,
  or answer the `REVIEW.md` questionnaire an unattended run leaves behind.
  A present user can grant a standing approval directive ("stop asking") —
  artifacts still get presented, gates record without blocking questions.
- Optional `specs/constitution.md`: durable MUST/SHOULD principles, loaded at
  plan + verify; conflicts are CRITICAL and never resolved by dilution.
- The document phase **reconciles the spec with what shipped** (spec-anchored,
  not write-once) and distills `lessons/` (one fact per file, conditional
  loading) that future planning reads.

`/sdlc:init` scaffolds a repo; `/sdlc:status` and `/sdlc:dashboard`
(`--serve` for a live localhost board) show state; per-phase commands exist to
resume mid-pipeline. A SessionStart hook injects the board state into every
new session automatically.

## Enforcement (deterministic, not prose)

- **Edit gate** (PreToolUse on Edit/Write/NotebookEdit/Bash/PowerShell):
  code changes are blocked unless a feature is in an approved
  implement/verify phase, and are scoped to the approved plan's
  `## Affected files`. Bash/PowerShell commands are screened for write
  patterns (documented residual gap: writes hidden inside quoted inline
  code). Inert in repos without `specs/`.
- **State validation** (PostToolUse): every `specs/*/status.json` write is
  checked against `schema/status.schema.json`.
- 32-case pytest suite covers the hooks and generator (`marketplace/tests`,
  CI on Ubuntu + Windows).

Prerequisite: `python` on PATH (hook scripts are stdlib-only). A missing
python makes hooks noisy but never blocks work.

## Install & upgrade

```
claude
> /plugin marketplace add C:\Users\Alex\PycharmProjects\sdlc-workflow\marketplace
> /plugin install sdlc@sdlc-marketplace
```

For a team: push `marketplace/` to GitHub and `add org/repo`.

Two operational notes (learned the hard way):
- Plugin content loads at **session start** — after changing the plugin,
  start a new session.
- `claude plugin marketplace update` refreshes the catalog but not the
  installed version pin — upgrade with `claude plugin uninstall sdlc` +
  `install`.

## Optional patterns

- **Git integration**: the workflow doesn't commit by itself. A good opt-in
  convention: branch per feature, commit at phase boundaries, tag at done —
  put it in the target repo's CLAUDE.md if wanted.
- **Team board**: `dashboard/ci-github-pages.yml` publishes the board to
  GitHub Pages on every `specs/**` push.
- **Evals** (experimental): `evals/` contains grader-based cases (spec
  creation, gate refusal) for `claude plugin eval`.

## Try the demo

`demo-app/` shipped its first feature (due dates) through the full workflow —
spec, plan, 15 green tests, adversarial review, reconciled docs, one lesson.
Open its `dashboard.html` or run `/sdlc:requirements <brief>` inside it to
continue.
