# Add due dates to tasks

## Problem
Tasks in taskler have no notion of time. Everything sits in one undifferentiated
list, so the user can't see what needs doing soon versus someday — the most
basic reason people keep a task list at all.

## Requirements
- R1: `add "<title>" --due YYYY-MM-DD` stores the due date with the task;
  `add` without `--due` behaves exactly as today.
- R2: An invalid `--due` value (not a real date in YYYY-MM-DD form) exits
  non-zero with a clear error and stores nothing.
- R3: `list` shows the due date as `YYYY-MM-DD` next to tasks that have one;
  undated tasks render exactly as today.
- R4: `list` orders open tasks: dated tasks first in ascending due order,
  undated tasks after them in current (insertion) order.
- R5: Overdue open tasks (due date strictly before today) are marked with a
  leading `!` in `list` output.
- R6: Existing `tasks.json` files from before this feature load without error;
  their tasks are treated as undated.

## Out of scope
- Times of day and timezones (dates only, compared in local time).
- Editing or removing a due date after creation.
- Reminders, notifications, recurring tasks.
- Sort options/flags for `list`.

## Acceptance criteria
- `python taskler.py add "Pay rent" --due 2026-08-15` then `list` shows
  `2026-08-15` on that row, ordered before any undated task.
- `add "x" --due 15.08.2026` exits non-zero, prints an error naming the
  expected format, and `list` is unchanged.
- With a task due yesterday, `list` shows it first with a `!` marker.
- A `tasks.json` written by the current version still loads and lists.
- Full pytest suite green.

## Open questions
(none — out-of-scope list above is the proposed boundary)
