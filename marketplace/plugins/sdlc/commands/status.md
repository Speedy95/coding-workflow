---
description: Show all SDLC features, their phases and gate states
---

Show the SDLC status board.

1. Read every `specs/*/status.json` (load the `sdlc:sdlc-state` skill if you
   need the schema). If there are none, say the workflow has no features yet
   and point at `/sdlc:requirements`.
2. Render a table: slug, feature, track, phase (+ task progress like 3/5 when
   present), the four gates (✓ approved / · open, with `by` for approved human
   gates), and updatedAt. Archived features (specs/archive/) are excluded.
3. Below the table, one line per in-flight feature naming its next action
   (e.g. "001-due-dates → spec awaits review: read specs/001-due-dates/spec.md,
   then say 'approve the spec'").
4. If `specs/metrics.jsonl` exists and has 3+ verify events, add a one-line
   health note (e.g. first-try green rate) — data, not vibes.

Read-only: this command never modifies state.
