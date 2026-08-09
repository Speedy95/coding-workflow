---
description: Execute an approved plan task-by-task with TDD
argument-hint: [slug]
---

Run the SDLC implement phase for: $ARGUMENTS

1. Load the `sdlc:sdlc-state` and `sdlc:tdd-loop` skills. Resolve the slug
   (argument, or the single feature in phase `implement`).
2. Check the gate: `plan_approved.approved` must be true. If not: present the
   plan and ask for approval per the sdlc-state skill (unattended: stop and
   report).
3. Execute the plan (quick track: the spec's Mini-plan) task by task per the
   tdd-loop skill: red → green → refactor, suite green after every task,
   checkbox in plan.md AND `tasks: {done, total}` mirrored to status.json as
   you go. Tasks marked [P] may be dispatched to `implementer` agents in
   parallel — use worktree isolation when doing so, and never parallelize
   tasks whose file sets overlap; when in doubt, run sequentially.
4. Honor the skill's scope discipline: plan.md is updated BEFORE touching any
   file it doesn't name; deviations and surfaced issues are recorded there.
5. When every task is checked off and the suite is green: set `phase: "verify"`
   and `updatedAt` in status.json, report briefly — tasks completed, final test
   run result, deviations — then continue straight into the verify phase
   (follow `/sdlc:verify`'s steps; no new command needed).

If a task is infeasible as written, stop and revise the plan with the user
rather than improvising around it.
