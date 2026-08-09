# Verification: Add a `remove` command

## Test evidence
```
$ python -m pytest
tests\test_taskler.py ................................                   [100%]
============================= 32 passed in 0.13s ==============================
```
(23 pre-existing + 9 by this feature; green on the verify phase's first run,
and again after hardening two tests per review findings F1/F2.)

## Requirement coverage
Adversarial review (sdlc:adversarial-reviewer, fresh context, read-only + test
execution, live CLI probes in a scratch cwd) attempted to refute each FR:

| FR | verdict | evidence |
|----|---------|----------|
| FR-1 remove after confirmation + report | met | taskler.py:62-69,131-146; test_remove_deletes_and_persists; test_cli_remove_yes_deletes_and_reports (exact string); double-removal probe errors cleanly |
| FR-2 prompt row + [y/N], abort on anything else/EOF | met | taskler.py:137-144; y/YES/" y " confirm, n/empty/"yes please"/EOF abort exit 1 with byte-identical store (cmp + md5 probes); prompt literal now pinned (prompts == ["remove? [y/N] "]) |
| FR-3 --yes skips prompt | met | test_cli_remove_yes_deletes_and_reports runs with unpatched input under closed stdin — a prompt would crash it; probe shows no prompt output |
| FR-4 unknown id: named error, exit 1, store unchanged | met | lookup precedes the --yes branch (taskler.py:133-136); probes incl. empty store (no tasks.json created); byte-compare tests |
| FR-5 survivors keep id/order/fields | met | list.remove, no re-indexing; test_remove_keeps_other_tasks_intact covers id/title/done/due; 5-task probe |

- AC-1..AC-5 — all pass (AC-3 attacked via overdue and done tasks: prompt row
  identical to the `list` renderer incl. `!`, by construction and now pinned
  by test with a past due date).

## Review findings
- F1 (low, **fixed**): prompt literal `remove? [y/N] ` was untested (all tests
  discarded input()'s prompt arg) → prompt captured and asserted exactly.
- F2 (low, **fixed**): `.strip()` lets `" y "` confirm — untested widening of
  the spec's letter → pinned by parametrize; folded into the spec as an
  amendment at document time (deliberate leniency).
- F3 (info): non-integer id exits 2 via argparse — spec-silent, consistent
  with `add`/`done`.
- F4 (info): declined/EOF abort prints nothing — spec doesn't require a
  message; UX note only.
- F5 (info, addressed): overdue-`!` prompt-row consistency was untested →
  covered by the strengthened AC-3 test.

No unresolved spec violations. Verdict: **pass**.
