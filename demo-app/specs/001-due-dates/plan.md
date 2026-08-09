# Plan: Add due dates to tasks

## Approach
Store the due date as an optional `"due": "YYYY-MM-DD"` string on the task dict
(absent key = undated, which makes R6 backward-compat automatic). Validate at
add time with `datetime.date.fromisoformat` via an argparse `type=` converter,
so invalid input fails inside argparse with a clear non-zero exit (R2). All
display logic — date column, ordering, overdue marker — lives in
`format_tasks`, which is the existing pure, tested seam; it gains an injectable
`today` parameter so overdue tests are deterministic.

Rejected alternatives: storing epoch timestamps (unreadable in tasks.json for
a tool this small); sorting inside `main`'s list handler (moves logic off the
tested pure function); a separate dates file (second store to corrupt).

Lessons applied: none — lessons/ is empty (first feature through the workflow).

## Affected files
- `taskler.py` — `add_task` (optional validated `due`), `format_tasks`
  (column, ordering, `!` marker, `today` param), `main` (`add --due` wiring)
- `tests/test_taskler.py` — new tests per task below

## Tasks
- [x] 1. **`add_task` stores an optional due date** — change: `due: str | None`
  param, validated (`date.fromisoformat`), stored only when present; test:
  stored verbatim; invalid string raises `ValueError`; omitted → no `due` key.
- [x] 2. **CLI wiring for `add --due`** — change: argparse `--due` with a
  `type=` converter that re-raises as `ArgumentTypeError` naming the
  `YYYY-MM-DD` format; test: `main(["add","x","--due","2026-08-15"])` persists
  the date; `main(["add","x","--due","15.08.2026"])` raises `SystemExit` with
  code 2 and the store stays empty.
- [x] 3. **`format_tasks` shows dates and orders dated-first** — change: render
  `YYYY-MM-DD` after the title for dated tasks; order open tasks dated
  (ascending due) then undated (insertion); test: mixed list renders in spec
  order with dates shown, undated rows byte-identical to today's format.
- [x] 4. **Overdue marker** — change: `format_tasks(..., today: date | None)`
  (default `date.today()`); open tasks with `due < today` get leading `!`;
  test: with injected `today`, yesterday-due task is marked and sorted first,
  today-due task is not marked.
- [x] 5. **Backward compat (R6)** — test-only: a store written in the current
  pre-feature shape (no `due` keys) loads, lists, and completes without error.

Suite must be green after every task.

## Test plan
`python -m pytest` — existing 6 tests stay green; ~8 new tests added across
tasks 1–5.

## Risks
- `date.today()` in display logic → made injectable (task 4); only `main`
  uses the real clock.
- `tasks.json` schema grows → absent-key convention keeps old files valid
  (task 5 proves it).

## Surfaced issues
- `list --all` now sorts completed dated tasks into the dated block (pre-feature
  it was pure insertion order). Spec-silent; decide and pin with a test in a
  future feature. (From verification finding F1.)
