---
name: retro
description: The document phase - reconcile the spec with what shipped, update docs, distill lessons (with load conditions), append metrics, propose plugin improvements, close out.
---

# Retro (document phase)

This phase is why the workflow compounds: experience becomes versioned
artifacts future runs load. Order matters — reconcile first, then document,
then distill.

## 1. Reconcile spec with reality (stay spec-anchored)

Implementation reveals intent no upfront spec contained. Diff `spec.md`
against what actually shipped: behaviors added/changed/narrowed during
implement+verify. Fold the deltas INTO the spec (update the FRs/ACs) and add
a short `## Amendments` note (date + one line per delta + why). A spec that
lies about the shipped behavior is worse than no spec — this step is what
separates spec-anchored from spec-first-then-discarded.

## 2. Documentation

Update README/docs for the shipped feature: behavior, new flags, examples.
Documentation describes current behavior, never the implementation journey.

## 3. Lessons — per-project memory

One fact per file in `lessons/`, with OKF-aligned frontmatter (plain
markdown + YAML, portable to any OKF-aware consumer):

```markdown
---
type: lesson                     # OKF: the one required field
inclusion: always | fileMatch | manual
match: "tests/**"                # only for fileMatch
tags: [testing, cli]             # grouping — tags before folders
source: 003-remove-command       # feature that produced it
verified: 2026-08-03             # last date the fact was confirmed true
---
# <short title>
**Fact:** ...
**Why it matters:** ...
**Apply when:** ...
```

Cross-link related lessons with standard markdown links
(`see [other lesson](other-lesson.md)`) — the links are the knowledge graph
and make merge candidates visible at compaction time.

`always` lessons load at every plan; `fileMatch` only when the plan's
affected files match the glob; `manual` only when explicitly pulled. Add the
INDEX line. Quality bar: a lesson earns its file only if a future planner
without it would plausibly do worse. Update/delete before creating; when a
lesson is re-confirmed in practice, refresh `verified`.
**Compaction**: at every ~10th done-event, sweep lessons/ — merge overlaps
(follow the cross-links), delete stale (old `verified` dates are the smell),
demote `always` → `fileMatch` where scope allows. A bloated lessons folder
degrades every future plan. Keep lessons/ flat; group by `tags` + INDEX
sections, and only reach for subfolders past ~30 lessons.

## 4. Metrics

Append `{"at", "slug", "event": "done", "lessonsWritten": N}` to
specs/metrics.jsonl.

## 5. Plugin improvements — shared team memory

Review this run's friction + metrics.jsonl trends with concrete thresholds:
first-try-green < 50% over last 5 verifies → strengthen tdd-loop/planning;
review findings rising → strengthen the spec quality bar; coverage < 90%
repeatedly → strengthen the coherence check. Present proposed diffs to the
plugin's files — never edit the plugin yourself; improvements land in the
shared repo through review.

## 6. Close out

Set `docs_complete`, `phase: "done"`. Offer archiving (move the feature dir
to `specs/archive/` — invisible to board and gate) when the working set grows
past ~10 shipped features. Summarize: shipped, amendments, lessons, proposals.
