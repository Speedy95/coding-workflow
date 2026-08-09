import json

from conftest import (PLAN_WITH_SCOPE, PLAN_WITHOUT_SCOPE, SPEC_WITH_MINI_PLAN,
                      SPEC_WITHOUT_MINI_PLAN, as_shell_path, plan_with, run_hook)


def edit_payload(repo, path, cwd=None, tool="Edit"):
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {"cwd": str(cwd or repo), "tool_name": tool,
            "tool_input": {key: str(repo / path)}}


def bash_payload(repo, command, tool="Bash"):
    return {"cwd": str(repo), "tool_name": tool, "tool_input": {"command": command}}


# ── phase gating ────────────────────────────────────────────────────────────

def test_blocks_code_edit_before_approval(repo):
    repo.write_feature(phase="requirements")
    code, out = run_hook("gate_check.py", edit_payload(repo, "src/app.py"))
    assert code == 2 and "approved" in out


def test_blocks_even_when_cwd_is_outside_repo(repo, tmp_path_factory):
    """P0 regression: root must derive from the target path, not the cwd."""
    repo.write_feature(phase="requirements")
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    code, out = run_hook("gate_check.py", edit_payload(repo, "src/app.py", cwd=elsewhere))
    assert code == 2


def test_blocks_notebook_edit(repo):
    repo.write_feature(phase="requirements")
    code, _ = run_hook("gate_check.py", edit_payload(repo, "src/nb.ipynb", tool="NotebookEdit"))
    assert code == 2


def test_allows_specs_lessons_docs_readme(repo):
    repo.write_feature(phase="requirements")
    for path in ("specs/001-x/spec.md", "lessons/a.md", "docs/x.md", "README.md"):
        code, _ = run_hook("gate_check.py", edit_payload(repo, path))
        assert code == 0, path


def test_allows_when_no_specs_dir(tmp_path):
    payload = {"cwd": str(tmp_path), "tool_name": "Edit",
               "tool_input": {"file_path": str(tmp_path / "x.py")}}
    assert run_hook("gate_check.py", payload)[0] == 0


def test_allows_when_no_features_yet(repo):
    assert run_hook("gate_check.py", edit_payload(repo, "src/app.py"))[0] == 0


def test_malformed_stdin_fails_open():
    import subprocess, sys
    from conftest import HOOKS
    proc = subprocess.run([sys.executable, str(HOOKS / "gate_check.py")],
                          input="not json", capture_output=True, text=True)
    assert proc.returncode == 0


# ── scope enforcement ───────────────────────────────────────────────────────

def test_allows_listed_file_in_approved_implement(repo):
    repo.write_feature(phase="implement", spec=True, plan=True)
    (repo / "taskler.py").write_text("", encoding="utf-8")
    assert run_hook("gate_check.py", edit_payload(repo, "taskler.py"))[0] == 0


def test_allows_new_file_in_listed_directory(repo):
    repo.write_feature(phase="implement", spec=True, plan=True)
    assert run_hook("gate_check.py", edit_payload(repo, "tests/test_new.py"))[0] == 0


def test_blocks_out_of_scope_file(repo):
    repo.write_feature(phase="implement", spec=True, plan=True)
    code, out = run_hook("gate_check.py", edit_payload(repo, "src/unrelated.py"))
    assert code == 2 and "Affected files" in out


def test_fails_open_when_plan_has_no_scope_section(repo):
    repo.write_feature(phase="implement", spec=True, plan=True, plan_md=PLAN_WITHOUT_SCOPE)
    assert run_hook("gate_check.py", edit_payload(repo, "src/unrelated.py"))[0] == 0


# ── quick track: scope from the spec's mini-plan (no plan.md) ───────────────

