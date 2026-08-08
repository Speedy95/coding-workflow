# Orchestrator: sdlc plugin improvement program (v1.2.0 → v2.0.0)

You are a worker agent executing ONE unit of this program. Read this file
fully, then your assigned small spec. Source analysis: `../IMPROVEMENTS-2.md`
(evidence + file:line for every claim; findings marked ✔ were confirmed by
executing payloads).

## Repos and layout

- `../marketplace/` — git repo, the plugin (`plugins/sdlc/`: commands/,
  skills/, agents/, hooks/, dashboard/, schema/, evals/; tests in `tests/`).
- `../demo-app/` — git repo, taskler; 3 features shipped through the
  workflow; used for smoke runs.
- This `specs/` folder is program documentation, NOT sdlc-plugin state — do
  not create status.json files here.

## Build order and sequencing

| Unit | Spec | Depends on | Parallel-safe? |
|------|------|-----------|----------------|
| A: v1.2.0 honest gate | 01-honest-gate.md | — | no (touches hooks + tests broadly) |
| B: v1.3.0 state machine + CLI | 02-state-machine-cli.md | A (invariant checks, validator changes) | no (touches skills A leaves alone, but shares tests/, schema/) |
| C: v1.4.0 verification + lessons | 03-verification-lessons.md | B (uses the CLI; dogfoods the workflow) | no |
| D: v2.0.0 platform design doc | 04-platform-design.md | A–C outcomes inform it | yes vs C, after A+B |

Strictly serialize A → B → C. D may run alongside C (it produces a document,
no code). One unit per session — plugin content snapshots at session start,
so a unit's live verification only sees the previous unit's install.

## Global conventions

- Python: stdlib only in hooks/ and bin/ (hard rule — hooks run everywhere).
- TDD: every behavior change lands with a failing test first, in
  `marketplace/tests/`. The repro payloads in IMPROVEMENTS-2.md ARE the red
  tests for unit A — port them verbatim.
- Fail-open philosophy stands: gate errors must never break unrelated work.
  New screens block only on positive evidence.
- Additive over destructive: extend `conftest.py` fixtures; never rewrite
  passing tests to fit new code.
- Docs: every unit updates `marketplace/CHANGELOG.md` (new version section),
  bumps `plugins/sdlc/.claude-plugin/plugin.json` version, and fixes any
  README count/claim it invalidates (audit found these drift — check them).
- Commit style: one commit per unit in each touched repo, message =
  `vX.Y.0: <unit name>` + bullet summary. Do not push.
- Timestamps: never invent — obtain via `date -u +%Y-%m-%dT%H:%M:%SZ`
  (unit B ships the CLI that removes this class of work).

## Resolving [VERIFY] and [DECIDE] markers

- `[VERIFY]`: an external claim (docs, spec versions) — confirm against the
  primary source before relying on it; if it fails verification, note it in
  your report and implement the fallback stated in the spec.
- `[DECIDE]`: a default has been chosen by the maintainer (Alex operates
  under a standing approval directive — do NOT block asking; implement the
  stated default and record it prominently in CHANGELOG).

## Per-unit definition of done

1. All new tests green AND full suite green: `python -m pytest tests -q`
   from `marketplace/` (baseline: 36 passing).
2. `claude plugin validate ./marketplace/plugins/sdlc --strict` passes
   [VERIFY: exact CLI syntax — check `claude plugin validate --help`].
3. CHANGELOG entry + version bump + README claims corrected.
4. Committed in each touched repo.
5. Plugin reinstalled: `claude plugin marketplace update sdlc-marketplace &&
   claude plugin uninstall sdlc && claude plugin install sdlc@sdlc-marketplace`.
6. Report written (format below). Live e2e smoke happens at the START of the
   next unit's session (fresh snapshot) — each unit begins by running the
   previous unit's smoke checklist, and unit A begins by confirming baseline.

## Report format (end of unit)

Write `specs/reports/<unit>-report.md`:
- Shipped: item-by-item vs your spec (done / deviated+why / dropped+why)
- Test delta: counts before/after, new test names
- [VERIFY] outcomes and [DECIDE] defaults applied
- Residual gaps knowingly left (with CHANGELOG reference)
- Smoke checklist for the next session (exact commands + expected output)
