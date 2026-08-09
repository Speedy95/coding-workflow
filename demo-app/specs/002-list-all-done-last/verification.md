# Verification: Fix — `list --all` orders completed tasks into the dated block

## Test evidence
```
$ python -m pytest
tests\test_taskler.py ...................                                [100%]
============================= 19 passed in 0.08s ==============================
```
(15 pre-existing tests + 4 added by this fix; green on the verify phase's
first run, and again after strengthening one test per review finding F1.)

## Requirement coverage
Adversarial review (sdlc:adversarial-reviewer, fresh context, read-only + test
execution) attempted to refute each requirement:

| FR | verdict | evidence |
|----|---------|----------|
| FR-1 open-before-done, open order = plain `list` | met | taskler.py:68-73 (shared code path by construction); test_all_lists_open_before_done; test_cli_list_all_prints_open_then_done; CLI repro probe matched spec's Expected |
| FR-2 done last, insertion order, due ignored | met | taskler.py:69,73 (plain filter, never sorted); test_all_done_tasks_in_insertion_order_ignoring_due (non-vacuous: later-due first); all-done CLI probe |
| FR-3 row format unchanged, `!` only open overdue | met | taskler.py:74-79 (`!` guarded by `not t["done"]`); test_done_overdue_renders_plain_and_last pins exact row; pre-existing overdue tests unmodified |

- AC-1 — pass (spec repro reproduced via CLI in scratch dir; pinned at
  format_tasks + CLI level)
- AC-2 — pass (inverted-due done tasks stay in insertion order)
- AC-3 — pass (overdue done: no `!`, date in parens, last)

Edge cases probed clean: all-done store, empty store, undated done task,
equal-due ties (stable sort, same as 001). Out-of-scope drift: only
`format_tasks` changed; plain `list` behavior confirmed unchanged.

## Review findings
- F1 (low, **fixed**): no test pinned dated-ascending order among multiple
  OPEN tasks under `--all` (only transitively via the shared code path) →
  extended test_all_lists_open_before_done with two open dated tasks; suite
  re-run green (19/19).

No unresolved spec violations. Verdict: **pass**.
