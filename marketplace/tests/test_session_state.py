from conftest import run_hook


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
