# taskler (SDLC demo app)

A deliberately tiny JSON-file-backed task list CLI, used as the playground for
the `sdlc` Claude Code plugin.

```
python taskler.py add "Buy milk"
python taskler.py add "Pay rent" --due 2026-08-15   # due date, YYYY-MM-DD
python taskler.py list          # open tasks (use --all to include done)
python taskler.py done 1
python taskler.py remove 2      # asks "remove? [y/N]"; --yes skips the prompt
```

`list` shows due dates as `(YYYY-MM-DD)` and orders dated tasks first
(soonest due on top), then undated ones. Overdue tasks are marked with a
leading `!`. An invalid `--due` value is rejected with exit code 2.
`list --all` appends completed tasks after the open ones, in the order they
were added (their due dates don't re-sort them, and they never carry `!`).
`remove` shows the task and asks for confirmation before deleting (`y`/`yes`
confirms; anything else, or a non-interactive stdin, safely aborts with exit
1). Unknown ids exit 1 without touching the store.

Run tests: `python -m pytest`

## Workflow

All feature work in this repo goes through the SDLC plugin: start with
`/sdlc:requirements <brief>`, then review and approve the spec and the plan in
conversation — the feature flows through implement → verify → document on its
own. See `/sdlc:status` or `/sdlc:dashboard`.

- `specs/` — per-feature state (spec, plan, verification, status.json)
- `lessons/` — accumulated repo knowledge, loaded during planning

A plugin hook blocks code edits while no feature has an approved plan — try
asking Claude to edit `taskler.py` before approving one.

## Demo feature ideas

- Add due dates to tasks (`add --due 2026-08-15`, show and sort in `list`)
- Add priorities (high/normal/low) with sorting
- `remove` command with confirmation
