---
description: Scaffold the SDLC workflow in the current repository
argument-hint: [--constitution]
---

Initialize the SDLC workflow here: $ARGUMENTS

1. Load the `sdlc:sdlc-state` skill. If `specs/` already has status.json
   files, report the existing state instead of scaffolding.
2. Create (only what's missing — never overwrite):
   - `specs/` with an empty `specs/metrics.jsonl`
   - `lessons/INDEX.md` (header: one line per lesson, curate over accumulate)
   - `.gitignore` entry for `dashboard.html`
   - a short CLAUDE.md section (append if the file exists): feature work goes
     through `/sdlc:requirements`; gates are hook-enforced; check
     `/sdlc:status` before starting work.
3. If `--constitution` was passed (or the user asks): create
   `specs/constitution.md` with 3–5 starter principles elicited from the user
   (MUST/SHOULD form, one line of rationale each) — e.g. test coverage
   expectations, dependency policy, compatibility guarantees. Keep it under a
   page; it is loaded at plan and verify time.
4. Report what was created and point at `/sdlc:requirements <brief>` to start
   the first feature.
