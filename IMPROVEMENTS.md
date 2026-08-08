# SDLC Workflow — Improvement Report

> **Status (2026-08-03, v1.0.0):** implemented — all of §1 (enforcement),
> §2.1–2.4, §3.1–3.4, §4.1–4.3, §5.1–5.2 (SessionStart, task mirror),
> §6.1 partial (orchestrator-side reviewer completeness) + 6.2–6.5,
> §7.1–7.2 + 7.5, §8.1 (cases, experimental) + 8.2–8.4 (docs/init/git-pattern).
> Deferred by design with rationale (see CHANGELOG): statusline override,
> blocking Stop hook, UserPromptSubmit injection, approve-from-board,
> MCP/LSP/routines, §7.4 notifications, §7.6 trend.

Sources: internal audit (built + first real e2e run, 2026-08-02), Claude Code
platform research, spec-driven-ecosystem research (Spec Kit, Kiro, OpenSpec,
BMAD, practitioner critiques). Priorities: **P0** defect · **P1** high value ·
**P2** valuable · **P3** future.

---

## 1. Correctness & enforcement (fix first — the gate is the product's promise)

- **1.1 [P0] Hook root derivation bug.** `gate_check.py` walks up from the
  session *cwd*, not the edited file's path — editing the repo from a session
  rooted elsewhere bypasses the gate entirely (proven during the e2e run).
  Fix: derive from `file_path`, fall back to cwd.
- **1.2 [P0] Gate surface too narrow.** Matcher is `Edit|Write` only —
  `NotebookEdit` and Bash writes (`echo >`, `sed -i`, `python - <<EOF`) slip
  through. Add NotebookEdit to the matcher; for Bash either a conservative
  write-pattern heuristic or an explicit documented limitation.
- **1.3 [P1] Repo-global unlock.** ANY feature in approved implement unlocks
  ALL code edits — a second, unapproved feature's edits ride along. Tighten:
  check the edited path against the approved feature's plan.md "Affected
  files" (directory-level match), warn or block on mismatch.
- **1.4 [P1] `python` on PATH assumption** in hooks.json breaks for teammates
  without it (hook error noise). Wrapper with `py -3` fallback, or document
  the prerequisite.
- **1.5 [P1] No schema validation for status.json.** Ship
  `schema/status.schema.json` + a stdlib validator script; optionally a
  PostToolUse hook validating any write to `specs/*/status.json`. Single
  source of truth replaces the prose schema in sdlc-state.
- **1.6 [P1] Verify-loop cap lives only in prose.** Record `verifyAttempts`
  in status.json so a resumed session honors the two-strikes rule.
- **1.7 [P1] The plugin's own code is untested.** gate_check.py and
  build_dashboard.py were only manually probed. Add a pytest suite in the
  marketplace repo (the 8 hook payload cases as fixtures) + CI running it and
  `claude plugin validate`.

## 2. Anti-ceremony guards (the ecosystem's loudest warning)

Field reports (marmelab, Fowler) show fixed heavyweight ceremony is the #1
reason spec-driven workflows get abandoned — 1,300 lines of artifacts for a
show-the-date feature; reviewers drowning in "expert-sounding prose."

- **2.1 [P1] `track: quick | full`** in status.json. Quick = spec-approval
  covers the plan (3-line plan inline), for small/low-risk work; full = the
  current five phases. Also a natural home for a **bugfix variant** where the
  failing repro test *is* the spec.
- **2.2 [P1] Hard length budgets in templates.** Spec ≤ 2 pages is already
  prose; make budgets explicit per section in writing-specs/planning, and
  have the coherence check (3.3) flag overruns.
- **2.3 [P1] Checklists as the gate's review surface** ("unit tests for
  English" — Spec Kit). `/sdlc:requirements` ends by generating 5–8 targeted
  quality-check items (`[Clarity, §FR-1] Is "prominent" quantified?`) so the
  human gate means answering a checklist, not cold-reading a document. This
  directly defends the conversational gates against rubber-stamping.
- **2.4 [P2] Pre-requirements explore mode** (OpenSpec `/explore`): when too
  confused to spec, an explicitly non-gated investigation that ends in a
  brief — entered as an option from `/sdlc:requirements`.

## 3. Spec quality & traceability

