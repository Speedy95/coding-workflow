---
description: Start a new feature or bugfix - gather requirements, size the track, write a spec for approval
argument-hint: <feature brief or bug report>
---

Start the SDLC requirements phase for: $ARGUMENTS

1. Load the `sdlc:sdlc-state` and `sdlc:writing-specs` skills.
2. Determine the next slug (`NNN+1-<kebab-name>`; first: `001-...`). Create
   `specs/<slug>/`; if `specs/` is new, create it + empty `specs/metrics.jsonl`.
3. Gather requirements per the writing-specs skill: one focused question round
   if needed; offer exploration if the user is still forming the idea; use the
   bug variant for defect reports. Unattended: proceed, record Assumptions
   (for several features at once, dispatch `spec-writer` agents in parallel).
4. Write `spec.md` (FR-IDs, EARS acceptance criteria, Risk, within budget) and
   `status.json` (phase "requirements", proposed `track`, gates unapproved).
   For `track: quick`, the spec ends with a `## Mini-plan` (approach + tasks +
   affected files, ≤ 15 lines).
5. Present: the requirements, the proposed track (with one-line reasoning),
   and the approval checklist from the skill. Then ask directly: "Approve this
   spec[, on the quick track]?" Revise and re-ask as needed. (Standing
   approval directive active? Present the same, record without asking — see
   the sdlc-state skill.)
6. On explicit approval, record the gate(s) per the sdlc-state skill — quick
   track records spec AND plan gates together (phase → implement) and
   continues into implementation; full track records the spec gate (phase →
   plan) and continues into the plan phase. Unattended: write the
   `REVIEW.md` questionnaire (see sdlc-state), stop, and report.

Never touch code before the required gates are recorded.
