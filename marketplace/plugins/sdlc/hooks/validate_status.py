"""PostToolUse hook (Write|Edit|NotebookEdit): validate specs/*/status.json.

Exit 0 when the write wasn't a status.json or the file is valid; exit 2 with
the error list on stderr so the model immediately fixes the state file.

Checks shape AND the invariants the rest of the workflow keys on: a phase that
claims implement/verify/document must carry an approved plan gate (that is the
exact state the edit gate reads), done must carry docs_complete, the slug must
match both the schema pattern and its own directory, and updatedAt must be a
real timestamp rather than prose.

schema/status.schema.json is the authority for the phase enum, track enum, gate
names and slug pattern — this hook loads it at start-up. FALLBACK below is a
mirror used only when the schema cannot be read (fail-open); the test suite
asserts the two agree.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "status.schema.json"

FALLBACK = {
    "phases": {"requirements", "plan", "implement", "verify", "document", "done"},
    "tracks": {"quick", "full"},
    "gate_keys": {"spec_approved", "plan_approved", "verification_passed", "docs_complete"},
    "slug_pattern": r"^[0-9]{3}-[a-z0-9-]+$",
}


def load_constants(path: Path = SCHEMA_PATH) -> dict:
    try:
        properties = json.loads(path.read_text(encoding="utf-8"))["properties"]
        constants = {
            "phases": set(properties["phase"]["enum"]),
            "tracks": set(properties["track"]["enum"]),
            "gate_keys": set(properties["gates"]["required"]),
            "slug_pattern": properties["slug"]["pattern"],
        }
        if not all(constants.values()):
            raise ValueError("schema is missing values")
        return constants
    except (OSError, UnicodeDecodeError, json.JSONDecodeError,
            KeyError, TypeError, ValueError):
        return FALLBACK


_CONSTANTS = load_constants()
PHASES = _CONSTANTS["phases"]
TRACKS = _CONSTANTS["tracks"]
GATE_KEYS = _CONSTANTS["gate_keys"]
SLUG_RE = re.compile(_CONSTANTS["slug_pattern"])

PLAN_REQUIRED_PHASES = ("implement", "verify", "document")
# One path segment between specs/ and status.json, so specs/archive/<slug>/ is
# skipped on purpose: archived state is frozen history, not live state.
STATUS_RE = re.compile(r"specs[\\/][^\\/]+[\\/]status\.json$")


def _gate_approved(doc, name: str) -> bool:
    return ((doc.get("gates") or {}).get(name) or {}).get("approved") is True


def validate(doc, path: Path | None = None) -> list[str]:
    errors = []
    if not isinstance(doc, dict):
        return ["root must be an object"]
    if doc.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    for key in ("feature", "slug", "updatedAt"):
        if not isinstance(doc.get(key), str) or not doc.get(key):
            errors.append(f"{key} must be a non-empty string")
    if doc.get("phase") not in PHASES:
        errors.append(f"phase must be one of {sorted(PHASES)}")
    gates = doc.get("gates")
    if not isinstance(gates, dict) or set(gates) != GATE_KEYS:
        errors.append(f"gates must contain exactly {sorted(GATE_KEYS)}")
    else:
        for name, gate in gates.items():
            if not isinstance(gate, dict) or not isinstance(gate.get("approved"), bool):
                errors.append(f"gates.{name}.approved must be a bool")
                continue
            for field in ("by", "at"):
                if gate.get(field) is not None and not isinstance(gate.get(field), str):
                    errors.append(f"gates.{name}.{field} must be string or null")
            if gate["approved"] and not gate.get("at"):
                errors.append(f"gates.{name} approved without an 'at' timestamp")
        phase = doc.get("phase")
        if phase in PLAN_REQUIRED_PHASES and not _gate_approved(doc, "plan_approved"):
            errors.append(f"phase '{phase}' requires gates.plan_approved.approved = true "
                          "(the edit gate reads exactly this)")
        if phase == "done" and not _gate_approved(doc, "docs_complete"):
            errors.append("phase 'done' requires gates.docs_complete.approved = true")
    slug = doc.get("slug")
    if isinstance(slug, str) and slug:
        if not SLUG_RE.match(slug):
            errors.append(f"slug '{slug}' must match {SLUG_RE.pattern}")
        if path is not None and slug != path.parent.name:
            errors.append(f"slug '{slug}' must equal its directory name '{path.parent.name}'")
    updated = doc.get("updatedAt")
    if isinstance(updated, str) and updated:
        try:
            datetime.fromisoformat(updated[:-1] if updated.endswith("Z") else updated)
        except ValueError:
            errors.append(f"updatedAt '{updated}' must be an ISO-8601 UTC timestamp "
                          "(e.g. 2026-08-09T12:00:00Z)")
    if "track" in doc and doc["track"] not in TRACKS:
        errors.append(f"track must be one of {sorted(TRACKS)}")
    if "verifyAttempts" in doc and not (isinstance(doc["verifyAttempts"], int) and doc["verifyAttempts"] >= 0):
        errors.append("verifyAttempts must be a non-negative integer")
    if "tasks" in doc:
        tasks = doc["tasks"]
        if not (isinstance(tasks, dict)
                and isinstance(tasks.get("done"), int) and isinstance(tasks.get("total"), int)
                and 0 <= tasks["done"] <= tasks["total"]):
            errors.append("tasks must be {done: int, total: int} with 0 <= done <= total")
    return errors


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not STATUS_RE.search(file_path):
        sys.exit(0)
    target = Path(file_path)
    if not target.is_absolute():
        target = Path(payload.get("cwd") or ".") / target
    try:
        doc = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        sys.exit(0)  # deleted/unreadable is not this hook's problem
    except json.JSONDecodeError as exc:
        print(f"SDLC state error: {target.name} is not valid JSON ({exc}). Fix it now.", file=sys.stderr)
        sys.exit(2)
    errors = validate(doc, target)
    if errors:
        print("SDLC state error in " + str(target) + ":\n- " + "\n- ".join(errors)
              + "\nFix status.json to match schema/status.schema.json (see sdlc-state skill).",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
