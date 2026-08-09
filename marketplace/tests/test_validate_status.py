import json

from conftest import make_status, run_hook


def payload(repo, path="specs/001-x/status.json"):
    return {"cwd": str(repo), "tool_name": "Write",
            "tool_input": {"file_path": str(repo / path)}}


def write(repo, doc):
    fdir = repo / "specs" / "001-x"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "status.json").write_text(json.dumps(doc), encoding="utf-8")


def test_valid_status_passes(repo):
    write(repo, make_status(phase="implement", spec=True, plan=True,
                            track="full", tasks={"done": 2, "total": 5}))
    assert run_hook("validate_status.py", payload(repo))[0] == 0


def test_non_status_files_ignored(repo):
    assert run_hook("validate_status.py", payload(repo, "src/app.py"))[0] == 0


def test_bad_phase_rejected(repo):
    doc = make_status()
    doc["phase"] = "vibing"
    write(repo, doc)
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "phase" in out


def test_missing_gate_rejected(repo):
    doc = make_status()
    del doc["gates"]["plan_approved"]
    write(repo, doc)
    assert run_hook("validate_status.py", payload(repo))[0] == 2


def test_approved_without_timestamp_rejected(repo):
    doc = make_status()
    doc["gates"]["spec_approved"] = {"approved": True, "by": "x", "at": None}
    write(repo, doc)
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "timestamp" in out


def test_bad_tasks_rejected(repo):
    write(repo, make_status(tasks={"done": 9, "total": 5}))
    assert run_hook("validate_status.py", payload(repo))[0] == 2


def test_invalid_json_rejected(repo):
    fdir = repo / "specs" / "001-x"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "status.json").write_text("{broken", encoding="utf-8")
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "JSON" in out


def test_bad_track_rejected(repo):
    write(repo, make_status(track="turbo"))
    assert run_hook("validate_status.py", payload(repo))[0] == 2
