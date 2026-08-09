"""PostToolUse hook (Write|Edit): validate specs/*/status.json after writes.

Exit 0 when the write wasn't a status.json or the file is valid; exit 2 with
the error list on stderr so the model immediately fixes the state file.
Stdlib-only mirror of schema/status.schema.json.
"""

import json
import re
import sys
from pathlib import Path

PHASES = {"requirements", "plan", "implement", "verify", "document", "done"}
GATE_KEYS = {"spec_approved", "plan_approved", "verification_passed", "docs_complete"}
TRACKS = {"quick", "full"}
STATUS_RE = re.compile(r"specs[\\/][^\\/]+[\\/]status\.json$")


def validate(doc) -> list[str]:
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
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
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
    errors = validate(doc)
    if errors:
        print("SDLC state error in " + str(target) + ":\n- " + "\n- ".join(errors)
              + "\nFix status.json to match schema/status.schema.json (see sdlc-state skill).",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
