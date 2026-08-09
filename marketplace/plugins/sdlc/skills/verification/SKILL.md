---
name: verification
description: The verify phase - suite evidence verbatim, adversarial review with per-FR verdicts, risk-scaled lenses, attempt tracking, and the gate set only on proof.
---

# Verification

Verification produces EVIDENCE, not assertions. Anyone must be able to audit
verification.md later and see exactly what was proven, per requirement.

## Process

1. Increment `verifyAttempts` in status.json at the start of each pass.
2. Run the full test suite; capture command + output verbatim. Any red: set
   `phase: "implement"`, summarize failures, continue back into implement —
   unless `verifyAttempts` ≥ 2, then STOP and hand findings to the user.
3. Dispatch the `adversarial-reviewer` agent (always a FRESH context per pass
   — accumulated goodwill hides gaps; never give it write tools) with: spec
   path, changed files, and `specs/constitution.md` if present. Require
   **a verdict per FR-ID** (met / violated / untested) with evidence.
   If the report comes back without per-FR verdicts, re-dispatch once with
   the gap named — an incomplete review is not a review.
4. **Risk scaling** (spec's Risk field): `high` → add a second reviewer pass
   with a security/abuse lens (or run /security-review when available) plus a
   regression lens on the named must-not-break files. `low` → single pass.
5. Constitution conflicts found by review are automatically CRITICAL: adjust
   the implementation or escalate the spec — never dilute the principle.
6. Triage: spec violations → back to implement (same loop rules as red
   tests). Out-of-scope observations → plan.md "Surfaced issues".
7. Only with green evidence and zero unresolved violations: write
   verification.md, set `verification_passed` (`by: "sdlc-verify"`),
   `phase: "document"`, and append the metrics line:
   `{"at", "slug", "event": "verify", "testsGreenFirstTry", "reviewFindings",
   "planRevisions", "coverage"}` (coverage % from the plan's coherence check;
   quick track has no coherence check — there, coverage = % of FRs whose
   review verdict is "met" backed by a named test; testsGreenFirstTry is
   false if any pass this phase saw red).

## verification.md structure

```markdown
# Verification: <feature>

## Test evidence
Command + verbatim output.

## Requirement coverage
| FR | verdict | evidence |
|----|---------|----------|
| FR-1 | met | test_x + file:line |
Every FR and AC appears; "untested" is a finding, not a footnote.

## Review findings
Each finding: fixed / rejected (why) / deferred to Surfaced issues.
```