def test_quick_track_scopes_from_spec_mini_plan(repo):
    """Regression (e2e run 002): quick features must not unlock the whole repo."""
    repo.write_feature(phase="implement", spec=True, plan=True, track="quick",
                       plan_md=None, spec_md=SPEC_WITH_MINI_PLAN)
    assert run_hook("gate_check.py", edit_payload(repo, "taskler.py"))[0] == 0
    assert run_hook("gate_check.py", edit_payload(repo, "tests/test_new.py"))[0] == 0
    code, out = run_hook("gate_check.py", edit_payload(repo, "src/unrelated.py"))
    assert code == 2 and "mini-plan" in out


def test_quick_track_without_affected_line_fails_open(repo):
    repo.write_feature(phase="implement", spec=True, plan=True, track="quick",
                       plan_md=None, spec_md=SPEC_WITHOUT_MINI_PLAN)
    assert run_hook("gate_check.py", edit_payload(repo, "src/unrelated.py"))[0] == 0


def test_spec_fallback_applies_when_plan_unparseable(repo):
    """An unparseable plan.md falls back to the spec's Affected-files line."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=PLAN_WITHOUT_SCOPE, spec_md=SPEC_WITH_MINI_PLAN)
    code, _ = run_hook("gate_check.py", edit_payload(repo, "src/unrelated.py"))
    assert code == 2


# ── bash / powershell screening ─────────────────────────────────────────────

def test_bash_redirect_into_gated_file_blocked(repo):
    repo.write_feature(phase="requirements")
    code, _ = run_hook("gate_check.py", bash_payload(repo, "echo hacked > src/app.py"))
    assert code == 2


def test_bash_innocuous_commands_allowed(repo):
    repo.write_feature(phase="requirements")
    for cmd in ("git status", "python -m pytest", "ls -la", "echo hi > /dev/null",
                'python -c "print(1 if 2 > 1 else 0)"', "git diff 2>&1"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 0, cmd


def test_bash_tee_and_sed_blocked(repo):
    repo.write_feature(phase="requirements")
    assert run_hook("gate_check.py", bash_payload(repo, "cat x | tee src/app.py"))[0] == 2
    assert run_hook("gate_check.py", bash_payload(repo, "sed -i 's/a/b/' src/app.py"))[0] == 2


def test_powershell_set_content_blocked(repo):
    repo.write_feature(phase="requirements")
    code, _ = run_hook("gate_check.py", bash_payload(
        repo, 'Set-Content -Path "src/app.py" -Value hacked', tool="PowerShell"))
    assert code == 2


# ── review-fix regressions (v1.2.1) ─────────────────────────────────────────

def test_git_global_flags_do_not_shadow_the_subcommand(repo):
    repo.write_feature(phase="requirements")
    (repo / "src" / "app.py").write_text("", encoding="utf-8")
    for cmd in ("git -C . restore src/app.py",
                "git -C . checkout -- src/app.py",
                "git --git-dir x checkout -- src/app.py"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 2, cmd


def test_git_checkout_pathspec_without_dashes_is_screened(repo):
    """git's DWIM turns `checkout <existing-file>` into a revert."""
    repo.write_feature(phase="requirements")
    (repo / "src" / "app.py").write_text("", encoding="utf-8")
    assert run_hook("gate_check.py", bash_payload(repo, "git checkout src/app.py"))[0] == 2


def test_git_checkout_branch_name_is_not_a_path(repo):
    repo.write_feature(phase="requirements")
    for cmd in ("git checkout main", "git checkout -b feature-x"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 0, cmd


def test_quoted_paths_with_spaces_are_screened(repo):
    repo.write_feature(phase="requirements")
    for cmd in ('echo hacked > "my dir/app.py"', 'rm "my dir/app.py"',
                'Remove-Item -Path "my dir/app.py"'):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 2, cmd


def test_quoted_code_strings_are_still_ignored(repo):
    repo.write_feature(phase="requirements")
    for cmd in ('python -c "print(1 if 2 > 1 else 0)"',
                'git commit -m "fix: a > b comparison"'):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 0, cmd


def test_powershell_literalpath_and_filepath_are_screened(repo):
    repo.write_feature(phase="requirements")
    for cmd in ("Set-Content -LiteralPath src/app.py -Value out.log",
                "Out-File -FilePath src/app.py -InputObject x",
                "Add-Content -LiteralPath src/app.py hacked"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd, tool="PowerShell"))[0] == 2, cmd


