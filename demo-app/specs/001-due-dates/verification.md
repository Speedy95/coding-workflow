# Verification: Add due dates to tasks

## Test evidence
```
$ python -m pytest
tests\test_taskler.py ...............                                    [100%]
============================= 15 passed in 0.06s ==============================
```
(6 pre-existing tests + 9 added by this feature; suite was green on the verify
phase's first run.)

## Spec compliance
Adversarial review (sdlc:adversarial-reviewer, fresh context, read-only + test
execution) attempted to refute each requirement:

- R1 `add --due` stores date, plain `add` unchanged — **met** (taskler.py:37-49; CLI probe)
- R2 invalid date → exit 2, clear error, nothing stored — **met**; attacked with
  lenient-ISO forms (`20260815`, `2026-8-5`, `2026-W33-1`, `+002026-08-15`,
  `2026-02-30`, empty, trailing space) — all rejected by the round-trip check
- R3 date shown, undated rows byte-identical — **met**
- R4 dated ascending first, undated insertion order — **met** (stable-sort tie
  behavior probed)
- R5 leading `!` on overdue open tasks, strict `<`, never on done — **met**
  (also probed against the real clock end-to-end)
- R6 pre-feature tasks.json loads as undated — **met** (absent-key convention)

All five acceptance criteria verified (CLI probes + suite).

## Review findings
- F1 (minor, deferred): `list --all` now sorts completed dated tasks into the
  dated block; pre-feature `--all` was pure insertion order. Spec-silent — not
  a violation. → recorded under "Surfaced issues" in plan.md for a future
  feature/decision.
- F2 (info): CLI `list` path pinned only via `format_tasks` + manual probes,
  not an automated CLI test. Coverage hygiene, behavior confirmed correct.
- F3 (info): equal-due tie order relies on Python's sort stability
  (language-guaranteed; probed correct). No test pins it.

No unresolved spec violations. Verdict: **pass**.
