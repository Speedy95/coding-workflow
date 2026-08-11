# sdlc plugin improvement program — spec index

Two-layer spec system (per the specs-workflow convention): workers read
`00-orchestrator.md` first, then their assigned unit spec. Source analysis
with all evidence: `../IMPROVEMENTS-2.md` (2026-08-09, against plugin
v1.1.0). Reports land in `specs/reports/`.

| Unit | Spec | Release | Scope |
|------|------|---------|-------|
| A | **done** — see [reports/unit-a-report.md](reports/unit-a-report.md) (spec removed; in git history) | v1.2.0 | Fixed 8 confirmed enforcement bugs + closed the test blind spots; a post-unit review round shipped v1.2.1 on top ([reports/session-2-handoff.md](reports/session-2-handoff.md)) |
| B | [02-state-machine-cli.md](02-state-machine-cli.md) | v1.3.0 | Abandoned state, plan re-approval, verifyFails, slug hygiene, `bin/sdlc_state.py` CLI, skills adopt it |
| C | [03-verification-lessons.md](03-verification-lessons.md) | v1.4.0 | Ablation check, UNRESOLVED verdict, reviewer de-bias, OKF v0.2 lessons, REVIEW.md v2, spike phase — dogfooded through the workflow itself |
| D | [04-platform-design.md](04-platform-design.md) | v2.0.0 | Design doc ONLY: skill-scoped hooks, defer/affected_paths, new hook events, metrics v2, MCP sketch, eval strategy |

Order: A → B → C strictly serialized (one unit per session — plugin
snapshots at session start). D may run parallel to C.

## Current state (baseline for workers)

- Plugin **v1.2.1** installed user-scope (single monorepo since
  2026-08-09); **135/135 tests green**. The authoritative baseline +
  gotchas live in [reports/session-2-handoff.md](reports/session-2-handoff.md)
  — read it before starting a unit.
- demo-app: 3 features shipped (001 pre-1.0 format, 002 quick, 003 full),
  2 lessons (v1.1.0 frontmatter), metrics.jsonl has 6 events.
- The 8 P0 enforcement bugs from IMPROVEMENTS-2.md are fixed (Unit A),
  plus 10 more bypasses found by the session-2 review (v1.2.1).
- This `specs/` folder itself must NOT gain status.json files (it would
  become a live gate root only if it had features — keep it
  documentation-only).

## Open [VERIFY] questions (workers resolve, reports record)

1. `claude plugin validate --strict` exact syntax (00, DoD).
2. Plugin `bin/` on Bash PATH while enabled (B1) — else CLAUDE_PLUGIN_ROOT
   fallback.
3. OKF v0.2 field shapes from the primary spec (C3) — else minimal
   fallback set.
4. Frontmatter `hooks:` schema, trust requirements, crash behavior (D1).
5. `defer` semantics + `PermissionRequest.affected_paths` payload (D2).
6. PostCompact / SessionEnd / SubagentStop / PostToolBatch existence and
   blocking semantics (D3).

## [DECIDE] defaults already chosen (standing directive — implement, don't ask)

- Scope union across concurrent features stays (A3); documented.
- ~~Document phase gets plan-scoped edit rights (A4)~~ — superseded by
  v1.2.1: document phase is docs-only (`.md/.rst/.txt` in scope); root
  CHANGELOG* always allowed stands.
- Scratch-extension redirect allowlist `.log/.txt/.out/.tmp` (A5) —
  since v1.2.1 only while a feature is approved.
- verifyAttempts → verifyFails with one-minor-version deprecation (B2).
- Abandoned features hidden from SessionStart, collapsed group on
  dashboard (B2).
- Ablation required on full track, optional on quick (C1).
- Lessons promote to human-reviewed only on explicit confirmation —
  standing directives do NOT auto-promote (C3).
- Gate-approval questions never default to yes on TTL expiry; non-gate
  questions default proceed-with-note after 7 days (C4).
