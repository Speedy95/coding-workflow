# Plan: Add a `remove` command

## Approach
Mirror the existing verb pattern: a `remove_task(task_id, store)` API function
(load → find → delete → save, `KeyError` on unknown id, exactly like
`complete_task`), plus a `remove` argparse subcommand with `--yes`. The
confirmation prompt reuses `format_tasks([task], include_done=True)` for the
list-style row (AC-3) — no row-formatting refactor. Input via `input()`;
`EOFError` (non-interactive) aborts. The CLI handler catches `KeyError` for a
clean exit-1 error (FR-4).
Rejected: extracting a `_format_row` helper (needless refactor when
`format_tasks` on a one-element list already yields the row); a generic
`confirm()` utility (one call site).
Lessons applied: `default-store-binds-at-def-time` — all `main()`-path tests
use `monkeypatch.chdir(tmp_path)`.

## Affected files
- `taskler.py` — `remove_task()`, `remove` subparser with `--yes`,
  confirmation + error handling in `main()`
- `tests/test_taskler.py` — API + CLI tests for removal

## Tasks
- [x] 1. **remove_task API** (FR-1, FR-4, FR-5) — change: add `remove_task`;
  tests: removes the task and persists; unknown id raises KeyError with store
  unchanged; remaining tasks keep id/order/fields (AC-5).
- [x] 2. **CLI `remove --yes`** (FR-1, FR-3) — change: subparser + handler;
  tests: `remove 2 --yes` deletes and prints `removed 2: <title>` (AC-1);
  unknown id prints error naming the id, returns 1, store unchanged (AC-4).
- [x] 3. **Confirmation prompt** (FR-2) — change: no-`--yes` path prints the
  `list`-style row, asks `remove? [y/N]`; tests: `y`/`YES` confirm; `n`,
  empty, EOF abort with exit 1 and byte-identical store (AC-2); prompt output
  contains the row (AC-3).

## Test plan
`python -m pytest` (suite currently 19 green; ~8 new tests in
`tests/test_taskler.py`, CLI paths via `monkeypatch.chdir` +
`monkeypatch.setattr("builtins.input", ...)` / raising EOFError).

## Risks
Destructive operation — tests only ever touch tmp_path stores; abort paths
assert byte-identical store content. Prompt regression risk in non-tty use is
pinned by the EOF test. Rollback: single commit revert.

## Surfaced issues
- `done <unknown-id>` crashes with a raw KeyError traceback (pre-existing,
  taskler.py:111-113) — same clean-error treatment as `remove` deserves its
  own small fix/spec.

## Coherence check
- Coverage FR→tasks: FR-1→(1,2), FR-2→3, FR-3→2, FR-4→(1,2), FR-5→1;
  AC-1→2, AC-2→3, AC-3→3, AC-4→2, AC-5→1. Tasks→FR: 1→(FR-1,4,5),
  2→(FR-1,3,4), 3→FR-2. **Coverage 100% both ways.**
- Ambiguity: no TODO/TBD/placeholders in spec or plan.
- Terminology: "abort"/"store unchanged"/"list-style row" used consistently.
- Budgets: spec < 2 pages, plan < 1.5 pages. No constitution file exists.
