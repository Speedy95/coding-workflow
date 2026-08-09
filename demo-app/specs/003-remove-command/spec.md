# Add a `remove` command

## Problem
Tasks can only be added or completed, never deleted — mistyped or obsolete
entries stay in the list forever. Deletion is destructive, so a typo'd id must
not silently destroy data: removal needs a confirmation step.

## Requirements
- FR-1: `remove <id>` shall delete the task with that id from the store after
  confirmation, and report what was removed.
- FR-2: Before deleting, the command shall print the task (same row format as
  `list`) and ask `remove? [y/N]` on stdin; only `y`/`yes`
  (case-insensitive, surrounding whitespace ignored) confirms — any other
  input, empty input, or non-interactive EOF aborts with exit 1 and deletes
  nothing.
- FR-3: `remove <id> --yes` shall skip the prompt and delete immediately.
- FR-4: An unknown id shall fail with a clear error, exit 1, store unchanged.
- FR-5: Remaining tasks keep their ids and order after a removal.

## Acceptance criteria (EARS)
- AC-1 (FR-1): WHEN `remove 2 --yes` runs against a store containing task 2,
  THE SYSTEM SHALL persist a store without task 2 and print
  `removed 2: <title>`.
- AC-2 (FR-2): WHEN `remove 2` receives `y` on stdin, THE SYSTEM SHALL delete
  task 2; WHEN it receives `n`, empty input, or EOF, THE SYSTEM SHALL exit 1
  and leave the store byte-identical.
- AC-3 (FR-2): WHEN prompting, THE SYSTEM SHALL show the task's `list`-style
  row before asking.
- AC-4 (FR-4): IF the id does not exist, THEN THE SYSTEM SHALL print an error
  naming the id, exit 1, and leave the store unchanged.
- AC-5 (FR-5): WHEN a task is removed, THE SYSTEM SHALL leave every other
  task's id, title, done and due fields unchanged, in their original order.

## Out of scope
- Id-reuse prevention: max+1 assignment stays; a freed highest id may be
  reassigned by a later `add` (accepted by Alex 2026-08-03).
- Bulk removal, `remove --all`, undo.

## Risk
normal — destructive data operation, mitigated by confirmation + tests.

## Open questions
(none — confirmation UX and id policy decided by Alex 2026-08-03)

## Amendments
- 2026-08-03: FR-2 widened to ignore surrounding whitespace in the
  confirmation answer (` y ` confirms) — implementation strips input for
  readline-padding tolerance; surfaced by verify finding F2, pinned by test.
