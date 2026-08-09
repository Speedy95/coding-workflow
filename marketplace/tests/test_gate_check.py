from conftest import (PLAN_WITHOUT_SCOPE, SPEC_WITH_MINI_PLAN,
                      SPEC_WITHOUT_MINI_PLAN, run_hook)


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


def test_bash_redirect_into_specs_allowed(repo):
    repo.write_feature(phase="requirements")
    assert run_hook("gate_check.py", bash_payload(repo, "echo x > specs/001-x/notes.md"))[0] == 0
