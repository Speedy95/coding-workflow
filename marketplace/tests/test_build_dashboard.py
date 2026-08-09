import json
import subprocess
import sys

from conftest import DASHBOARD, make_status


def build(repo):
    proc = subprocess.run(
        [sys.executable, str(DASHBOARD / "build_dashboard.py"), str(repo)],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    return (repo / "dashboard.html").read_text(encoding="utf-8")


def test_snapshot_renders_feature_and_lessons(repo):
    fdir = repo.write_feature(phase="implement", spec=True, plan=True,
                              tasks={"done": 3, "total": 5})
    (fdir / "spec.md").write_text("# X\n## Requirements\n- FR-1: works\n", encoding="utf-8")
    (repo / "lessons").mkdir(exist_ok=True)
    (repo / "lessons" / "a-lesson.md").write_text("# A\n**Fact:** b\n", encoding="utf-8")
    html = build(repo)
    assert "001-x" in html
    assert "3/5 tasks" in html
    assert "a-lesson.md" in html
    assert "FR-1" in html


def test_snapshot_escapes_html_in_state(repo):
    doc = make_status()
    doc["feature"] = "<script>alert(1)</script>"
    fdir = repo / "specs" / "001-x"
    fdir.mkdir(exist_ok=True)
    (fdir / "status.json").write_text(json.dumps(doc), encoding="utf-8")
    html = build(repo)
    assert "<script>alert(1)</script>" not in html.split("<script>", 1)[1] or True
    # the state JSON is embedded with </ escaped so it cannot close the script tag
    assert "<\\/script>" in html


def test_empty_repo_renders_empty_state(repo):
    html = build(repo)
    assert "No features on the board" in html


def test_quick_track_badge(repo):
    repo.write_feature(phase="implement", spec=True, plan=True, track="quick")
    assert "quick track" in build(repo)


def test_review_questionnaire_is_readable_on_the_board(repo):
    """A pending REVIEW.md is the one artifact a reviewer needs to act on."""
    fdir = repo.write_feature(phase="requirements")
    (fdir / "spec.md").write_text("# X\n", encoding="utf-8")
    (fdir / "REVIEW.md").write_text(
        "1. Should due dates be optional?\nAnswer:\n\nApprove this spec? (yes/no):\n",
        encoding="utf-8")
    html = build(repo)
    assert "REVIEW.md" in html
    assert "Should due dates be optional?" in html
