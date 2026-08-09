---
name: sdlc-state
description: The SDLC workflow's file-based state model - specs/ layout, status.json schema, phase transitions, gates, and the metrics ledger. Load before reading or writing any workflow state.
---

# SDLC state model

All workflow state lives as files in the target repository. The conversation is
never the source of truth — any teammate (or agent) must be able to resume any
feature at any phase from the files alone.

## Layout

```
specs/
├── metrics.jsonl            # append-only outcome ledger (one JSON object per line)
├── constitution.md          # OPTIONAL: durable project principles (MUST/SHOULD),
│                            #   loaded at plan + verify; conflicts are CRITICAL —
│                            #   adjust spec/plan, never dilute the principle
├── archive/                 # shipped features moved out of the working set
│                            #   (invisible to the board and the edit gate)
└── <slug>/                  # one folder per feature, slug = NNN-kebab-name (001-due-dates)
    ├── spec.md              # requirements phase output (FR-IDs + EARS criteria)
    ├── plan.md              # plan phase output (FR-traced tasks, Affected files)
    ├── verification.md      # verify phase output (evidence + per-FR verdicts)
    └── status.json          # machine-readable state — THE contract for tooling/UIs
lessons/
├── INDEX.md                 # one line per lesson: - [title](file.md) — hook
└── *.md                     # one fact per file, with inclusion frontmatter
```

The authoritative status.json schema is `schema/status.schema.json` in the
plugin (a PostToolUse hook validates every write against it). Optional fields
beyond the example below: `track` ("full" default | "quick"), `tasks`
({done, total}, mirrored by implement), `verifyAttempts` (failed verify
passes — at 2 the auto-loop stops and hands to the user). Quick-track
features have no plan.md — set `artifacts.plan` to `"spec.md#mini-plan"`;
the edit gate scopes them via the mini-plan's `Affected files:` line.

## status.json (schemaVersion 1)

```json
{
  "schemaVersion": 1,
  "feature": "Add due dates to tasks",
  "slug": "001-due-dates",
  "phase": "requirements",
  "gates": {
    "spec_approved":       { "approved": false, "by": null, "at": null },
    "plan_approved":       { "approved": false, "by": null, "at": null },
    "verification_passed": { "approved": false, "by": null, "at": null },
    "docs_complete":       { "approved": false, "by": null, "at": null }
  },
  "artifacts": {
    "spec": "spec.md",
    "plan": "plan.md",
    "verification": "verification.md"
  },
  "updatedAt": "2026-08-02T12:00:00Z"
}
```

Rules:

- `phase` is one of: `requirements`, `plan`, `implement`, `verify`, `document`, `done`.
- Phases advance strictly in order; never skip one.
- **Tracks.** `track: "full"` (default) runs all five phases. `track: "quick"`
  — for small, low-risk work and most bugfixes — folds planning into the spec
  gate: the spec carries a mini-plan (approach + tasks + affected files,
  ≤ 15 lines), and ONE approval records `spec_approved` AND `plan_approved`
  together (same by/at, phase → implement). The track is proposed by the
  requirements phase and confirmed by the user at approval. Verify and
  document still run (leaner: no second reviewer, lessons optional).
- **Phases auto-continue.** When a phase completes and the next gate is open
  (or is a machine gate that just passed), flow directly into the next phase —
  do not wait for another command. Stop only at a closed human gate, on a
  verification failure that needs the user, or when unattended.
- `spec_approved` and `plan_approved` are HUMAN gates, recorded when — and only
  when — the user explicitly approves the named artifact after seeing it:
  - Present the artifact (or its faithful summary), then ask directly:
    "Approve this spec/plan, or should I revise it?"
  - Only an explicit affirmative to that question counts. A passing "ok",
    "continue", or conversational momentum NEVER counts — never infer approval.
  - The user may also volunteer approval in any later session ("approve the
    plan for 003-x") — same recording, provided they've had the artifact.
  - Before recording, sanity-check: the artifact exists and is non-trivial,
    the feature is in the matching phase, and (spec) unresolved Open questions
    are surfaced and explicitly accepted.
  - Record `by` = git `user.name` (fallback `$USER`), `at` = current UTC ISO.
    Approving spec sets `phase: "plan"`; approving plan sets `phase: "implement"`.
- **Standing approval directives.** A present user may explicitly delegate
  routine approvals ("stop asking for approvals", "proceed through the
  gates"). From then on: still present each artifact + checklist, then record
  the gate as `by: "<git user.name> (standing directive)"` and continue
  WITHOUT a blocking question. The directive must be explicit — momentum
  still never counts — and it does not cover genuine forks: unresolved Open
  questions, revised-after-feedback artifacts, destructive scope changes, or
  real uncertainty still get a direct question.
- **UNATTENDED RUNS NEVER SELF-APPROVE.** No human present → the gate stays
  closed, the workflow stops there and reports what awaits review. A standing
  directive given in conversation does not carry into unattended runs.
- **Async review questionnaires.** When an unattended run stops at a human
  gate, it also writes `specs/<slug>/REVIEW.md`: the approval checklist as
  numbered questions with blank `Answer:` lines, ending with
  `Approve this <spec|plan>? (yes/no):`. The user answers in their editor
  whenever. Any later session that finds a REVIEW.md whose final line is an
  explicit yes/approved records the gate normally (`by` = git user.name,
  `at` = now), addresses the other answers (revise → re-ask via a fresh
  REVIEW.md), then deletes the file. An unanswered or negative REVIEW.md
  never advances anything.
- `verification_passed` is a MACHINE gate: the verify phase sets it (`by:
  "sdlc-verify"`) only with green test output captured as evidence in
  verification.md. Never set it without that evidence.
- `docs_complete` is set by the document phase; it also sets `phase: "done"`.
- Always refresh `updatedAt` (UTC ISO 8601) on every write.
- Never edit gate fields to work around a block. If a gate is wrong, tell the user.

## metrics.jsonl

One line appended per verify run and per completed feature:

```json
{"at": "<iso>", "slug": "001-due-dates", "event": "verify", "testsGreenFirstTry": true, "reviewFindings": 2, "planRevisions": 0, "coverage": 100}
{"at": "<iso>", "slug": "001-due-dates", "event": "done", "lessonsWritten": 1}
```

These ground retros in data ("verify failed first-pass in 6 of 10 runs") instead
of vibes. Add fields freely; never remove or rewrite existing lines.

## Resolving the active feature

Commands that take an optional `<slug>`: if omitted, look for exactly one
feature whose phase matches the command's expected input phase. If zero or
several match, list them and ask the user which one.
