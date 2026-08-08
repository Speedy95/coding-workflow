# Unit C — v1.4.0 "verification deepening + lessons v2"

Goal: research-backed verification upgrades (IMPROVEMENTS-2.md P3) and the
OKF v0.2 lesson model. Depends on Unit B (CLI, REVIEW.md v2 hooks into
`review write`).

**Dogfood requirement**: run items C1–C4 as REAL features through the sdlc
workflow itself — `python bin/sdlc_state.py init` a `specs/` root in
`marketplace/` (the plugin repo becomes its own first production user).
Each item = one quick-track feature (C4 full-track). This doubles as the
e2e regression run for Units A+B. The workflow's edit gate will then govern
the plugin repo: plan Affected files accordingly.

## C1. Ablation check (verification skill)

New step in `skills/verification/SKILL.md` between suite run and reviewer
dispatch, for every FR whose implementation lives in an identifiable
function/module:
1. Stub the claimed implementation (rename function + minimal raise, or
   comment-out module body — via a temporary git stash-able edit).
2. Run the FR's named tests: they MUST go red. Record `FR-n: ablation red`
   in verification.md's coverage table (new column).
3. Restore (git checkout -- the file), re-run suite green.
A test that stays green under ablation is a CRITICAL finding (the test
does not depend on the code it claims to pin) — same severity as a spec
violation, back to implement.
Rationale + citation (arxiv 2606.28430) as one line in the skill.
[DECIDE] Ablation is required for `full` track, optional for `quick`.

## C2. UNRESOLVED verdict + reviewer de-biasing

- `agents/adversarial-reviewer.md`: verdict set becomes
  met | violated | UNRESOLVED (replaces "untested"); every `violated`
  MUST cite a runnable repro (command + expected-vs-actual), every
  UNRESOLVED states what evidence would resolve it.
- `skills/verification/SKILL.md`: any UNRESOLVED blocks
  verification_passed; attended → surface to user; unattended →
  `review write` a question per UNRESOLVED and stop (2-strike rule
  unchanged, UNRESOLVED does not increment verifyFails).
- De-biasing (dispatch template in verify command/skill): reviewer prompt
  must NOT include who wrote the code or prior verdicts; FR list is
  passed in shuffled order (`--shuffle-frs` note); reviewer told verbosity
  and confidence language carry no weight.

## C3. Lessons → OKF v0.2

[VERIFY] v0.2 field shapes against
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
(fallback: keep our v1.1.0 fields, add only `superseded_by` + `status`).
- Frontmatter model (retro skill template + migrate demo-app's 2 lessons):
  `type: lesson` (closed enum: lesson — reject others in lint),
  `status: draft|stable|deprecated`, `verified: [{by, at}]` (list of
  events; replaces scalar `verified:`), `stale_after: <date>`,
  `superseded_by: <file>` (invalidate, never delete or rewrite a claim),
  keep `inclusion`/`match`/`tags`/`source`.
- Trust tiers derived, not stored: unverified (empty verified[]) /
  machine-confirmed (only agent entries) / human-reviewed (any
  `human:<name>` entry). Retro writes `by: "agent:sdlc-retro"`;
  [DECIDE] Alex's explicit confirmation in conversation adds
  `human:alex` — standing directives do NOT auto-promote lessons.
- Planning skill: prefer human-reviewed > machine-confirmed > unverified
  when lessons conflict; skip `deprecated` and superseded; treat past
  `stale_after` as needs-reverification (load, but flag).
- CLI: `sdlc_state.py lesson verify <file> --by <actor>` appends a
  verified event; `lesson supersede <old> <new>`; INDEX.md regenerated
  mechanically by `lesson index` (fixes hand-kept INDEX).
- Retro compaction step: use tiers + stale_after + usage instead of gut
  feel; superseded lessons drop from INDEX but keep their file.

## C4. REVIEW.md v2 (full-track feature)

Extends Unit B's `review` subcommands:
- Per-question risk tier: `[low]` (proceed by default) / `[high]` (blocks).
  File format: `1. [high] <question>` + `Answer:` lines.
- TTL header line: `expires: <ISO date> → default: reject`.
  [DECIDE] defaults: spec/plan approval questions are ALWAYS high + reject
  on expiry (an approval can never default to yes); non-gate questions
  (e.g. UNRESOLVED verdicts, scope re-affirmations) may be low and default
  to proceed-with-note after 7 days.
- Provenance: on record, append to status.json gate entry:
  `via: "review-md"`, plus `answeredBy` if determinable — documented as
  audit hint (B5), not auth.
- `review check` honors tiers/TTL: expired file → apply defaults, rename
  `REVIEW-expired-<date>.md`, report what was defaulted.
- Question authoring guidance (sdlc-state skill): write for the least
  technical reviewer — what happens, what won't happen on reject, the one
  key risk.

## C5. Small additions (docs/prompts only)

- `writing-specs/SKILL.md`: formalize the exploration path as an optional
  **spike phase** — non-gated, time-boxed, output is a brief (premise,
  findings, recommendation) saved as `specs/<slug>/spike.md` BEFORE the
  spec is written; the spec cites it. Trigger words: user unsure, novel
  domain, "not sure this is possible".
- `writing-specs/SKILL.md`: optional per-FR `invariant:` line (a property
  statement); planning turns each into a property-test task
  (Hypothesis for Python targets); verification checks the property test
  exists for FRs that declare one.
- `dashboard/ci-github-pages.yml` sibling example
  `ci-mutation-nightly.yml`: nightly mutmut/Stryker run appending a
  `mutationScore` metrics event — example only, not wired.

## Verification plan

- Each dogfooded feature leaves its own spec/verification.md in
  `marketplace/specs/` — those artifacts ARE the acceptance evidence.
- Ablation check demonstrated live on one feature (paste transcript).
- `tests/`: lesson lint + lesson subcommands + review v2 tiers/TTL
  (≈ +12 tests).
- Demo-app lessons migrated; INDEX regenerated; planning skill loads them
  without error in a smoke session.
