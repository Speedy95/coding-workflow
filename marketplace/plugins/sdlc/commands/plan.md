---
description: Turn an approved spec into an implementation plan for approval
argument-hint: [slug]
---

Run the SDLC plan phase for: $ARGUMENTS

1. Load the `sdlc:sdlc-state` and `sdlc:planning` skills. Resolve the slug
   (argument, or the single feature in phase `plan` per the sdlc-state skill).
2. Check the gate: `spec_approved.approved` must be true in
   `specs/<slug>/status.json`. If not: present the spec and ask for approval
   per the sdlc-state skill (unattended: stop and report). Never plan from an
   unapproved spec.
3. Quick-track features skip this phase (the mini-plan was approved with the
   spec) — if asked to plan one anyway, say so and stop.
4. Follow the planning skill fully: lessons (respect inclusion conditions),
   constitution if present, mandatory codebase recon, FR-traced tasks with
   [P] markers, then the coherence check (coverage matrix + %, ambiguity,
   terminology, budgets). Write `specs/<slug>/plan.md`; refresh `updatedAt`
   (phase stays `plan` — only approval advances it).
5. Present the approach, task list, coherence result, and the plan checklist,
   then ask directly: "Approve this plan, or should I revise it?" Revise and
   re-ask as needed. (Standing approval directive active? Present the same,
   record without asking — see the sdlc-state skill.)
6. On explicit approval, record the plan gate per the sdlc-state skill and
   continue straight into the implement phase. If unattended, write the
   `REVIEW.md` questionnaire (see sdlc-state), stop, and report that the
   plan awaits review.

Do not touch any code before the plan gate is recorded (the edit hook
enforces it).
