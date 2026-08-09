# taskler

Tiny task-list CLI (`taskler.py`) with pytest tests in `tests/`. Run the suite
with `python -m pytest`.

This repo uses the **sdlc plugin workflow**: all feature work goes through
`/sdlc:requirements` → `/sdlc:plan` → `/sdlc:implement` → `/sdlc:verify` →
`/sdlc:document`, with state in `specs/` and repo knowledge in `lessons/`.
Check `/sdlc:status` before starting work. Do not edit code outside an approved
implement phase — a hook enforces this; if it blocks you, the answer is to
advance the workflow, not to work around the hook.
