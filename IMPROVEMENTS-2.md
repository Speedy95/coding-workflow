# SDLC workflow — full analysis #2 (2026-08-09, against v1.1.0)

Inputs: fresh-eyes internal audit (46 findings, most confirmed by executing
payloads against the hooks), ecosystem research sweep (6 angles, ~40 sourced
findings), MCP/hooks capability research (claims verified against official
docs), and first-person friction notes from the three e2e runs. Prior report:
IMPROVEMENTS.md (v1.0.0). Items marked ✔ were verified by execution.

---

## P0 — Enforcement bugs (the gate lies about what it enforces)

1. ✔ **Root-level file in Affected files unlocks the whole repo root.**
   `posixpath.dirname("taskler.py")` is `""`, and every root-level file
   matches dir `""` — `setup.py`, `Makefile`, `conftest.py` all allowed.
   Nearly every project lists a root-level file. Fix: skip empty dirname.
   (gate_check.py:114-115)
2. ✔ **`lstrip("./")` mangles dot-paths.** `.github/workflows/ci.yml` →
   `github/...`: the listed file is BLOCKED, a wrong path is allowed.
   Fix: `removeprefix("./")`. (gate_check.py:102)
3. ✔ **Deletion/copy/move are entirely ungated.** `rm -rf`, `mv`, `cp`,
   `Remove-Item`, `git checkout --`, `git apply`, `patch <`, `curl -o`,
   `truncate`, `dd` all pass the Bash screen. Deleting a gated file is not a
   gated operation. Fix: extend command_targets extractor.
4. ✔ **Any unrelated `specs/` dir disables gating beneath it.** A common
   `api/specs/` (OpenAPI fixtures) becomes a false root: everything under it
   is silently ungated. Fix: root requires `metrics.jsonl` or `*/status.json`.
5. ✔ **Two approved features union their scopes**, and one unparseable plan
   kills scoping for all. Fix: per-feature fail-open only.
6. ✔ **`phase: document` blocks its own work** — CHANGELOG.md, mkdocs.yml,
   any docs outside `docs/`/README are blocked; the retro skill instructs the
   very edits the gate refuses. Fix: doc-scope unlock for document phase.
7. ✔ Redirect bypasses: `1>` and `>|` unmatched; POSIX `/c/...` paths on
   Windows fail open; `cd` in compound commands mis-resolves targets;
   dotted dir names (`src/v1.2/`) never match as directories.
8. ✔ **validate_status checks shape, not invariants**: accepts
   `phase: implement` with `plan_approved: false` (the exact state the gate
   keys on), `done` without docs_complete, slug ≠ dirname, `updatedAt:
   "yesterday"`. Also only fires on Edit|Write — Bash/NotebookEdit writes to
   status.json are unvalidated, and `specs/archive/**` is skipped entirely.
   Cheapest single robustness win: 4 invariant checks + schema round-trip test
   (the "authoritative" schema/status.schema.json is loaded by nothing ✔ and
   already drifted from the hook mirror ✔).

## P1 — State-machine gaps (real journeys with no path)

9. **No abandoned/parked state.** A dropped feature pollutes the board,
   SessionStart, and the scope union forever. Add `phase: "abandoned"`
   (excluded from board/gate/metrics) + an escape hatch after repeated spec
   rejection.
10. **Plan revision after approval is un-gated.** Growing Affected files
    mid-implement takes effect instantly under the original approval —
    the gate is bypassable by editing plan.md. Fix: `planRevisions` counter
    in status.json (also fixes the metrics field that's currently
    unfalsifiable) + re-affirmation when scope grows. Research corroboration:
    OpenSpec's Zone Guard forbids spec+code edits in the same session —
    same shape as our PreToolUse gate, directly kills spec reward-hacking.
11. **`verifyAttempts` semantics are ambiguous** (schema says failed passes;
    skill increments every pass; demo data proves the drift ✔) and it never
    resets after a recovery — permanent 2-strike lockout. Rename/redefine +
    reset on implement→verify.
12. **Slug collisions after archiving** (next-slug scan ignores
    `specs/archive/`), slug ≠ dirname is unvalidated ✔, rename/split has no
    story. REVIEW.md answered "no" is a dead end (re-flagged every session
    forever ✔). Monorepos: nearest-specs/-wins is undocumented.
13. **tasks.done desyncs from plan.md checkboxes** on crash or subagent
    handoff; derive done from counting `- [x]` instead of mirroring by hand.

## P2 — Bookkeeping automation (the friction I felt personally)