def test_sed_and_tee_screen_every_file_argument(repo):
    repo.write_feature(phase="requirements")
    assert run_hook("gate_check.py",
                    bash_payload(repo, "sed -i 's/a/b/' notes.log src/app.py"))[0] == 2
    assert run_hook("gate_check.py",
                    bash_payload(repo, "cat x | tee first.log src/app.py"))[0] == 2


def test_scratch_extensions_stay_gated_before_approval(repo):
    """v1.1.0 guarantee restored: with nothing approved, every write is gated."""
    repo.write_feature(phase="requirements")
    for cmd in ("pip freeze > requirements.txt", "echo x > CMakeLists.txt"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 2, cmd


def test_hooks_json_command_survives_missing_python(repo):
    """The manifest command must fall back to python3 (macOS/Ubuntu have no python)."""
    import json as _json
    from conftest import HOOKS
    manifest = _json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
    commands = [h["command"] for group in manifest["hooks"].values()
                for entry in group for h in entry["hooks"]]
    assert commands, "no hook commands found"
    for command in commands:
        assert "python3" in command, f"no python3 fallback in: {command}"


def test_hooks_json_gate_command_blocks_via_shell(repo):
    """Run the manifest's literal PreToolUse command through a real shell."""
    import json as _json
    import os
    import shutil
    import subprocess
    from conftest import HOOKS
    bash = shutil.which("bash")
    if not bash:
        import pytest
        pytest.skip("no bash on PATH")
    manifest = _json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
    command = manifest["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    repo.write_feature(phase="requirements")
    payload = _json.dumps(edit_payload(repo, "src/app.py"))
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(HOOKS.parent))
    proc = subprocess.run([bash, "-c", command], input=payload,
                          capture_output=True, text=True, env=env, timeout=30)
    assert proc.returncode == 2, proc.stderr + proc.stdout


def test_bash_redirect_into_specs_allowed(repo):
    repo.write_feature(phase="requirements")
    assert run_hook("gate_check.py", bash_payload(repo, "echo x > specs/001-x/notes.md"))[0] == 0


# ── A1: scope matching (audit P0 items 1, 2, 7) ──────────────────────────────

def test_root_entry_does_not_unlock_sibling_root_files(repo):
    """P0-1: dirname('taskler.py') is '' — every root-level file must not match it."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("taskler.py"))
    assert run_hook("gate_check.py", edit_payload(repo, "taskler.py"))[0] == 0
    for sibling in ("setup.py", "Makefile", "conftest.py"):
        code, _ = run_hook("gate_check.py", edit_payload(repo, sibling))
        assert code == 2, sibling


def test_dot_prefixed_entry_matches_itself_not_a_mangled_path(repo):
    """P0-2: lstrip('./') turned '.github/...' into 'github/...'."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with(".github/workflows/ci.yml"))
    assert run_hook("gate_check.py", edit_payload(repo, ".github/workflows/ci.yml"))[0] == 0
    code, _ = run_hook("gate_check.py", edit_payload(repo, "github/workflows/ci.yml"))
    assert code == 2


def test_leading_dot_slash_entry_is_normalized(repo):
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("./taskler.py"))
    assert run_hook("gate_check.py", edit_payload(repo, "taskler.py"))[0] == 0


