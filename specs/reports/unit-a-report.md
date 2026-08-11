# Unit A report — v1.2.0 "honest gate"

Spec: `01-honest-gate.md` (removed after completion; in git history). Source analysis:
[IMPROVEMENTS-2.md](../../IMPROVEMENTS-2.md) P0 items 1–8.
Plugin v1.1.0 → **v1.2.0**, installed user-scope and verified enabled.

## Shipped

| Item | Status | Notes |
|---|---|---|
| A1 empty dirname no longer collected | done | root-level entry stops unlocking the repo root |
| A1 `removeprefix("./")` (was `lstrip`) | done | `.github/...` matches itself; `..` entries dropped, not rewritten |
| A1 trailing slash = directory prefix | done | no-dot heuristic kept as the fallback for legacy entries |
| A2 root requires metrics.jsonl or `*/status.json` | done | walk continues past non-qualifying `specs/` dirs |
| A2 same rule in session_state.py | done | duplicated as `is_sdlc_root()` with a comment naming its twin |
| A3 per-feature fail-open + union | done | union documented in README Enforcement |
| A4 `document` phase unlocks like implement/verify | done | |
| A4 root `CHANGELOG*` always allowed | done | |
| A4 phase × permission matrix test | done | `tests/test_gate_matrix.py`, 42 cases |
| A5 rm / truncate / dd / mv / cp / curl -o screens | **deviated** | see below |
| A5 git checkout `--` paths | done | `git restore` added too (same destructive shape) |
| A5 git apply / patch → repo-root treatment | **deviated** | see below |
| A5 PowerShell Remove-/Move-/Copy-Item, -OutFile | done | full cmdlet names only; aliases (`ri`, `mi`, `del`) unscreened |
| A5 `1>` and `>\|` redirect forms | done | `2> file` is now screened as well |
| A5 `/c/...` → `C:/...` rewrite | done | applied to command targets only, `os.name == "nt"` guarded |
| A5 scratch-extension allowlist | **deviated** | see below |
| A6 five status invariants | done | plan gate, docs_complete, slug↔dir, slug pattern, ISO updatedAt |
| A6 constants loaded from the schema | done | `load_constants()`, `FALLBACK` mirror, parity tests both ways |
| A6 PostToolUse matcher + NotebookEdit | done | `Edit\|Write\|NotebookEdit`; contract asserted in a test |
| A6 archive exclusion kept + commented | done | |
| A7 unknown phase not reported as "shipped" | done | |
| A7 ascii-stdout crash | done | root cause was the em-dash in the hook's own board lines |
| A7 dashboard reads REVIEW.md; status.md mentions it | done | |
| A7 eval grader requires REVIEW.md | done | |
| A7 README counts corrected | done | "32-case" → 118-case, "one feature shipped" → three |
| A7 demo-app README / 001 spec header | done | |
| *(unplanned)* `/sdlc:dashboard` frontmatter | done | see "Found along the way" |

### Deviations

1. **`mv` screens every positional, not just first + last.** The spec said
   "LAST path arg AND for mv also first". With `mv a b c dir/` every source is
   destroyed, so first+last leaves `b` unscreened. Taking all positionals is a
   superset of the spec and adds no false positives — every positional of `mv`
   is either a destroyed source or the destination. `cp` follows the spec
   (last only): its sources are read-only.
2. **`git apply` / `patch` block via a dedicated message, not a synthetic
   repo-root path.** The spec's "treat as a write to repo root" would have
   produced a scope-violation message naming `.` as the file, which is
   confusing and would have made the reason unguessable. Same verdict, honest
   wording: they are refused whenever the enclosing repo has any features on
   the board, and allowed outside one. Note this is strict — `git apply` is
   refused even during an approved implement phase, because the gate genuinely
   cannot enumerate what a patch writes.
3. **Scratch allowlist ignores the spec's second condition.** The spec said
   "extension in the allowlist AND path is not in any approved scope"; the
   second clause is vacuous, because an in-scope path is already allowed by
   the scope check that runs first. Implemented as the extension test alone —
   but only for *write*-kind targets (redirect, tee, `cp` destination,
   `curl -o`, Out-File). Destructive verbs get no pass, so `rm notes.txt` is
   still gated. Without that split, the allowlist would have made every
   `.txt`/`.log` file in the repo freely deletable.

Nothing was dropped.

### Found along the way (unplanned, fixed)

`claude plugin validate --strict` failed on v1.1.0 for two reasons unrelated to
the audit, both now fixed:

- `commands/dashboard.md` frontmatter was invalid YAML —
  `argument-hint: [--serve] [output path]` is two flow sequences on one line.
  The runtime silently dropped **all** of that command's metadata, description
  included, so `/sdlc:dashboard` had no description anywhere in the UI.
- `marketplace.json` had no `description`.

Both manifests now pass `--strict`. Worth adding to CI in a later unit.

## Test delta

**36 → 118 passing** (+82; 78 distinct test functions, 118 with parametrized
cases). Full suite green, no test rewritten — conftest gained `slug=` on
`write_feature`, plus `plan_with()`, `as_shell_path()` and `load_hook_module()`.

