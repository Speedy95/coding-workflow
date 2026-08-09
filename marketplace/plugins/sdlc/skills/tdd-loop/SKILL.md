---
name: tdd-loop
description: The implement phase's red-green-refactor discipline - one plan task at a time, vacuous-red detection, task progress mirrored to status.json, scope control.
---

# TDD loop

The implement phase executes `plan.md` one task at a time. For each task:

1. **Red** — write the task's test first. Run it. Confirm it fails for the
   RIGHT reason (the feature is missing, not a typo).
   **Vacuous-red check**: if a new test PASSES before the implementation
   exists, it isn't pinning the requirement (e.g. asserting an exit code that
   an unrelated failure also produces). Strengthen the assertion until it
   fails for the feature's absence, or explicitly note why it can only become
   meaningful post-implementation.
2. **Green** — minimum code to pass. Run the failing test, then the full suite.
3. **Refactor** — clean up while green. Suite again.
4. Mark the task done: check it off in plan.md AND mirror progress into
   status.json (`"tasks": {"done": n, "total": m}`, refresh updatedAt) — the
   dashboard, session-start injection, and any resumed session read it.
   Quick track (no plan.md): the status.json mirror IS the task record — the
   spec's mini-plan list stays untouched.

Never proceed on a red suite. Never weaken or delete a failing test to reach
green — a failing test is information.

## Scope discipline

- Touch only files the plan names — the edit gate enforces this. If reality
  demands another file, update **plan.md's Affected files first** (entry +
  reason; quick track: the spec mini-plan's single `Affected files:` line),
  then edit.
- A wrong/infeasible task: stop and revise the plan with the user (unattended:
  record the deviation prominently in plan.md). Count revisions — verify
  reports them to metrics.
- Unrelated discoveries go to plan.md "Surfaced issues", not into this change.

## Done

Every task checked off, suite green → set `phase: "verify"`, final task
mirror, and continue into the verify phase.
