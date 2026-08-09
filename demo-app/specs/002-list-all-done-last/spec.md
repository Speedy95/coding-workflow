# Fix: `list --all` orders completed tasks into the dated block

## Problem
The due-dates feature (001) made `format_tasks` sort every visible dated task
into the dated-ascending block — including completed ones. Pre-feature
`list --all` was pure insertion order, so the reordering shipped as a
spec-silent side effect (adversarial review finding F1). Decision: completed
tasks belong at the end, not interleaved with open work.

## Repro
Steps (fresh store):
```
taskler add "Old chore" --due 2026-07-01   # then: taskler done 1
taskler add "Buy milk"
taskler list --all
```
**Actual:** `[x] 1: Old chore (2026-07-01)` is listed FIRST (sorted into the
dated block, above open tasks).
**Expected:** open tasks first (dated ascending, then undated in insertion
order — same as plain `list`), completed tasks after them.

## Requirements
- FR-1: `list --all` shall order open tasks exactly as plain `list` does
  (dated ascending, then undated in insertion order), before any completed task.
- FR-2: Completed tasks shall appear after all open tasks, in insertion order,
  regardless of due date.
- FR-3: Row formatting is unchanged: due date shown in parentheses; leading
  `!` only on open overdue tasks (never on completed).

## Acceptance criteria (EARS)
- AC-1 (FR-1, FR-2): WHEN `list --all` renders a store containing a completed
  dated task and open tasks, THE SYSTEM SHALL print all open rows first
  (dated ascending, then undated) and the completed rows after them — the
  repro above passes, suite stays green.
- AC-2 (FR-2): WHEN several completed tasks are visible, THE SYSTEM SHALL
  print them in insertion order, ignoring their due dates.
- AC-3 (FR-3): WHILE a completed task is overdue, THE SYSTEM SHALL render it
  without the `!` marker and with its date in parentheses.

## Out of scope
- Plain `list` ordering (unchanged by design).
- New sorting flags/options; changes to storage or other commands.

## Risk
low — display-only change in one function, no data or CLI surface changes.

## Open questions
(none — ordering decision made by Alex 2026-08-03: done-last)

## Amendments
- 2026-08-03: shipped as specified — no behavioral deltas. Verify finding F1
  (low) strengthened FR-1's test pin (multiple open dated tasks under `--all`);
  no FR/AC change.

## Mini-plan (track: quick)
Approach: in `format_tasks`, partition `visible` into open/done before the
dated/undated split; sort only open tasks; append done tasks in insertion order.
Tasks:
1. Red: repro test at `format_tasks` level (completed dated task sorts after
   open undated) + done-insertion-order case (AC-2) + no-`!`-on-done (AC-3).
2. Green: reorder logic in `format_tasks`.
3. CLI-level pin: one test through `main()` for `list --all` (per lesson,
   `monkeypatch.chdir(tmp_path)`).
Affected files: `taskler.py`, `tests/test_taskler.py`
