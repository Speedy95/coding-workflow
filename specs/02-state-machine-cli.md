# Unit B — v1.3.0 "state machine + CLI"

Goal: close the state-machine gaps (IMPROVEMENTS-2.md P1) and eliminate
hand-authored bookkeeping (P2) via a plugin-shipped CLI. Depends on Unit A
(invariant checks in validate_status.py, hardened find_root).

> **Session-2 amendments (v1.2.1)** — read
> `reports/session-2-handoff.md` first. Deltas that bind this spec:
> baseline is **135 tests** (a post-Unit-A review round shipped v1.2.1);
> any launcher that invokes the CLI must use the hooks.json pattern
> (`[ -f script ] || exit 0`, then `python` → `python3` fallback);
> the document phase is now **docs-only** (`.md/.rst/.txt` in scope) —
> B4's skill/command rewrites must not instruct code edits there;
> the CLI must always write both `tasks.done` and `tasks.total`;
> commit as several small reviewable commits, not one per unit.

## B1. `bin/sdlc_state.py` — the state CLI

New file `marketplace/plugins/sdlc/bin/sdlc_state.py` (stdlib only,
argparse, one file). [VERIFY] plugin `bin/` is added to Bash PATH while
enabled — check plugins docs; fallback: skills/commands call it via
`python "${CLAUDE_PLUGIN_ROOT}/bin/sdlc_state.py"`.

Subcommands (all: resolve repo root like gate_check A2; all writes stamp
`updatedAt` with real `datetime.now(timezone.utc)`; all validate result
against the same invariants as validate_status before writing — refuse
with exit 2 on violation):

- `init <slug> --feature "<title>" [--track quick|full]` — create
  `specs/<slug>/status.json` (schemaVersion 1, phase requirements, gates
  unapproved). Slug numbering: next NNN = max across `specs/*/` AND
  `specs/archive/*/` + 1 (fixes collision gap).
- `approve <slug> <spec|plan> --by "<name>" [--note "standing directive"]`
  — set gate, advance phase (spec→plan, plan→implement; quick track:
  `approve <slug> spec` sets BOTH gates, phase→implement). Refuses if
  artifact file missing.
- `set-phase <slug> <phase>` — legal transitions only
  (requirements→plan→implement→verify→document→done; verify→implement;
  any→abandoned). Sets machine gates on the transitions that imply them
  (document: verification_passed must already be true — refuse otherwise;
  done: sets docs_complete with by "sdlc-document").
- `mirror-tasks <slug>` — parse plan.md, count `- [x]`/`- [ ]` under
  `## Tasks`, write `tasks: {done,total}`. plan.md checkboxes become the
  single ground truth (fixes desync gap). Quick track: `--done N --total M`
  explicit flags instead.
- `verify-result <slug> --red|--green` — green: set verification_passed
  (by "sdlc-verify"), phase→document, reset `verifyFails` to 0. red:
  increment `verifyFails`, phase→implement; exit code 3 when
  verifyFails ≥ 2 (signals the 2-strike stop to the caller).
- `metric <slug> --event verify|done [--field k=v ...]` — append one line
  to specs/metrics.jsonl with real timestamp; numbers parsed as numbers.
- `review write <slug> --gate spec|plan --question "..." ...` /
  `review check <slug>` — create REVIEW.md from questions + approve line;
  check parses an answered file: prints APPROVED/REJECTED/UNANSWERED and
  the answers; APPROVED+`--record --by "<name>"` records the gate and
  deletes the file; REJECTED renames it `REVIEW-rejected-<date>.md`
  (fixes the dead-end gap) and prints the feedback for the agent to act on.
- `abandon <slug> --reason "..."` — phase→abandoned, reason stored as
  `abandonReason`, appends metrics event `abandoned`.
- `archive <slug>` — refuses unless phase done or abandoned; moves dir to
  `specs/archive/<slug>/`.
- `lint <slug>` — structure check: spec.md has `## Requirements` with
  FR-IDs, `## Risk`, `## Out of scope`; quick track additionally the
  `Affected files:` line; plan.md (full track) has `## Affected files` +
  `## Tasks` with checkboxes. Exit 2 + list of misses.

## B2. Schema + hook changes

- `schema/status.schema.json`: phase enum += `abandoned`; rename
  `verifyAttempts` → `verifyFails` (description: "failed verify passes;
  reset on green"); += `planRevisions` (int ≥0), `abandonReason` (string).
- `validate_status.py`: mirror the above via the schema-loading mechanism
  from Unit A; accept EITHER verifyAttempts or verifyFails during a
  deprecation window [DECIDE: one minor version], warn on the old name via
  stderr message but exit 0.
- `gate_check.py`: `abandoned` is never an approved phase (no change
  needed — approved set is explicit — but add a test proving it).
- `session_state.py` + `build_dashboard.py`: abandoned features hidden
  from the board and injection by default; dashboard shows them only in a
  collapsed "abandoned" group [DECIDE: hidden entirely in SessionStart].

## B3. Plan re-approval on scope growth

- `tdd-loop/SKILL.md` scope-discipline bullet: adding an Affected-files
  entry mid-implement = run `sdlc_state.py plan-revised <slug>` (new
  subcommand: increments `planRevisions`) AND re-affirm with the user
  (attended: one-line confirmation covered by standing directives;
  unattended: `review write` a single-question REVIEW.md and STOP).
- `verification/SKILL.md` metrics line: `planRevisions` now read from
  status.json instead of "counted" from memory.

## B4. Skills/commands adopt the CLI

Rewrite the bookkeeping steps (NOT the workflow logic) in: requirements.md,
plan.md, implement.md, verify.md, document.md commands + sdlc-state,
tdd-loop, verification, retro skills — each "edit status.json / append
metrics / write timestamps" instruction becomes the corresponding CLI call.
sdlc-state keeps the JSON contract documentation (the CLI is the writer,
the file stays the source of truth readable by everything else).
Manual editing remains legal for humans; the invariant hook still guards.

## B5. Monorepo + identity documentation (docs-only items)

- sdlc-state skill: add "one SDLC root per repo; nearest `specs/` wins for
  nested roots — do not nest" and "approver identity comes from git
  user.name — it is an audit hint, not authentication".
- README Enforcement section: state the `specs/`-is-writable trust
  assumption explicitly (audit 5.11) and the residual Bash gaps list.

## Verification plan

- pytest: new `tests/test_sdlc_state.py` covering every subcommand happy
  path + refusals (illegal transition, approve without artifact, verify
  2-strike exit 3, archive of in-flight feature refused, slug numbering
  across archive, REVIEW.md rejected path). Target ≈ +20 tests.
- Round-trip: drive a synthetic feature init→approve→…→done purely via
  CLI; validate_status must never fire; resulting status.json passes the
  schema parity test from Unit A.
- Migration: demo-app's three status.json files updated
  (verifyAttempts→verifyFails) in the same commit; suite + dashboard
  rebuild green.
