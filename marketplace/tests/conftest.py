import json
import os
import re
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


def plan_with(*entries: str) -> str:
    """A plan.md whose '## Affected files' section lists exactly `entries`."""
    body = "\n".join(f"- `{entry}` — reason" for entry in entries)
    return f"# Plan: x\n\n## Approach\nStuff.\n\n## Affected files\n{body}\n\n## Tasks\n- [ ] 1. do it\n"


def as_shell_path(path) -> str:
    """An absolute path spelled the way a shell on this OS hands it to the hook.

    The Bash tool on Windows is Git Bash, where `C:\\repo` is written `/c/repo` —
    the POSIX drive form the gate has to rewrite before it can resolve a target.
    """
    text = str(path).replace("\\", "/")
    if os.name == "nt" and re.match(r"^[A-Za-z]:/", text):
        return "/" + text[0].lower() + text[2:]
    return text


def load_hook_module(name: str):
    """Import a hook script in-process (they are import-safe: main() is guarded)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"sdlc_hook_{name}", HOOKS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
                      plan_md=PLAN_WITH_SCOPE, spec_md=None, slug="001-x", **kw):
        fdir = self.path / "specs" / slug
        fdir.mkdir(parents=True, exist_ok=True)
        doc = make_status(phase, spec, plan, **kw)
        doc["slug"] = slug
        (fdir / "status.json").write_text(json.dumps(doc), encoding="utf-8")
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