def test_trailing_slash_entry_is_always_a_directory_prefix(repo):
    """P0-7: 'src/v1.2/' has a dot in its basename — the no-dot heuristic missed it."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("src/v1.2/"))
    assert run_hook("gate_check.py", edit_payload(repo, "src/v1.2/mod.py"))[0] == 0
    code, _ = run_hook("gate_check.py", edit_payload(repo, "src/other.py"))
    assert code == 2


def test_directory_entry_does_not_unlock_its_parent(repo):
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("src/v1.2/"))
    code, _ = run_hook("gate_check.py", edit_payload(repo, "src/sibling.py"))
    assert code == 2


def test_parent_traversal_entry_is_ignored(repo):
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("../outside.py", "taskler.py"))
    assert run_hook("gate_check.py", edit_payload(repo, "taskler.py"))[0] == 0
    code, _ = run_hook("gate_check.py", edit_payload(repo, "outside.py"))
    assert code == 2


# ── A2: root detection (audit P0 item 4) ────────────────────────────────────

def test_decoy_specs_dir_does_not_shadow_the_real_root(repo):
    """P0-4: an api/specs/ OpenAPI folder silently ungated everything beneath it."""
    repo.write_feature(phase="requirements")
    (repo / "api" / "specs").mkdir(parents=True)
    (repo / "api" / "specs" / "openapi.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")
    code, _ = run_hook("gate_check.py", edit_payload(repo, "api/handler.py"))
    assert code == 2


def test_repo_with_only_a_decoy_specs_dir_is_untouched(tmp_path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "openapi.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")
    payload = {"cwd": str(tmp_path), "tool_name": "Edit",
               "tool_input": {"file_path": str(tmp_path / "app.py")}}
    assert run_hook("gate_check.py", payload)[0] == 0


def test_metrics_jsonl_qualifies_a_root_without_features(repo):
    """A repo whose features are all archived still resolves as its own root.

    Contrast with the decoy test above: the same nesting, but specs/metrics.jsonl
    makes the inner dir a real root, so the outer root's gate stops at it.
    """
    repo.write_feature(phase="requirements")  # outer root blocks code edits
    inner_specs = repo / "vendor" / "lib" / "specs"
    inner_specs.mkdir(parents=True)
    (inner_specs / "metrics.jsonl").write_text('{"event":"verify"}\n', encoding="utf-8")
    assert run_hook("gate_check.py", edit_payload(repo, "vendor/lib/app.py"))[0] == 0


# ── A3: multi-feature scope union + per-feature fail-open ───────────────────

def test_scope_is_the_union_of_features_that_declare_one(repo):
    """P0-5: one unparseable plan used to disable scoping for every feature."""
    repo.write_feature(slug="001-x", phase="implement", spec=True, plan=True,
                       plan_md=plan_with("alpha.py"))
    repo.write_feature(slug="002-y", phase="implement", spec=True, plan=True,
                       plan_md=plan_with("beta.py"))
    repo.write_feature(slug="003-z", phase="implement", spec=True, plan=True,
                       plan_md=PLAN_WITHOUT_SCOPE)
    assert run_hook("gate_check.py", edit_payload(repo, "alpha.py"))[0] == 0
    assert run_hook("gate_check.py", edit_payload(repo, "beta.py"))[0] == 0
    code, _ = run_hook("gate_check.py", edit_payload(repo, "gamma.py"))
    assert code == 2


def test_fails_open_only_when_no_feature_declares_scope(repo):
    repo.write_feature(slug="001-x", phase="implement", spec=True, plan=True,
                       plan_md=PLAN_WITHOUT_SCOPE)
    repo.write_feature(slug="002-y", phase="implement", spec=True, plan=True,
                       plan_md=PLAN_WITHOUT_SCOPE)
    assert run_hook("gate_check.py", edit_payload(repo, "gamma.py"))[0] == 0


# ── A5: command screening — destructive verbs (audit P0 item 3) ─────────────

def test_destructive_posix_commands_are_screened(repo):
    repo.write_feature(phase="requirements")
    for cmd in ("rm -rf src/app.py",
                "rm src/app.py",
                "mv src/app.py src/moved.py",
                "cp /etc/hosts src/app.py",
                "truncate -s 0 src/app.py",
                "dd if=/dev/zero of=src/app.py",
                "git checkout -- src/app.py",
                "git restore src/app.py",
                "curl -o src/app.py https://example.com/x",
                "curl --output src/app.py https://example.com/x"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 2, cmd


def test_mv_screens_source_as_well_as_destination(repo):
    """Moving a gated file out of scope destroys it just as surely as writing it."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       plan_md=plan_with("scratch/"))
    (repo / "scratch").mkdir()
    code, _ = run_hook("gate_check.py", bash_payload(repo, "mv src/app.py scratch/app.py"))
    assert code == 2


