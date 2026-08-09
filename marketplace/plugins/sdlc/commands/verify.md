---
description: Verify implementation against the spec - test evidence plus adversarial review
argument-hint: [slug]
---

Run the SDLC verify phase for: $ARGUMENTS

1. Load the `sdlc:sdlc-state` and `sdlc:verification` skills. Resolve the slug
   (argument, or the single feature in phase `verify`).
2. Follow the verification skill exactly: increment `verifyAttempts`, run the
   full suite, capture output verbatim; on any red, set `phase: "implement"`
   and continue back into implement — unless this is the second failed
   attempt, then stop and hand the findings to the user.
3. On green, dispatch the `adversarial-reviewer` (fresh context, spec +
   changed files + constitution if present) and require per-FR verdicts —
   re-dispatch once if the report lacks them. Scale by the spec's Risk field
   (high → add security/regression lens). Triage findings per the skill.
4. Only with green evidence and no unresolved violations: write
   `specs/<slug>/verification.md`, set the `verification_passed` gate and
   `phase: "document"`, and append the verify metrics line to
   `specs/metrics.jsonl`.
5. Report: evidence summary, per-requirement compliance, findings and their
   resolutions — then continue straight into the document phase (follow
   `/sdlc:document`'s steps; no new command needed).

Never set `verification_passed` without captured green test output. Evidence
before assertions, always.