New, by file:

- **`tests/test_gate_matrix.py`** (new file, 42 cases) —
  `test_edit_permission_matrix` (30: 6 phases × 5 file classes),
  `test_bash_write_follows_the_same_matrix` (12).
- **`tests/test_gate_check.py`** (+25) — `test_root_entry_does_not_unlock_sibling_root_files`,
  `test_dot_prefixed_entry_matches_itself_not_a_mangled_path`,
  `test_leading_dot_slash_entry_is_normalized`,
  `test_trailing_slash_entry_is_always_a_directory_prefix`,
  `test_directory_entry_does_not_unlock_its_parent`,
  `test_parent_traversal_entry_is_ignored`,
  `test_decoy_specs_dir_does_not_shadow_the_real_root`,
  `test_repo_with_only_a_decoy_specs_dir_is_untouched`,
  `test_metrics_jsonl_qualifies_a_root_without_features`,
  `test_scope_is_the_union_of_features_that_declare_one`,
  `test_fails_open_only_when_no_feature_declares_scope`,
  `test_destructive_posix_commands_are_screened` (10 payloads),
  `test_mv_screens_source_as_well_as_destination`,
  `test_destructive_powershell_cmdlets_are_screened` (5 payloads),
  `test_opaque_patch_commands_are_blocked_in_a_gated_repo`,
  `test_opaque_patch_commands_allowed_outside_sdlc_repos`,
  `test_destructive_commands_outside_the_repo_are_allowed`,
  `test_explicit_stdout_redirect_forms_are_screened`,
  `test_posix_drive_form_target_is_resolved_on_windows`,
  `test_scratch_log_redirects_are_allowed`,
  `test_scratch_extension_allowance_does_not_cover_deletion`,
  `test_root_changelog_always_allowed`, `test_nested_changelog_is_not_exempt`.
- **`tests/test_validate_status.py`** (+13) — `test_implement_without_plan_approval_rejected`,
  `test_verify_and_document_also_require_plan_approval`,
  `test_done_without_docs_complete_rejected`,
  `test_slug_must_match_the_directory_name`,
  `test_slug_must_match_the_schema_pattern`,
  `test_unparseable_updated_at_rejected`, `test_iso_timestamp_forms_accepted`,
  `test_archived_status_files_are_left_alone`,
  `test_hook_constants_come_from_the_schema`,
  `test_hardcoded_fallbacks_match_the_schema`,
  `test_unreadable_schema_falls_back`, `test_malformed_schema_falls_back`,
  `test_hooks_json_validates_every_write_tool`.
- **`tests/test_session_state.py`** (+3) — `test_unknown_phase_is_not_reported_as_shipped`,
  `test_decoy_specs_dir_does_not_become_the_board_root`,
  `test_survives_ascii_only_stdout`.
- **`tests/test_build_dashboard.py`** (+1) — `test_review_questionnaire_is_readable_on_the_board`.

All 82 were written first and observed failing (37 failing test *functions*
before any fix; the parametrized matrix accounts for the rest).

## Manual probe series (IMPROVEMENTS-2 P0 1–8)

Re-run by hand against the fixed hooks, outside pytest. 30/30 as expected:

```
     probe                                                          expect  got
PASS 1. sibling root file (setup.py) vs entry `taskler.py`          BLOCK   BLOCK
PASS 1. the listed root file itself                                 allow   allow
PASS 2. listed .github/workflows/ci.yml                             allow   allow
PASS 2. mangled github/workflows/ci.yml                             BLOCK   BLOCK
PASS 3. rm -rf src/app.py                                           BLOCK   BLOCK
PASS 3. mv src/app.py src/b.py                                      BLOCK   BLOCK
PASS 3. cp x src/app.py                                             BLOCK   BLOCK
PASS 3. truncate -s 0 src/app.py                                    BLOCK   BLOCK
PASS 3. dd if=/dev/zero of=src/app.py                               BLOCK   BLOCK
PASS 3. git checkout -- src/app.py                                  BLOCK   BLOCK
PASS 3. curl -o src/app.py https://e.com                            BLOCK   BLOCK
PASS 3. git apply fix.diff                                          BLOCK   BLOCK
PASS 3. patch -p1 < fix.diff                                        BLOCK   BLOCK
PASS 3. Remove-Item -Path src/app.py                                BLOCK   BLOCK
PASS 4. file under a decoy api/specs/ root                          BLOCK   BLOCK
PASS 5. alpha.py (feature 1 scope)                                  allow   allow
PASS 5. beta.py (feature 2 scope)                                   allow   allow
PASS 5. gamma.py (nobody's scope, 003 unparseable)                  BLOCK   BLOCK
PASS 6. document phase writes root CHANGELOG.md                     allow   allow
PASS 6. document phase writes its in-scope file                     allow   allow
PASS 6. document phase writes out-of-scope code                     BLOCK   BLOCK
PASS 7. echo x 1> alpha2.py                                         BLOCK   BLOCK
PASS 7. echo x >| alpha2.py                                         BLOCK   BLOCK
PASS 7. echo x > /c/Users/.../repo/alpha2.py                        BLOCK   BLOCK
PASS 7. dotted dir entry src/v1.2/ allows src/v1.2/mod.py           allow   allow
PASS 7. pytest > test-output.log (scratch)                          allow   allow
PASS 8. phase implement with plan_approved false                    BLOCK   BLOCK
PASS 8. phase done without docs_complete                            BLOCK   BLOCK
PASS 8. updatedAt 'yesterday'                                       BLOCK   BLOCK
PASS 8. slug != directory name                                      BLOCK   BLOCK

30/30 probes as expected
perf, 50 features (incl. python startup): min 44 ms, median 47 ms, max 164 ms
```