- **3.1 [P1] EARS notation for acceptance criteria** (Kiro/Mavin): `WHEN
  <trigger> THE SYSTEM SHALL <behavior>` (+ While/Where/If patterns). One
  clause ↔ one test case — makes TDD tasks and verification evidence
  mechanically traceable. Cost: a section in writing-specs.
- **3.2 [P1] Requirement IDs + traceability chain.** Every criterion gets an
  ID (FR-1…); plan tasks cite the IDs they satisfy; verify reports a per-ID
  coverage table. Turns the verification gate from judgement into a table —
  and gives the dashboard real per-feature content.
- **3.3 [P1] Coherence/coverage check before implementation** (Spec Kit
  `/analyze`): after planning, a read-only pass over spec+plan detecting
  requirements with zero tasks, tasks with no requirement, ambiguity
  (TODO/placeholders), terminology drift — graded findings + a coverage %
  that lands in metrics.jsonl. Cheapest high-value addition; can run at the
  end of `/sdlc:plan` rather than as a separate command (keep-it-light).
- **3.4 [P2] Constitution/steering layer** (Spec Kit constitution.md, Kiro
  steering): a small normative file of durable project principles
  (MUST/SHOULD), loaded at plan *and* verify so the adversarial reviewer
  judges against fixed standards, with the rule "constitution conflicts are
  CRITICAL — adjust spec/plan, don't dilute the principle." Distinct from
  lessons/ (empirical vs normative).

## 4. Post-ship integrity (be spec-anchored, not spec-first)

