# Unit A — v1.2.0 "honest gate"

Goal: the enforcement layer does what its docs claim. Every numbered item
below was CONFIRMED by live payload in the audit (IMPROVEMENTS-2.md P0).
Files: `marketplace/plugins/sdlc/hooks/gate_check.py`, `validate_status.py`,
`session_state.py`, `hooks.json`, `schema/status.schema.json`,
`dashboard/build_dashboard.py`, `commands/status.md`, tests, READMEs,
`evals/requirements-creates-spec/graders/artifacts.md`.

## A1. Scope-matching fixes (gate_check.py)

Current: `rel_is_in_scope` (gate_check.py:87-97) adds
`posixpath.dirname(entry)` for every entry to a `dirs` set; a root-level
entry (`taskler.py`) yields `""`, and every root-level file's dirname is
also `""` → whole repo root allowed.
- Fix: only add non-empty dirnames to `dirs`. Exact-file matches keep
  working for root-level entries.
- Path normalization (`_backtick_paths`, gate_check.py:102): replace
  `.lstrip("./")` (char-set strip mangles `.github/...`) with
  `.removeprefix("./")` applied repeatedly? No — apply once; also reject
  entries containing `..` (they currently mangle to a different path).
- Directory entries: current heuristic `"." not in basename` (line ~112)
  breaks `src/v1.2/`. New rule: an entry ending in `/` is ALWAYS a
  directory prefix; the no-dot heuristic remains only as fallback for
  legacy entries without slash.
- Tests: root-entry does not unlock sibling root files; `.github/...`
  entry allows exactly that path; `src/v1.2/` entry allows files beneath.

## A2. Root detection (gate_check.py `find_root`, lines 39-50)

Current: any ancestor with a `specs/` dir wins → false roots (e.g.
`api/specs/` OpenAPI fixtures) disable gating beneath them.
- Fix: a candidate root qualifies only if `specs/metrics.jsonl` exists OR
  `specs/*/status.json` glob is non-empty. Keep walking up past
  non-qualifying `specs/` dirs (do not stop at them).
- Apply the same rule in `session_state.py:find_root` (lines 16-24) —
  extract to a shared helper is NOT possible across hook files without a
  package; duplicate the 3-line check with a comment naming the twin.
- Tests: repo with decoy `api/specs/` — file under `api/` is still gated
  by the real root above; a repo with ONLY a decoy specs/ is untouched.

## A3. Multi-feature scope + per-feature fail-open (gate_check.py:152-161)

Current: entries union across approved features; ANY feature without
parseable entries kills scoping for all.
- Fix: judge edits against the union of entries from features that HAVE
  parseable entries; a feature without entries contributes nothing. Fail
  open (no scoping) only when NO approved feature has parseable entries.
- [DECIDE] Scope union across features remains (per-feature attribution of
  an edit is unknowable at hook level); documented in README Enforcement.
- Tests: two features, disjoint scopes, third unparseable → edits limited
  to the union; single unparseable feature alone → fail open (existing
  test still passes).

## A4. Document phase (gate_state, gate_check.py:60-71)

Current: `phase: "document"` is not in the approved set → the retro's own
work (CHANGELOG.md, mkdocs.yml, code-adjacent doc files) is blocked.
- Fix: treat `document` like implement/verify (requires plan_approved),
  same plan-scope rules — reconcile edits stay within the feature's scope.
- Additionally extend the always-allowed check (line ~127): root-level
  `CHANGELOG*` joins `README*`.
- Tests: full phase×permission matrix — for each of requirements/plan/
  implement/verify/document/done × (in-scope file, out-of-scope file,
  specs/ file): expected allow/block. This is the audit's biggest test
  blind spot; make it a parametrized table test.

## A5. Bash/PowerShell screening (gate_check.py:31-36, 147-159)