14. **A state CLI (`bin/sdlc_state.py`)**: init/approve/advance/mirror/metric
    subcommands. Removes per-feature: ~10 hand-authored status.json edits,
    **~14 model-invented timestamps** (the model has no clock; demo 001's are
    provably fabricated ✔), 2 metrics lines, INDEX lines, REVIEW.md
    lifecycle. Plugin `bin/` is now on the Bash PATH while enabled — this is
    the intended home. Deterministic-beats-prose is also the strongest
    research theme (drift critique: "I can read them. I can recite them.
    I just don't follow them.").
15. `${CLAUDE_PLUGIN_DATA}` (persistent, survives updates) — verified real;
    candidate home for cross-repo metrics aggregation.
16. Structure linting at the gates: spec missing `## Risk` or the mini-plan
    `Affected files:` line degrades silently today (risk scaling and scoping
    both key on them ✔). A stdlib linter invoked at spec/plan approval.

## P3 — Workflow upgrades (research-backed, high conviction)

17. **Ablation check in verify** (cheapest high-value item): no-op the module
    an FR claims to implement; its tests must go red. Evidence: agents passed
    222/222 hidden tests with dead-code libraries in 11/12 runs
    (arxiv 2606.28430). Generalizes our vacuous-red rule to whole modules.
18. **`UNRESOLVED` per-FR verdict** that blocks the gate and escalates to
    human — calibrated abstention beats reviewer ensembles (which measurably
    don't work: agreement ρ 0.20-0.59 with correctness, 48% error in a top
    model's high-confidence verdicts). Theme: everything wants a third value
    (verdicts, eval outcomes, rejection classes, lesson lifecycle).
19. **De-bias the adversarial reviewer**: strip authorship cues, randomize FR
    order between passes, require every "violated" verdict to cite a runnable
    repro (LLM-judge test-retest reliability on test-gen judging: as low as
    50.4%).
20. **OKF v0.2 migration for lessons** (spec moved under us): `verified[]`
    events → trust tiers (unverified/machine-confirmed/human-reviewed),
    `status: draft|stable|deprecated`, `stale_after`, `usage_count`. Retro
    writes machine-confirmed; Alex's confirmation promotes; verify can
    promote lessons that fired. Add `superseded_by:` (invalidate, never
    delete — recency-wins consensus). Pin a closed `type` enum.
21. **REVIEW.md v2**: risk tier per question, TTL with declared default
    action (auto-reject vs auto-proceed per tier), decision provenance
    (who/what answered under which delegation rule), questions written for
    the least-technical reviewer. Research: 3-tier HITL with async digest for
    the middle tier is the consistent industry pattern.
22. **Spike/learning phase before requirements** (opt-in): the #1 documented
    SDD failure is building on a wrong premise with a clean spec (Nearform).
    Our recon happens at plan time — after requirements lock. A non-gated
    "explore first, brief after" mode formalizes what writing-specs hints at.
23. Optional per-FR `invariant:` field → property test in implement (PBT ∪
    example tests caught 81% vs 69% alone); nightly mutation score as a
    metrics signal, never a PR gate (full line coverage can coexist with 4%
    mutation score).

## P4 — Platform modernization (verified against current docs)

24. **Skill-scoped `hooks:` frontmatter** — the gate could live in the
    implement skill's lifetime instead of inferring phase from status.json
    globally. Big architectural simplification; needs a fresh design pass.
25. **`permissionDecision: defer`** — the gate should defer (fall through to
    normal permission flow) rather than allow on out-of-scope calls it has no
    opinion about. `PermissionRequest.affected_paths` (harness-computed)
    could replace our hand-rolled Bash command parsing entirely.
26. New hook events worth wiring: **PostCompact** (re-inject workflow state
    after compaction), **SessionEnd** (phase-duration + interruption metrics),
    **SubagentStop** (reviewer/implementer accounting), PostToolBatch.
    Stop-hook phase enforcement: skip (fights the user; already deferred).
27. **Unattended hardening**: `disallowed-tools: AskUserQuestion` in
    unattended skill contexts → forces REVIEW.md instead of a silent hang
    (the documented resume-dialog trap).
28. **MCP phase 2** (only if remote approval is wanted): plugin-bundled stdio
    MCP server (~200 LOC) exposing board resources + approve_gate tool for
    claude.ai/Slack/other agents; consume GitHub MCP for issue sync.
    Decision tree: deterministic→hooks, external services→MCP,
    user-initiated→skills.
29. **Eval harness upgrade**: trajectory assertions ("did the gate block?")
    à la superpowers-evals with 3-valued verdicts; promptfoo `skill-used`
    assertion to catch skills silently not triggering; `claude plugin
    validate --strict` in CI.

## P5 — Metrics schema v2

30. Add per-event: `run_id` (survives retries), `rejection_class`
    (agent-failure/process-failure/unknown — 36%/31%/33% split in an 11k-PR
    study), `intervention_class`, batch size (diff LOC, files),
    `human_intervention_count`, `agent_initiated_stop_count`. Pair every
    speed metric with a stability metric (DORA: AI adoption ↑throughput,
    ↓stability). Percentiles, not means. Align token fields to OTel
    `gen_ai.usage.*` names (free now). Deliberately exclude: acceptance
    rate, %AI-authored LOC, self-reported speedup (METR: 19% slower while
    feeling 20% faster). External anchor: AI PRs merge at 32.7% vs 84.5%
    human — our gated flow should demonstrably beat that.

## Explicitly evaluated, not adopted

- Reviewer ensembles (evidence-negative), durable-execution engines
  (Temporal-class — wrong failure category for us), Tessl (closed beta),
  full OKF bundles (still ceremony at our scale), PAM memory interchange
  (watch), SSGM governance middleware (no empirical validation), Stop-hook
  hard phase enforcement (fights the user), Linear/Jira MCP (overkill),
  breadth-first agent catalogs (solve discovery, not discipline).

## Suggested execution order

1. **v1.2.0 "honest gate"**: P0 items 1-8 + tests for the uncovered matrix
   (phase×permission, multi-feature, archive exclusion, serve mode).
2. **v1.3.0 "state machine"**: P1 (abandoned state, plan re-approval +
   planRevisions, verifyAttempts semantics, slug hygiene, checkbox-derived
   tasks) + P2 state CLI (which removes the timestamp/bookkeeping class of
   bugs wholesale).
3. **v1.4.0 "verification deepening"**: P3 items 17-19 + 21; OKF v0.2
   migration (20).
4. **v2.0.0 "platform"**: P4 redesign on skill-scoped hooks + defer +
   affected_paths; metrics v2 (P5); MCP server if remote approval is wanted.