- **4.1 [P1] Reconcile step in the document phase** (OpenSpec archive-fold,
  Plumb): before writing lessons, diff `spec.md` against what actually
  shipped, record deltas as approved decisions, and fold them in — so specs
  stay true for maintenance instead of rotting the moment the feature lands.
  This is the main differentiation from Spec Kit/Kiro (whose specs are
  effectively discarded after implementation — Fowler's critique).
- **4.2 [P2] Lessons scaling**: Kiro-style conditional loading frontmatter
  (`inclusion: always | fileMatch <glob> | manual`) so planning loads only
  relevant lessons; plus a compaction pass every ~10 done-events (merge,
  prune, delete stale). Prevents the predictable context ceiling.
- **4.3 [P2] Archive completed features** — `specs/archive/` move on request
  or after N shipped, keeping the working folder and board lean while
  history stays in git + archive.

## 5. Session & resume UX (platform adoptions)

- **5.1 [P1] SessionStart hook injecting board state** — one line per
  in-flight feature ("001-x awaiting plan review; 002-y implementing 3/5")
  into every new session in an SDLC repo. Kills the cold-start problem;
  makes the per-phase resume commands almost never needed manually.
- **5.2 [P1] Task progress in status.json** (`tasks: {done, total}`,
  mirrored by implement) → dashboard rows, statusline, resume clarity.
- **5.3 [P1] Statusline integration** — "SDLC: implement 3/5" while working.
- **5.4 [P2] Goals/continuous-execution** for the implement→verify→document
  stretch: set completion condition "verification passed + docs complete"
  instead of relying purely on prompt-chaining prose.
- **5.5 [P2] Stop hook**: warn when a session ends mid-implement with a red
  suite or unchecked tasks.
- **5.6 [P2] UserPromptSubmit hook**: nudge when the user asks for
  implementation while gates are closed (points at the workflow instead of
  letting the request fight the edit-block hook).

## 6. Agents & scaling

- **6.1 [P1] SubagentStop validation** — verify implementer/reviewer output
  shape (tests named? evidence present?) before completion counts.
- **6.2 [P1] Parallel implementation, properly**: Spec Kit-style `[P]`
  markers on independent plan tasks + worktree isolation for parallel
  implementer agents (supported by the Agent tool). Update implement.md's
  parallel guidance accordingly.
- **6.3 [P2] Risk-scaled verification**: optional `risk: low|normal|high` in
  the spec; high → multi-lens verify (correctness + security + regression
  lenses in parallel), possibly delegating to /security-review for risky
  surfaces.
- **6.4 [P2] Per-agent tuning**: implementer `permissionMode: acceptEdits` +
  higher effort; doc-writer cheaper model; keep the adversarial reviewer
  fresh-context per pass (already true — now validated by VSDD research;
  make it an explicit rule) and never give it write tools.
- **6.5 [P2] spec-writer**: wire it explicitly into the unattended/
  multi-feature path or remove it (keep-it-light says unused surface goes).

## 7. Dashboard & visibility

- **7.1 [P1] Split the embedded template** into `dashboard/template.html`
  (loaded via `Path(__file__).parent`) — earned after this week's iteration
  count; zero-dependency property unchanged.
- **7.2 [P1] "3/5 tasks" on implementing rows** (needs 5.2).
- **7.3 [P2] Per-requirement coverage table in the dossier** (needs 3.2).
- **7.4 [P2] Phase-completion notifications** via Notification hook → n8n /
  Discord (existing infra) for long unattended stretches.
- **7.5 [P2] Ship a CI template** (GitHub Action: build snapshot on
  `specs/**` push → Pages) as a file in the plugin.
- **7.6 [P3] approve-from-board** behind `--serve` (separate decision — it
  shifts the gate's trust model). **[P3]** metrics trend once data accrues.

## 8. Distribution, docs, integration

- **8.1 [P1] Plugin eval harness** (`claude plugin eval`, evals/ cases):
  regression-test the *prompts* — "user asks for a feature → spec.md
  created, zero code edits", "implement without approved plan → refuses".
  Guards against prompt regressions the way 1.7 guards the scripts.
- **8.2 [P2] `/sdlc:init`** scaffold: specs/, lessons/INDEX.md, gitignore
  dashboard.html, CLAUDE.md pointer — tonight's demo repo was hand-scaffolded.
- **8.3 [P1] Doc gaps found tonight**: plugin content snapshots at session
  start (changes need a fresh session); `marketplace update` does not bump
  the installed version (uninstall+install); the conversational-gate
  contract (what counts as approval; unattended never self-approves); add a
  CHANGELOG.
- **8.4 [P2] Git integration policy** (opt-in): branch-per-feature,
  commit at phase boundaries, tag on done — audit trail in git, not just
  specs/. Pairs with worktrees (6.2).
- **8.5 [P3] MCP server exposing workflow state** as resources — the clean
  integration path for external tools and the verbose desktop app.

---

## Failure modes to keep designed-out (from field reports)

1. **Ceremony dwarfing the work** → tracks (2.1) + budgets (2.2).
2. **Double review burden / rubber-stamp gates** → checklists (2.3),
   dashboard shows only what needs a decision.
3. **Agents self-certifying verification** → keep: verbatim evidence,
   fresh-context read-only adversarial reviewer. (Strongly validated.)
4. **Prose as control** → anything that must hold is a hook/gate, never a
   paragraph. (Validated; 1.1–1.3 close the current gaps.)
5. **Brownfield blindness** → make codebase reconnaissance a mandatory,
   named plan task ("existing files this change touches").
6. **Spec-as-source ambition** → stay spec-anchored (4.1); don't chase
   humans-edit-only-specs.

## If only five things get done

1. **Hook fixes (1.1 + 1.2)** — enforcement is the promise; it currently leaks.
2. **`track: quick|full` + checklist gates (2.1 + 2.3)** — the two proven
   abandonment killers.
3. **SessionStart injection + task progress + statusline (5.1–5.3)** — the
   daily-driver UX.
4. **Requirement IDs + coverage check (3.2 + 3.3)** — verification becomes a
   table, not vibes.
5. **Reconcile-on-document (4.1)** — the feature that makes this
   spec-anchored where Spec Kit/Kiro are spec-first.

## Sources

Internal: e2e run of 001-due-dates (demo-app), plugin build log v0.1→v0.7.
Platform: code.claude.com/docs — hooks, sub-agents, skills, plugins-reference,
agent-teams, statusline, goals, changelog 2.1.186–2.1.219.
Ecosystem: github.com/github/spec-kit (+ tasks/analyze/checklist/constitution
templates), kiro.dev/docs (specs, steering, hooks), github.com/Fission-AI/
OpenSpec, BMAD-METHOD, buildermethods.com/agent-os, alistairmavin.com/ears;
critiques: marmelab.com "Waterfall Strikes Back", martinfowler.com SDD tools
series, isoform.ai "Limits of SDD", dbreunig.com "SDD Triangle", brooker.co.za
"Waterfall vs Spec".
