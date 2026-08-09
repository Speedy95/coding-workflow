# Changelog — sdlc plugin

## 1.2.0 (2026-08-09) — honest gate

The enforcement layer now does what the docs claimed. Every fix below closes a
bug that was confirmed by executing a payload against v1.1.0 (analysis #2, P0
items 1–8). The suite grew 36 → 118 cases, mostly to cover blind spots that let
these through.

**Over-allowing (the gate said no and meant yes):**
- A root-level entry in `## Affected files` (`taskler.py` — nearly every plan
  has one) unlocked **the entire repo root**: `posixpath.dirname` returns `""`
  for it and every root-level file matched that empty directory. Empty
  dirnames are no longer collected, and an explicit directory entry no longer
  unlocks its parent either.
- Deletion, move, copy and download were **entirely ungated** — `rm`, `mv`,
  `cp`, `truncate`, `dd`, `git checkout -- <path>`, `git restore`, `curl -o`,
  `Remove-Item`, `Move-Item`, `Copy-Item`, `Invoke-WebRequest -OutFile` all
  passed the Bash screen. Deleting a gated file is now a gated operation.
  `git apply` and `patch`, whose targets cannot be enumerated, are refused
  inside a gated repo — use Edit/Write, which is checked per file.
- **Any unrelated `specs/` directory disabled gating beneath it** (a vendored
  `api/specs/` of OpenAPI fixtures was enough). A directory now qualifies as
  an SDLC root only if `specs/` holds `metrics.jsonl` or `*/status.json`; the
  walk continues past non-qualifying ones. Same rule in the SessionStart hook.
- One approved feature with an unparseable plan **switched scoping off for
  every other feature**. Scope is now the union of the features that declare
  one; the gate fails open only when none does.
- `1> file` was eaten by the redirect regex's digit guard and `>| file` was
  never matched at all; both are screened now, as is `2> file`.
- On Windows, Git Bash's `/c/Users/...` form resolved to `<cwd>/c/Users/...`
  and fell open. Drive-letter paths are rewritten before resolving.

**Over-blocking (the gate refused legitimate work):**
- `phase: document` was not in the approved set, so **the retro was blocked
  from doing its own job** — the skill instructed exactly the edits the gate
  refused. `document` now unlocks like implement/verify, scoped to the same
  plan. Root-level `CHANGELOG*` joins `README*` as always-writable.
- `lstrip("./")` is a character-set strip: it mangled `.github/workflows/ci.yml`
  into `github/...`, so the listed file was blocked and a path that does not
  exist was allowed. Now a single `removeprefix("./")`; entries containing
  `..` are dropped rather than silently rewritten to some other in-repo path.
- A directory entry with a dot in its name (`src/v1.2/`) never matched as a
  directory. A trailing slash now always means "directory prefix"; the
  no-dot heuristic remains only as the fallback for entries written without one.
- Redirecting scratch output (`pytest > test-output.log`) was blocked as a
  code change. **[DECIDE]** Redirect-family targets ending in
  `.log`/`.txt`/`.out`/`.tmp` are allowed; destructive verbs get no such pass
  (`rm notes.txt` is still gated).