Perf sanity holds: 47 ms median with 50 features on the board, unchanged from
the audit's 47 ms baseline and well under the 100 ms budget. The added
per-feature work is one extra `glob` during root detection; scope parsing was
already per-feature.

## [VERIFY] outcomes

1. **`claude plugin validate --strict` syntax — confirmed.** `claude plugin
   validate [--strict] <path>`; `<path>` is a plugin *or* marketplace
   directory, and `--strict` "treat[s] warnings as errors (exit 1)". Both
   `./marketplace/plugins/sdlc` and `./marketplace` now exit 0 (they did not
   before this unit — see "Found along the way").

The other five open [VERIFY] questions in `specs/README.md` belong to units
B–D and were not touched.

## [DECIDE] defaults applied

- **Scope union across concurrently approved features stays** (A3). Recorded
  in CHANGELOG 1.2.0 and in the README Enforcement section as an explicit
  property, not an accident: per-feature attribution of an edit is unknowable
  at hook level.
- **Document phase gets plan-scoped edit rights + root `CHANGELOG*` always
  allowed** (A4).
- **Scratch-extension allowlist `.log/.txt/.out/.tmp`** (A5), narrowed to
  write-kind targets only (deviation 3 above).

## Residual gaps knowingly left

All listed in CHANGELOG 1.2.0 under "Residual gaps knowingly left", and the
first four in the README Enforcement section:

- Writes hidden inside quoted inline code (`python -c "..."`) — unchanged.
- `cd dir && ...` compounds: relative targets are judged against the tool
  call's cwd, so a `cd` into a subdirectory can over- or under-block.
- `status.json` written via Bash bypasses PostToolUse validation entirely
  (the hook only fires on Edit/Write/NotebookEdit).
- Redirects to `.log/.txt/.out/.tmp` are allowed by design.
- `specs/archive/**` is excluded from validation on purpose (frozen history);
  a repo whose features are *all* archived qualifies as a root only via
  `specs/metrics.jsonl`.
- PowerShell aliases (`ri`, `mi`, `del`, `erase`) and POSIX `unlink`/`shred`
  are unscreened; only the full cmdlet/command names are.
- `git checkout <branch>` (no `--`) is not screened: it names a ref, and
  treating refs as paths would false-positive on every branch switch.

## Process note — the repo layout changed mid-unit

Between my last edit and the commit step, the three-repo layout was folded into
a single monorepo: `marketplace/.git` and `demo-app/.git` were removed
(histories preserved in untracked `.git-bundles/`) and commit `94a0e39`
"monorepo: fold marketplace and demo-app into this repo" swept my in-progress
Unit A files in with it. I verified nothing was lost or altered (working tree
clean, 118/118 green, every A7 doc edit present in HEAD) and did **not** rewrite
that already-pushed commit. Consequence for the orchestrator's conventions:
there is now one repo, not three, so this unit has **one** code commit
(`94a0e39`, under someone else's message) plus this report's commit carrying
the `v1.2.0: honest gate` summary. Units B and C should assume a single repo.

## Smoke checklist for the next session (Unit B)

Run these first, in a **new** session (plugin content snapshots at session
start, so v1.2.0 hooks are only live from now on).

```bash
cd C:/Users/Alex/PycharmProjects/coding-workflow
python -m pytest marketplace/tests -q          # expect: 118 passed
claude plugin validate --strict ./marketplace/plugins/sdlc   # expect: ✔ Validation passed
claude plugin list | grep -A1 sdlc@sdlc-marketplace          # expect: Version: 1.2.0
```

Live gate checks (these exercise the *installed* hooks, not the repo copy):

1. In `demo-app/` (three features, all `done`), ask Claude to edit
   `taskler.py` → expect the gate to refuse with "no feature is in an approved
   implement/verify/document phase". Before v1.2.0 this also refused, but for
   the wrong reason; the message now names `document` too.
2. In `demo-app/`, ask Claude to run `rm taskler.py` → expect a block. On
   v1.1.0 this was allowed — it is the single most visible behaviour change.
3. In `coding-workflow/` itself, edit any file under `marketplace/` → expect
   **no** gate message: `specs/` here holds program documentation with no
   `status.json` and no `metrics.jsonl`, so it is deliberately not a board.
   (This is A2 working; on v1.1.0 this directory *was* a false root.)
4. Open a session in `demo-app/` → SessionStart should print three `shipped`
   lines and no "in flight" work.

If check 3 ever starts blocking, something added feature state under
`coding-workflow/specs/` — that folder must stay documentation-only.
