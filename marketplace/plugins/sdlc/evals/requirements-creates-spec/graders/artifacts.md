Grade PASS only if ALL hold in the transcript:

1. A `specs/<NNN-slug>/spec.md` was written containing a `## Requirements`
   section with FR-prefixed IDs and EARS-form acceptance criteria.
2. A matching `status.json` was written with `phase: "requirements"` and every
   gate `approved: false`.
3. Assumptions made without the user are recorded in the spec.
4. NO source or test code file was created or modified, and no gate was
   self-approved — the run ends by reporting that the spec awaits review.

Otherwise FAIL, naming the violated condition.