**State validation** (`validate_status.py`) checked shape but not invariants —
it accepted `phase: implement` with `plan_approved: false`, which is precisely
the state the edit gate reads. It now also rejects done without
`docs_complete`, a slug that does not match its own directory or the schema
pattern, and an `updatedAt` of `"yesterday"`. `schema/status.schema.json` was
authoritative in name only (nothing loaded it, and it had already drifted from
the hook's copy): the hook now reads the phase enum, track enum, gate names and
slug pattern **from the schema at start-up**, falling back to a mirrored copy
only if it cannot be read — and a test asserts the two agree. The PostToolUse
matcher covers `NotebookEdit` as well.

**Smaller fixes:** an unrecognised phase was reported as "shipped" by the
SessionStart hook (now flagged as unrecognised, with no resume hint); that hook
crashed with `UnicodeEncodeError` on an ascii-only console because its board
lines contain an em-dash; the dashboard now renders a pending `REVIEW.md` as a
readable artifact and `/sdlc:status` mentions one when present; the
requirements eval grader now requires an unattended run to leave a `REVIEW.md`
ending in the approve line. `/sdlc:dashboard`'s frontmatter was invalid YAML
(`argument-hint: [--serve] [output path]` — two flow sequences on one line), so
the command loaded with *no* metadata at all, description included; both
manifests now pass `claude plugin validate --strict`, which is worth adding to
CI.

**[DECIDE] defaults applied** (standing directive — implemented, not asked):
- Scope stays a **union across concurrently approved features**. Attributing an
  edit to one particular feature is unknowable at hook level, so two approved
  features widen the allowed set; documented in the README's Enforcement
  section rather than papered over.
- The document phase gets plan-scoped edit rights plus root `CHANGELOG*`.
- Scratch redirect allowlist is exactly `.log`, `.txt`, `.out`, `.tmp`.

**Residual gaps knowingly left** (unchanged or newly documented):
- Writes hidden inside quoted inline code (`python -c "..."`) are not caught.
- `cd dir && ...` compounds: relative targets are judged against the tool
  call's cwd, not the cd'd directory — can over- or under-block.
- `status.json` written via Bash bypasses PostToolUse validation entirely.
- `specs/archive/**` is deliberately excluded from validation (frozen history).
- A repo whose features are *all* archived qualifies as a root only via
  `specs/metrics.jsonl`.
- Shell aliases for the destructive cmdlets (`ri`, `del`, `mi`) are unscreened.

## 1.1.0 (2026-08-03) — OKF-aligned lessons + async review questionnaires

- **Lessons are now OKF-aligned** (Google's Open Knowledge Format, v0.1):
  frontmatter gains `type: lesson` (OKF's one required field), `tags`
  (grouping — tags before folders), `source` (originating feature) and
  `verified` (last confirmation date, the staleness signal for compaction);
  related lessons cross-link with standard markdown links, forming the
  knowledge graph. Existing `inclusion`/`match` fields are unchanged
  (OKF permits producer-defined fields).
- **Async review questionnaires**: unattended runs stopping at a human gate
  now write `specs/<slug>/REVIEW.md` — the approval checklist as answerable
  questions ending in `Approve this <spec|plan>? (yes/no):`. A later session
  finding an explicit written yes records the gate normally, addresses the
  other answers, and deletes the file. The SessionStart hook flags pending
  questionnaires (+1 test, 36 total).
- Evaluated but deferred: full OKF bundle structure (typed subdirs/log.md —
  ceremony at lessons scale), a grilling-style deep-interview exploration
  mode (future minor version).

## 1.0.2 (2026-08-03) — standing approval directives

From e2e run 003 (full track): repeated gate questions fatigue a present
user driving multiple features. The gate contract now supports an explicit
**standing approval directive** ("stop asking for approvals"): artifacts and
checklists are still presented, gates are recorded as
`by: "<user> (standing directive)"` without a blocking question, but genuine
forks (open questions, revised artifacts, destructive scope changes) still
ask. Momentum still never counts; unattended runs still never self-approve
(a standing directive does not carry into them).

## 1.0.1 (2026-08-03) — quick-track fixes from e2e run 002

Findings from the first live quick-track run (demo-app 002-list-all-done-last):

- **Quick-track scope gap closed**: the edit gate scoped only via plan.md, so
  quick-track features (mini-plan in spec.md, no plan.md) silently unlocked
  the whole repo. The gate now falls back to the spec mini-plan's
  `Affected files:` line (backticked paths, single line); writing-specs
  documents the format as load-bearing. +3 gate tests (35 total).
- tdd-loop: quick track has no plan.md checkboxes — status.json's task mirror
  is the task record; scope additions go to the mini-plan line.
- verification: defined `coverage` for quick track (% of FRs "met" with a
  named test) — it was only defined via the full-track coherence check.
- sdlc-state: documented the quick-track convention
  `artifacts.plan = "spec.md#mini-plan"`.

## 1.0.0 (2026-08-03) — production hardening

Enforcement:
- Gate hook derives the SDLC root from the **edited file's path** (fix: a
  session rooted outside the repo could bypass the gate).
- Gate now covers NotebookEdit and screens Bash/PowerShell commands for write
  patterns (redirects, tee, sed -i, Out-File/Set-Content) with quote-aware
  false-positive protection. Residual gap (documented): writes hidden inside
  quoted inline code (e.g. `python -c "..."`) are not caught.
- **Feature-scoped unlock**: with an approved plan, edits are limited to the
  plan's `## Affected files` (exact file / same dir / listed dir). Fails open
  when the section is missing or unparseable.
- New PostToolUse hook validates every `specs/*/status.json` write against
  `schema/status.schema.json` (now the authoritative schema).
- New SessionStart hook injects the board state into any session opened in an
  SDLC repo ("001-x: implement 3/5 — resume with /sdlc:implement 001-x").
- 32-case pytest suite for the hooks and dashboard generator; CI workflow.

Workflow:
- **Tracks**: `quick` folds planning into the spec gate (mini-plan in the
  spec, one approval) for small/low-risk work and bugfixes; `full` unchanged.
- **Checklist gates**: requirements/plan end with 5–8 targeted review items —
  the gate means answering them, not cold-reading documents. Hard length
  budgets on spec (≤2 pages) and plan (≤1.5).
- **Traceability**: FR-IDs on requirements, EARS acceptance criteria, plan
  tasks cite FR-IDs, verification reports a per-FR verdict table; plan phase
  runs a coherence check (two-way coverage + %, ambiguity, terminology,
  budgets) before approval.
- Optional `specs/constitution.md` (normative principles, loaded at plan +
  verify; conflicts are CRITICAL — adjust the change, never the principle).
- **Reconcile-on-document**: spec.md is folded into line with what actually
  shipped (+ Amendments note) — spec-anchored, not spec-first.
- verifyAttempts recorded (auto-loop hard-stops after 2 failed passes even
  across sessions); vacuous-red detection in the TDD loop; task progress
  mirrored to status.json; lessons get inclusion frontmatter
  (always/fileMatch/manual) + a compaction cadence; specs/archive/ convention.
- `[P]` parallel task markers + worktree isolation guidance; implementer runs
  acceptEdits; adversarial reviewer must return per-FR verdicts (re-dispatched
  once if not) and checks the constitution; risk-scaled second lens on high.
- New `/sdlc:init` scaffold command. Eval cases under `evals/` (experimental).

Dashboard:
- Template extracted to `dashboard/template.html` (same zero-dependency
  output); task progress ("implementing · 3/5 tasks") and quick-track badge;
  `ci-github-pages.yml` example shipped.

### Deferred by design (not omissions)
- **Statusline**: users often have their own; a snippet belongs in docs, not
  a forced override.
- **Blocking Stop hook** ("suite is red, don't stop"): fights the user;
  SessionStart injection covers resume safety instead.
- **UserPromptSubmit context injection**: per-prompt cost; SessionStart
  already carries the state.
- **Approve-from-board**: changes the gate's trust model; separate decision.
- **MCP server for workflow state / LSP spec linting / cloud routines**:
  future tiers; checklist + coherence check cover linting needs today.
- **Automatic git branching/committing**: policy belongs to the target repo;
  documented as an opt-in pattern in the README instead.

## 0.7.0 — conversational gates (no approve command), auto-continuing phases
## 0.6.x — single-list status-first board, recency ordering, contrast pass
## 0.5.0 — Onyx/Dignitas design schema
## 0.4.x — dossier board: artifact reader (md), lessons tab, --serve live mode
## 0.3.0 — signal-box gate rail design
## 0.2.0 — dashboard generator
## 0.1.0 — initial gated workflow (commands, skills, agents, edit gate)
