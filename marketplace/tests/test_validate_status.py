import json

from conftest import HOOKS, load_hook_module, make_status, run_hook

SCHEMA = json.loads((HOOKS.parent / "schema" / "status.schema.json").read_text(encoding="utf-8"))


def payload(repo, path="specs/001-x/status.json"):
    return {"cwd": str(repo), "tool_name": "Write",
            "tool_input": {"file_path": str(repo / path)}}


def write(repo, doc, slug="001-x"):
    fdir = repo / "specs" / slug
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


# ── invariants, not just shape (audit P0 item 8) ────────────────────────────

def test_implement_without_plan_approval_rejected(repo):
    """The exact state the edit gate keys on: claiming implement without the gate."""
    write(repo, make_status(phase="implement", spec=True, plan=False))
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "plan_approved" in out


def test_verify_and_document_also_require_plan_approval(repo):
    for phase in ("verify", "document"):
        write(repo, make_status(phase=phase, spec=True, plan=False))
        code, out = run_hook("validate_status.py", payload(repo))
        assert code == 2 and "plan_approved" in out, phase


def test_done_without_docs_complete_rejected(repo):
    write(repo, make_status(phase="done", spec=True, plan=True))
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "docs_complete" in out


def test_slug_must_match_the_directory_name(repo):
    doc = make_status()
    doc["slug"] = "002-elsewhere"
    write(repo, doc)
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "directory" in out


def test_slug_must_match_the_schema_pattern(repo):
    doc = make_status()
    doc["slug"] = "not_a_slug"
    write(repo, doc, slug="not_a_slug")
    code, out = run_hook("validate_status.py",
                         payload(repo, "specs/not_a_slug/status.json"))
    assert code == 2 and "slug" in out


def test_unparseable_updated_at_rejected(repo):
    doc = make_status()
    doc["updatedAt"] = "yesterday"
    write(repo, doc)
    code, out = run_hook("validate_status.py", payload(repo))
    assert code == 2 and "updatedAt" in out


def test_iso_timestamp_forms_accepted(repo):
    for stamp in ("2026-08-01T00:00:00Z", "2026-08-01T00:00:00+00:00", "2026-08-01"):
        doc = make_status(phase="implement", spec=True, plan=True)
        doc["updatedAt"] = stamp
        write(repo, doc)
        assert run_hook("validate_status.py", payload(repo))[0] == 0, stamp


def test_archived_status_files_are_left_alone(repo):
    """Archived state is frozen history — validating it would re-flag old formats."""
    doc = make_status(phase="implement", spec=True, plan=False)
    fdir = repo / "specs" / "archive" / "001-x"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "status.json").write_text(json.dumps(doc), encoding="utf-8")
    assert run_hook("validate_status.py",
                    payload(repo, "specs/archive/001-x/status.json"))[0] == 0


# ── the schema file is load-bearing, not decoration ─────────────────────────

def test_hook_constants_come_from_the_schema():
    mod = load_hook_module("validate_status")
    assert mod.PHASES == set(SCHEMA["properties"]["phase"]["enum"])
    assert mod.TRACKS == set(SCHEMA["properties"]["track"]["enum"])
    assert mod.GATE_KEYS == set(SCHEMA["properties"]["gates"]["required"])
    assert mod.SLUG_RE.pattern == SCHEMA["properties"]["slug"]["pattern"]


def test_hardcoded_fallbacks_match_the_schema():
    """Guards the drift the audit found between the schema and its hook mirror."""
    mod = load_hook_module("validate_status")
    assert mod.FALLBACK["phases"] == set(SCHEMA["properties"]["phase"]["enum"])
    assert mod.FALLBACK["tracks"] == set(SCHEMA["properties"]["track"]["enum"])
    assert mod.FALLBACK["gate_keys"] == set(SCHEMA["properties"]["gates"]["required"])
    assert mod.FALLBACK["slug_pattern"] == SCHEMA["properties"]["slug"]["pattern"]


def test_unreadable_schema_falls_back(tmp_path):
    mod = load_hook_module("validate_status")
    assert mod.load_constants(tmp_path / "missing.json") == mod.FALLBACK


def test_malformed_schema_falls_back(tmp_path):
    mod = load_hook_module("validate_status")
    broken = tmp_path / "broken.json"
    broken.write_text('{"properties": {}}', encoding="utf-8")
    assert mod.load_constants(broken) == mod.FALLBACK


def test_hooks_json_validates_every_write_tool():
    hooks = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
    matchers = [entry["matcher"] for entry in hooks["hooks"]["PostToolUse"]]
    assert "Edit|Write|NotebookEdit" in matchers