def test_destructive_powershell_cmdlets_are_screened(repo):
    repo.write_feature(phase="requirements")
    for cmd in ('Remove-Item -Path "src/app.py" -Force',
                'Remove-Item src/app.py',
                'Move-Item -Path src/app.py -Destination src/moved.py',
                'Copy-Item other.txt -Destination src/app.py',
                'Invoke-WebRequest https://example.com -OutFile src/app.py'):
        assert run_hook("gate_check.py", bash_payload(repo, cmd, tool="PowerShell"))[0] == 2, cmd


def test_opaque_patch_commands_are_blocked_in_a_gated_repo(repo):
    repo.write_feature(phase="requirements")
    for cmd in ("git apply fix.diff", "patch -p1 -i fix.diff", "patch -p1 < fix.diff"):
        code, out = run_hook("gate_check.py", bash_payload(repo, cmd))
        assert code == 2, cmd
        assert "cannot" in out.lower(), cmd


def test_opaque_patch_commands_allowed_outside_sdlc_repos(tmp_path):
    payload = {"cwd": str(tmp_path), "tool_name": "Bash",
               "tool_input": {"command": "git apply fix.diff"}}
    assert run_hook("gate_check.py", payload)[0] == 0


def test_destructive_commands_outside_the_repo_are_allowed(repo, tmp_path_factory):
    repo.write_feature(phase="requirements")
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    cmd = f"rm -rf {as_shell_path(elsewhere / 'junk.py')}"
    assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 0


# ── A5: redirect forms and false-positive guards ────────────────────────────

def test_explicit_stdout_redirect_forms_are_screened(repo):
    """P0-7: `1>` was eaten by the digit guard, `>|` was never matched."""
    repo.write_feature(phase="requirements")
    for cmd in ("echo hacked 1> src/app.py",
                "echo hacked >| src/app.py",
                "echo hacked 1>> src/app.py"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 2, cmd


def test_posix_drive_form_target_is_resolved_on_windows(repo):
    """P0-7: Git Bash hands us /c/... — it used to resolve to <cwd>/c/... and fail open."""
    repo.write_feature(phase="requirements")
    target = as_shell_path((repo / "src" / "app.py"))
    code, _ = run_hook("gate_check.py", bash_payload(repo, f"echo hacked > {target}"))
    assert code == 2


def test_scratch_log_redirects_are_allowed(repo):
    """Audit 5.8: `pytest > test-output.log` is scratch, not a code change.

    Only once a feature is approved, though — before approval every enumerable
    write stays gated (review v1.2.1; see
    test_scratch_extensions_stay_gated_before_approval).
    """
    repo.write_feature(phase="implement", spec=True, plan=True)
    for cmd in ("python -m pytest > test-output.log",
                "python -m pytest > out.txt",
                "make 2> build.out",
                "echo x > scratch.tmp"):
        assert run_hook("gate_check.py", bash_payload(repo, cmd))[0] == 0, cmd


def test_scratch_extension_allowance_does_not_cover_deletion(repo):
    repo.write_feature(phase="requirements")
    assert run_hook("gate_check.py", bash_payload(repo, "rm notes.txt"))[0] == 2


# ── A4: CHANGELOG is always writable at the repo root ───────────────────────

def test_root_changelog_always_allowed(repo):
    repo.write_feature(phase="requirements")
    for path in ("CHANGELOG.md", "CHANGELOG"):
        assert run_hook("gate_check.py", edit_payload(repo, path))[0] == 0, path


def test_nested_changelog_is_not_exempt(repo):
    repo.write_feature(phase="requirements")
    code, _ = run_hook("gate_check.py", edit_payload(repo, "src/CHANGELOG.md"))
    assert code == 2
