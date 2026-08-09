import json
import os
import subprocess
import sys

from conftest import HOOKS, run_hook


def test_silent_outside_sdlc_repos(tmp_path):
    code, out = run_hook("session_state.py", {"cwd": str(tmp_path)})
    assert code == 0 and out.strip() == ""


def test_silent_with_no_features(repo):
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert code == 0 and out.strip() == ""


def test_injects_board_state(repo):
    repo.write_feature(phase="implement", spec=True, plan=True,
                       tasks={"done": 3, "total": 5})
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert code == 0
    assert "001-x" in out and "implement 3/5" in out and "/sdlc:implement" in out


def test_partial_tasks_object_does_not_crash_board(repo):
    """A hand-written status.json may carry tasks without 'done' (review v1.2.1)."""
    repo.write_feature(phase="implement", spec=True, plan=True,
                       tasks={"total": 5})
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert code == 0 and "001-x" in out and "0/5" in out


def test_pending_review_questionnaire_flagged(repo):
    fdir = repo.write_feature(phase="requirements")
    (fdir / "spec.md").write_text("# spec", encoding="utf-8")
    (fdir / "REVIEW.md").write_text("1. ...\nAnswer:\n", encoding="utf-8")
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert code == 0 and "REVIEW.md questionnaire present" in out


def test_quick_track_and_done_shown(repo):
    repo.write_feature(phase="done", spec=True, plan=True, track="quick")
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert "shipped" in out and "[quick]" in out


def test_unknown_phase_is_not_reported_as_shipped(repo):
    """An unrecognised phase fell through to the 'shipped' line — silently wrong."""
    repo.write_feature(phase="vibing")
    code, out = run_hook("session_state.py", {"cwd": str(repo)})
    assert code == 0
    assert "vibing" in out
    assert "shipped" not in out and "resume with" not in out


def test_decoy_specs_dir_does_not_become_the_board_root(repo):
    """Mirrors the gate's root rule: specs/ alone is not an SDLC repo."""
    repo.write_feature(phase="implement", spec=True, plan=True)
    decoy = repo / "api"
    (decoy / "specs").mkdir(parents=True)
    code, out = run_hook("session_state.py", {"cwd": str(decoy)})
    assert code == 0 and "001-x" in out


def test_survives_ascii_only_stdout(repo):
    """The board lines contain an em-dash; an ascii console must not kill the hook."""
    repo.write_feature(phase="implement", spec=True, plan=True)
    proc = subprocess.run(
        [sys.executable, str(HOOKS / "session_state.py")],
        input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
        encoding="ascii", errors="replace", timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "ascii"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "001-x" in proc.stdout and "/sdlc:implement" in proc.stdout
