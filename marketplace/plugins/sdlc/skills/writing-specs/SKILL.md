---
name: writing-specs
description: How to gather requirements and write a spec.md - structure, EARS acceptance criteria with FR-IDs, track sizing, review checklist, and unattended handling.
---

# Writing specs

A spec answers "what and why", never "how". Budgets are hard: **spec ≤ 2 pages**,
Problem ≤ 4 sentences, ≤ 10 requirements, ≤ 8 acceptance criteria. A spec nobody
reads gates nothing — length is a defect, not thoroughness.

## Process

1. Start from the user's brief. If anything material is unclear, ask ONE round
   of focused questions (≤ 3). If the user doesn't yet know what they want,
   offer a short non-gated **exploration** first (investigate, prototype
   nothing, come back with a brief) — don't force a spec out of confusion.
2. Unattended: pick the most reasonable interpretation, record every guess
   under **Assumptions**.
3. Read the repo enough to spot conflicts with existing behavior.
4. **Size the track.** Propose `track: quick` for small, low-risk changes
   (single concern, few files, no schema/behavior breakage) — quick folds the
   plan into the spec approval (one gate, mini-plan). Default is `full`. The
   user confirms the track at spec approval.
5. **Bug variant**: for defect reports, the spec is the repro — Expected vs
   Actual, steps, and one acceptance criterion "the repro test passes, suite
   stays green". Default `track: quick`.

## spec.md structure

```markdown
# <Feature name>

## Problem
Why this exists, from the user's perspective.

## Requirements
Each requirement gets a stable ID and must be testable:
- FR-1: ...
- FR-2: ...

## Acceptance criteria (EARS)
One criterion per FR where sensible, in EARS form — each maps to one test:
- AC-1 (FR-1): WHEN <trigger> THE SYSTEM SHALL <observable behavior>
- AC-2 (FR-2): IF <unwanted trigger>, THEN THE SYSTEM SHALL <response>
(Also available: WHILE <state> ... / WHERE <feature present> ...)

## Out of scope
Explicit non-goals — this section prevents scope creep. Never empty.

## Risk
low | normal | high — high means security/data/irreversibility surface;
verification scales with this.

## Assumptions
Only when unattended: every interpretation made without the user.

## Open questions
Must be empty (or explicitly accepted) before approval.

## Mini-plan (track: quick)          <- quick track only, ≤ 15 lines
Approach: one or two sentences.
Tasks:
1. ...
Affected files: `path/one.py`, `tests/test_one.py`
```

The `Affected files:` line is load-bearing: the edit gate parses exactly that
line (backticked paths, one line) to scope quick-track edits — keep the
format, and update the line first when a new file turns out to be needed.

## The approval checklist

End the requirements phase by generating 5–8 targeted review items — "unit
tests for English". Each tests requirement QUALITY, never implementation, and
cites its target: `[Clarity, FR-3] Is "fast" quantified?` · `[Coverage, AC]
Does any criterion cover the empty-input case?` · `[Consistency] Do FR-2 and
FR-5 use the same term for the same thing?` Present the checklist WITH the
approval question — the human gate means answering these items, not
cold-reading the document.

## Quality bar

- Every FR testable; every AC observable and traceable to one FR.
- No solution language — that's the plan's job.
- Within budget; over budget → cut, don't compress the font.
