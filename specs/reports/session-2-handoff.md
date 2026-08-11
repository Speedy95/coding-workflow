# Session 2 handoff — post-review v1.2.1, ready for Unit B

Audience: the next session's agent (and Alex). Read this INSTEAD of the
smoke checklist at the bottom of `unit-a-report.md` — that one predates
v1.2.1 and its numbers are stale. Then read `00-orchestrator.md` and your
spec `02-state-machine-cli.md`.

## Where things stand

- Plugin `sdlc` is at **v1.2.1**, installed user-scope from the local
  marketplace. Suite: **135 passed** (`python -m pytest marketplace/tests -q`
  from the repo root). `claude plugin validate --strict
  ./marketplace/plugins/sdlc` passes.
- One repo: `coding-workflow` (monorepo since Unit A; pre-monorepo inner
  histories discarded 2026-08-11 at Alex's request — the v1.1.0 fold-in
  commits are now the earliest state). Remote `main` was **force-pushed** this
  session — the three opaque commits were rewritten into 12 reviewable
  increments (`67c74ca..2402653`). Local branch `backup-linear` holds the
  pre-rewrite state; delete it once Alex is satisfied.

## What session 2 did (between Unit A and Unit B)

1. Ran a high-effort multi-agent code review of Unit A's gate. It CONFIRMED
   **10 bypasses** in the freshly hardened hooks — all fixed as **v1.2.1**
   with red-first tests (+17, 118 → 135). Highlights:
   - hooks ran bare `python` → the whole enforcement layer was silently
     dead on stock macOS/Ubuntu (now: `python` → `python3` fallback);
   - scratch-extension exemption ran BEFORE the approval check;
   - `git -C . restore f` / `git checkout f` (no `--`) destroyed gated
     files unscreened; quoted paths with spaces escaped screening;
     `-LiteralPath`/`-FilePath` screened the wrong token; `sed -i`/`tee`
     only screened their first file argument;
   - **policy change**: document phase now unlocks ONLY `.md/.rst/.txt`
     within scope — code is frozen once verified (shipped == verified).
   Full list: CHANGELOG 1.2.1.
2. Rewrote history into small increments and force-pushed (above).
3. Hardened `hooks.json` further: each hook command is guarded by
   `[ -f <script> ] || exit 0` (see gotcha 1 below).

## Gotchas learned live — do not relearn these

1. **Local-path plugin installs reference the SOURCE tree.**
   `CLAUDE_PLUGIN_ROOT` = `<repo>/marketplace/plugins/sdlc`, not a copy.
   If the hook scripts vanish from disk (e.g. `git reset --hard` to an old
   commit), Python exits 2 → Claude Code reads that as a gate BLOCK →
   every Edit/Write/Bash/PowerShell call in the session is locked, with no
   self-rescue. The `[ -f ]` guard in hooks.json fixes future sessions,
   but THIS session's hook command is snapshotted at session start — so:
   **never remove or hard-reset `marketplace/` mid-session.** Manipulate
   the index (`git checkout <ref> -- <paths>`, `git reset` without
   `--hard`) instead. Recovery if it ever happens: Alex runs the restore
   via `! <command>` (user shell bypasses hooks).
2. **Plugin content snapshots at session start** — v1.2.1 hooks are live
   in new sessions only. After any plugin change:
   `claude plugin marketplace update sdlc-marketplace && claude plugin
   uninstall sdlc && claude plugin install sdlc@sdlc-marketplace`, then
   verify in a NEW session.
3. The v1.1.0 marketplace bundle has `__pycache__` committed — filter it
   if you ever extract from the bundles.
4. `coding-workflow/specs/` is program documentation, NOT a workflow
   board. If the gate ever fires on edits under `marketplace/`, someone
   added `status.json`/`metrics.jsonl` under `specs/` — remove it.

## Smoke checklist for Unit B (run first, new session)

```bash
cd C:/Users/Alex/PycharmProjects/coding-workflow
python -m pytest marketplace/tests -q        # expect: 135 passed
claude plugin validate --strict ./marketplace/plugins/sdlc  # expect: ✔
claude plugin list                           # expect sdlc … 1.2.1
```

Live gate probes (installed hooks, not the repo copy):

1. `demo-app/`: ask to edit `taskler.py` → refusal mentioning "approved
   implement/verify phase" and the docs-only document-phase note (new
   v1.2.1 message text).
2. `demo-app/`: `rm taskler.py` → blocked. Also try the v1.2.1 forms:
   `git -C . restore taskler.py` and `git checkout taskler.py` → blocked.
3. `coding-workflow/`: edit any file under `marketplace/` → NO gate
   (deliberately not a board).
4. New session in `demo-app/` → SessionStart prints three `shipped` lines.

## Open items no spec owns yet (Alex to assign — proposed: fold into B as B6)

- **Deleting the board directory itself is ungated**: `check_target` only
  inspects the target's PARENT for a board, so `rm -rf demo-app` from
  outside passes the gate while `rm demo-app/taskler.py` blocks.
  Discovered live during the session-2 history rewrite; not yet in any
  CHANGELOG/spec.
- Unassigned residual screening gaps from CHANGELOG 1.2.1: PowerShell
  alias commands (`ri`, `del`, `erase`, `mi`), POSIX `unlink`/`shred`;
  `status.json` written via Bash bypasses PostToolUse validation (cheap
  fix: re-validate all boards at SessionStart, warn on invalid).
- Copy-on-install vs live source-reference for local plugin installs
  (the session-2 lockout root cause) → belongs in Unit D1's architecture
  comparison, one bullet.

## Unit B notes (read with 02-state-machine-cli.md)

- Baseline is 135 tests, not the 36 the orchestrator mentions or the 118
  in unit-a-report. Target after B ≈ 155+.
- The CLI launcher must copy the hooks.json pattern: `[ -f ]` guard +
  `python`/`python3` fallback (or document `python3`-first invocation) —
  bare `python` does not exist on stock macOS/Ubuntu.
- `set-phase <slug> document` semantics unchanged by v1.2.1, but remember
  the gate now enforces docs-only in that phase — B4's skill rewrites must
  not instruct code edits during document.
- v1.2.1 made the board tolerant of a `tasks` object missing `done`; the
  CLI should still always write both keys.
- Commit style for B: several small, reviewable commits (Alex's explicit
  preference — supersedes the orchestrator's "one commit per unit"). Push
  normally (no force) when done.