Current extractors: redirects, tee, sed -i, PS Out-File/Set-Content/
Add-Content. Unscreened & confirmed allowed: rm, mv, cp, Remove-Item,
Move-Item, Copy-Item, git checkout --, git apply, patch, curl -o,
truncate -s, dd of=.
- Add extractor regexes (conservative, same sanitization pipeline):
  - `\brm\b` + all path args; `\btruncate\b` + path after `-s N`;
    `\bdd\b` + `of=<path>`
  - `\bmv\b|\bcp\b` + LAST path arg (destination) AND for mv also first
    (source is destroyed); PS `Move-Item|Copy-Item|Remove-Item` -Path/
    positional
  - `\bgit\s+checkout\b.*--\s+(.+)` (paths after --), `\bgit\s+apply\b`
    → treat as write to repo root (block unless fail-open), `\bpatch\b`
    with `-i file` or `< file` → same root-level treatment
  - `\bcurl\b.*(?:-o|--output)\s+(\S+)`, PS `-OutFile <path>`
- Redirect fixes: permit optional `1` immediately before `>` in
  REDIRECT_RE (currently `[^->\d]` guard eats `1>`); add `>|` alternative.
- Windows/Git-Bash: a target matching `^/([a-zA-Z])/` is rewritten to
  `<drive>:/` before resolving (audit A5.5: `/c/...` currently resolves to
  `C:\c\...` and fails open).
- Residual gaps that STAY (document in CHANGELOG + README): writes inside
  quoted inline code (`python -c "..."`) — existing; `cd dir && ...`
  compound resolution — new screens still judge relative targets against
  payload cwd (over/under-block documented).
- False-positive guard (audit 5.8): before blocking a redirect target,
  allow if extension is in a scratch allowlist `{.log,.txt,.out,.tmp}` AND
  path is not in any approved scope. [DECIDE] default allowlist as stated.
- Tests: each new screen blocks against a gated file and allows /dev/null,
  scratch logs, out-of-repo paths; `1>` and `>|` block; `/c/...` path
  form blocks on Windows runner (use forward-slash payloads, they work
  cross-platform).

## A6. Status validation invariants (validate_status.py)

Current: shape-only. Add (exit 2 with message, same style):
- `phase` in (implement, verify, document) ⇒ `plan_approved.approved` true
- `phase` == done ⇒ `docs_complete.approved` true
- `slug` == parent directory name
- `updatedAt` parses as ISO-8601 (`datetime.fromisoformat` after
  stripping trailing Z)
- gate `at` non-null when `approved` true
Constants come FROM the schema: load `schema/status.schema.json` at hook
start (path: `Path(__file__).parents[1]/"schema"/...`), read the slug
pattern and phase enum from it; fall back to hardcoded copies on any load
error (fail-open). This makes the schema file load-bearing.
- Matcher: extend hooks.json PostToolUse to `Edit|Write|NotebookEdit`.
  Bash-written status.json remains unvalidated — documented residual.
- STATUS_RE currently skips `specs/archive/**` — keep (archived state is
  frozen history), but add a comment saying so.
- Tests: each invariant red/green; schema↔hook parity test (phase enum and
  slug pattern in the hook match the schema by construction — assert by
  reading both).

## A7. Small confirmed fixes

- `session_state.py:41` unknown phase → falls into "shipped" line. Fix:
  unknown phases render `?<phase>` with no resume hint (mirror
  build_dashboard.py:62 fallback). Test with `phase: "vibing"`.
- `session_state.py` UnicodeEncodeError under ascii stdout: wrap prints —
  `sys.stdout.reconfigure(errors="replace")` at main() start (3.7+ ok).
- `build_dashboard.py:26` ARTIFACT_FILES += `REVIEW.md`; `commands/
  status.md` next-action line mentions an existing REVIEW.md.
- Eval grader `evals/requirements-creates-spec/graders/artifacts.md`: add
  condition — unattended run MUST have written `REVIEW.md` ending with the
  approve line.
- README (marketplace root): "32-case" → actual count (compute at end);
  "one feature shipped" → three. demo-app/README.md: remove shipped items
  from "Demo feature ideas" (due dates, remove) leaving priorities item.
- demo-app 001 spec: add one-line header note "pre-1.0 spec format
  (R-IDs, no EARS) — kept as historical artifact".

## Verification plan (unit level)

- Full suite green; new tests ≈ +20-25 (target ≥ 58 total).
- Manual probe series from IMPROVEMENTS-2.md P0 items 1-7 re-run by hand
  against the fixed hooks — every one must now block (or allow) correctly;
  paste transcript into the unit report.
- Perf sanity: gated-call overhead stays < 100 ms with 50 features
  (audit measured 47 ms baseline).
