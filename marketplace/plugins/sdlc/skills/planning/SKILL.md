---
name: planning
description: How to turn an approved spec into plan.md - FR-traced task breakdown with per-task tests, mandatory codebase recon, parallel markers, and a coherence check before approval.
---

# Planning

A plan turns an approved spec into ordered, testable tasks. Budget: **plan ≤
1.5 pages**; if it wants to be longer, the feature wants splitting.

## Process

1. Read the approved `spec.md` in full; read `specs/constitution.md` if it
   exists (its principles are non-negotiable — a conflict means adjusting the
   plan or escalating the spec, never diluting the principle).
2. Read `lessons/INDEX.md` and every lesson whose hook or `apply-when` matches
   this feature's area. Cite applied lessons in the plan.
3. **Codebase recon is a mandatory step, not a vibe**: name the existing
   files/functions this change touches or must not break — brownfield
   blindness (missing an existing function that needed updating) is the #1
   reported failure of spec-driven agents.

## plan.md structure

```markdown
# Plan: <feature>

## Approach
Strategy in a short paragraph + rejected alternatives (one line each) +
lessons applied.

## Affected files
- `path/file.py` — what changes and why
(The edit gate enforces this list: files outside it are blocked until added
here. List every file including tests.)

## Tasks
Each task cites the FR-IDs it satisfies and names its proving test.
Mark [P] only when tasks touch disjoint files and share no dependency:
- [ ] 1. **<task>** (FR-1, FR-2) — change: ...; test: ...
- [ ] 2. [P] **<task>** (FR-3) — change: ...; test: ...

## Test plan
Commands the verify phase runs; new test files.

## Risks
What could break, how we'd notice, how we'd roll back.
```

## Coherence check (before asking for approval)

Run a self-check and report the result with the approval question:
- **Coverage both ways**: every FR/AC has ≥ 1 task; every task cites ≥ 1 FR.
  Report the matrix and a coverage % (goes to metrics at verify time).
- **Ambiguity**: no TODO / TBD / `<placeholder>` anywhere in spec or plan.
- **Terminology**: same concept, same word, in both artifacts.
- **Budgets**: spec and plan within their length budgets.
- **Constitution**: no task conflicts with a constitution principle.
Findings are fixed before approval, not disclosed and shipped.

## The plan checklist

Present 4–6 review items with the approval ask, e.g. `[Coverage] FR-4 has no
task — intentional?` · `[Real files] Does src/auth.py actually exist?` ·
`[Tests] Does every task name a runnable test?`

## Quality bar

- A task without a test is a smell — split or rethink.
- Suite green after every task, not just at the end.
- Infeasible or ambiguous spec → stop and say so; the spec gate exists to be
  re-run.
