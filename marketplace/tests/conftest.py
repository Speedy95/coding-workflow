import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "sdlc" / "hooks"
DASHBOARD = Path(__file__).resolve().parents[1] / "plugins" / "sdlc" / "dashboard"

PLAN_WITH_SCOPE = """# Plan: x

## Approach
Stuff.

## Affected files
- `taskler.py` — main change
- `tests/test_taskler.py` — tests

## Tasks
- [ ] 1. do it
"""

PLAN_WITHOUT_SCOPE = "# Plan: x\n\nJust vibes, no affected files section.\n"

SPEC_WITH_MINI_PLAN = """# Fix: x

## Problem
Small thing.

## Mini-plan (track: quick)
Approach: tweak it.
Tasks:
1. test
2. fix
Affected files: `taskler.py`, `tests/test_taskler.py`
"""

SPEC_WITHOUT_MINI_PLAN = "# Fix: x\n\n## Problem\nNo mini-plan here.\n"


def run_hook(script: str, payload: dict):
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=30,
    )
    return proc.returncode, proc.stderr + proc.stdout


def make_status(phase="requirements", spec=False, plan=False, track=None, tasks=None):
    def gate(ok):
        return {"approved": ok, "by": "tester" if ok else None,
                "at": "2026-08-01T00:00:00Z" if ok else None}
    doc = {
        "schemaVersion": 1, "feature": "X", "slug": "001-x", "phase": phase,
        "gates": {"spec_approved": gate(spec), "plan_approved": gate(plan),
                  "verification_passed": gate(False), "docs_complete": gate(False)},
        "updatedAt": "2026-08-01T00:00:00Z",
    }
    if track:
        doc["track"] = track
    if tasks:
        doc["tasks"] = tasks
    return doc


class SdlcRepo:
    """Path-like SDLC repo skeleton with a write_feature() helper."""

    def __init__(self, path: Path):
        self.path = path

    def __truediv__(self, other):
        return self.path / other

    def __str__(self):
        return str(self.path)

    def __fspath__(self):
        return str(self.path)

    def write_feature(self, phase="requirements", spec=False, plan=False,
                      plan_md=PLAN_WITH_SCOPE, spec_md=None, **kw):
        fdir = self.path / "specs" / "001-x"
        fdir.mkdir(exist_ok=True)
        (fdir / "status.json").write_text(
            json.dumps(make_status(phase, spec, plan, **kw)), encoding="utf-8")
        if plan_md is not None:
            (fdir / "plan.md").write_text(plan_md, encoding="utf-8")
        if spec_md is not None:
            (fdir / "spec.md").write_text(spec_md, encoding="utf-8")
        return fdir


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    return SdlcRepo(tmp_path)
