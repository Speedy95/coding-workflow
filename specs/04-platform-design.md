# Unit D — v2.0.0 platform DESIGN DOC (no implementation)

Goal: a written, decision-ready design for the v2 enforcement architecture
and metrics schema. Deliverable is ONE document:
`specs/reports/v2-platform-design.md`, presented to Alex for approval
BEFORE any v2 code exists. This unit writes no plugin code and bumps no
version. May run in parallel with Unit C.

## D1. Enforcement architecture comparison

Compare, with concrete hook configs and failure-mode tables:
- **Status quo**: global PreToolUse gate inferring phase from status.json.
- **Skill-scoped**: `hooks:` frontmatter in the implement/verify skill so
  the gate exists only during those phases. [VERIFY] against
  https://code.claude.com/docs/en/hooks — frontmatter hooks schema, the
  Stop→SubagentStop auto-conversion, workspace-trust requirement, and what
  happens when a session crashes mid-skill (does the scoped hook leak?).
- **Hybrid** (expected recommendation): keep a thin global gate for
  defense-in-depth (a session can edit gated files without any skill
  active), add skill-scoped strictness during implement.
Must answer: migration for repos mid-feature during upgrade; behavior in
sessions running the OLD plugin snapshot against a NEW repo state;
graceful degradation when frontmatter hooks are untrusted.

## D2. Permission-flow modernization

- `permissionDecision: "defer"` [VERIFY: semantics — falls through to the
  normal permission flow]: gate stops force-allowing calls it has no
  opinion on (today exit 0 = allow); design when to defer vs allow.
- `PermissionRequest.affected_paths` [VERIFY: payload shape]: evaluate
  replacing our Bash command_targets parsing entirely with
  harness-computed paths; enumerate what coverage would be LOST (does it
  fire for redirects? subshells?) with test transcripts from a scratch
  session; keep our parser wherever affected_paths is blind.
- `updatedInput` rewriting: assess ONE use — auto-inserting `--dry-run`?
  Likely SKIP; justify either way.

## D3. New hook wiring

Design (config + payload handling, no code): **PostCompact** re-inject
current feature/phase/scope so compaction never drops workflow state;
**SessionEnd** append a session metrics event (duration, feature, phase
transitions seen, interruption count); **SubagentStop** record reviewer/
implementer identity + token usage into the feature's metrics;
**PostToolBatch** as a cheaper place than per-call PostToolUse for status
validation [VERIFY each event exists + blocking semantics per docs].
Unattended: `disallowed-tools: AskUserQuestion` in skill frontmatter for
unattended contexts — verify the field name and that REVIEW.md fallback
instructions trigger correctly.

## D4. Metrics schema v2 (ledger stays JSONL)

Field-by-field proposal with rationale, aligned to IMPROVEMENTS-2.md P5:
`run_id` (uuid per phase attempt), `gen_ai.conversation.id`,
`gen_ai.usage.input_tokens`/`output_tokens` (OTel names),
`rejection_class` (agent-failure|process-failure|unknown),
`intervention_class` (none|feedback-loop|human-commit),
`diff_loc`/`files_touched` (batch size), `human_intervention_count`,
`agent_initiated_stop_count`, stability events (`reopened`, `reverted`).
Rules: percentiles-not-means in any reporting; every speed metric paired
with a stability metric; explicitly EXCLUDED (with citations): acceptance
rate, %AI-LOC, self-reported speedup. Migration: additive fields only,
schemaVersion stays 1 for status.json; metrics events get `v: 2`.

## D5. MCP server (design only, build-gated on real need)

~200-LOC stdio server sketch: resources (board summary, per-feature
status), tools (`get_board`, `approve_gate` — requires the same artifact-
seen + explicit-yes contract, recorded with `via: "mcp"`), bundled via
plugin `.mcp.json`. Threat model: approve_gate is remote-writable state —
document why it must NOT ship until authenticated transport is settled.
Recommendation gate: build only when Alex asks for remote approval.

## D6. Eval strategy

- Trajectory assertions: adapt superpowers-evals' pattern (setup.sh /
  story / checks.sh, 3-valued verdict) for two scenarios: "gate blocks
  ungated edit" and "quick-track feature end-to-end".
- promptfoo `skill-used` smoke config for the requirements skill.
- CI: `claude plugin validate --strict` job added to tests.yml.
Estimate tokens/cost per eval run; recommend cadence (pre-release only).

## Report / DoD

The design doc, plus: every [VERIFY] resolved with doc-quote + URL; a
risks section (top 5, with the drift critique and 3-4x token cost of
multi-agent ceremony from IMPROVEMENTS-2.md as anchors); a phased v2
implementation plan (sized units) ready to become specs 05+ after Alex's
review. No code, no version bump, no reinstall.
