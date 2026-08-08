# sdlc plugin improvement program — spec index

Two-layer spec system (per the specs-workflow convention): workers read
`00-orchestrator.md` first, then their assigned unit spec. Source analysis
with all evidence: `../IMPROVEMENTS-2.md` (2026-08-09, against plugin
v1.1.0). Reports land in `specs/reports/`.

| Unit | Spec | Release | Scope |
|------|------|---------|-------|
| A | [01-honest-gate.md](01-honest-gate.md) | v1.2.0 | Fix 8 confirmed enforcement bugs + close the test blind spots |
| B | [02-state-machine-cli.md](02-state-machine-cli.md) | v1.3.0 | Abandoned state, plan re-approval, verifyFails, slug hygiene, `bin/sdlc_state.py` CLI, skills adopt it |
| C | [03-verification-lessons.md](03-verification-lessons.md) | v1.4.0 | Ablation check, UNRESOLVED verdict, reviewer de-bias, OKF v0.2 lessons, REVIEW.md v2, spike phase — dogfooded through the workflow itself |
| D | [04-platform-design.md](04-platform-design.md) | v2.0.0 | Design doc ONLY: skill-scoped hooks, defer/affected_paths, new hook events, metrics v2, MCP sketch, eval strategy |

Order: A → B → C strictly serialized (one unit per session — plugin
snapshots at session start). D may run parallel to C.

## Current state audit (baseline for workers)

- Plugin v1.1.0 installed user-scope; marketplace repo at `3297f0a`,
  demo-app at `66755f1`; 36/36 tests green.
- demo-app: 3 features shipped (001 pre-1.0 format, 002 quick, 003 full),
  2 lessons (v1.1.0 frontmatter), metrics.jsonl has 6 events.
- Known-broken (confirmed): the 8 P0 items in IMPROVEMENTS-2.md — the
  gate currently over-allows (root files, unscreened rm/mv, false roots,
  scope union) and over-blocks (.github paths, document phase, `1>` vs
  `1> file` false positives on logs).
- This `specs/` folder itself must NOT gain status.json files (it would
  become a live gate root after Unit A only if it had features — keep it
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
- Document phase gets plan-scoped edit rights + root CHANGELOG* always
  allowed (A4).
- Scratch-extension redirect allowlist `.log/.txt/.out/.tmp` (A5).
- verifyAttempts → verifyFails with one-minor-version deprecation (B2).
- Abandoned features hidden from SessionStart, collapsed group on
  dashboard (B2).
- Ablation required on full track, optional on quick (C1).
- Lessons promote to human-reviewed only on explicit confirmation —
  standing directives do NOT auto-promote (C3).
- Gate-approval questions never default to yes on TTL expiry; non-gate
  questions default proceed-with-note after 7 days (C4).
