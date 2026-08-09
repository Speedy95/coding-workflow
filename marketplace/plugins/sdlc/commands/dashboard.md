---
description: SDLC board - static snapshot or live local dashboard with artifact reader
argument-hint: [--serve] [output path]
---

Run the SDLC dashboard: $ARGUMENTS

The bundled generator is stdlib-only Python:
`python "${CLAUDE_PLUGIN_ROOT}/dashboard/build_dashboard.py"`

Two modes — pick from the user's arguments:

1. **Snapshot (default)**: run it from the repo root (pass `-o <path>` if the
   user gave an output path). Writes a self-contained `dashboard.html` — the
   full board plus every spec/plan/verification and lesson embedded and
   rendered as markdown in the browser. Safe to open, commit, or publish via
   CI. Report the output path; offer `start dashboard.html` to open it.

2. **Live (`--serve`)**: run with `--serve` (optionally `--port N`, default
   8645) as a background task. It binds 127.0.0.1 only, re-scans `specs/` on
   every poll, and the board auto-refreshes as features move — tell the user
   the URL and that it runs until stopped.

The board groups features by who is blocked: "needs you" (gates awaiting the
user's review, with the approve command one click from the clipboard) first,
then in-progress, shipped, and the repo's lessons. Clicking a strip expands
the gate ledger and artifacts.

If the script errors that no `specs/` exists, the workflow has no state here —
point the user at `/sdlc:requirements`.
