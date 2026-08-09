---
description: Document the shipped feature, distill lessons, and close out
argument-hint: [slug]
---

Run the SDLC document phase for: $ARGUMENTS

1. Load the `sdlc:sdlc-state` and `sdlc:retro` skills. Resolve the slug
   (argument, or the single feature in phase `document`).
2. Check the gate: `verification_passed.approved` must be true. If not, stop
   and point the user at `/sdlc:verify <slug>`.
3. Follow the retro skill's six steps in order: reconcile spec.md with what
   actually shipped (fold deltas in + Amendments note), update user docs (the
   `doc-writer` agent may do the writing), distill lessons with inclusion
   frontmatter (compaction sweep every ~10th feature), append the done-event
   metrics line, review this run + metrics trends against the skill's
   thresholds and draft proposed plugin diffs, then set `docs_complete` and
   `phase: "done"` (offer archiving when the working set is large).
4. Report: what shipped, docs updated, lessons written (or why none), and the
   proposed plugin improvements as concrete diffs for the user to apply to the
   marketplace repo.

Never edit the plugin itself — improvements land in the shared repo through
review.
