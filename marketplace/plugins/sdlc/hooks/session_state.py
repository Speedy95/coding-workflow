"""SessionStart hook: inject the SDLC board state into new sessions.

Prints a compact summary to stdout (added to the session's context) when the
working directory is inside an SDLC-managed repo with at least one feature.
Silent (exit 0, no output) everywhere else — the hook must be invisible in
non-SDLC repos.
"""

import json
import sys
from pathlib import Path

PHASES = ["requirements", "plan", "implement", "verify", "document"]


def is_sdlc_root(candidate: Path) -> bool:
    """True when candidate/specs is a real SDLC board, not just a specs/ folder.

    Twin of the identical check in gate_check.py — hooks cannot share a module
    (no package on sys.path), so keep the two definitions in sync.
    """
    specs = candidate / "specs"
    try:
        if not specs.is_dir():
            return False
        if (specs / "metrics.jsonl").exists():
            return True
        return any(specs.glob("*/status.json"))
    except OSError:
        return False


def find_root(start: Path) -> Path | None:
    try:
        p = start.resolve()
    except OSError:
        return None
    for candidate in [p, *p.parents]:
        if is_sdlc_root(candidate):
            return candidate
    return None


def next_action(feature_dir: Path, st: dict) -> str:
    slug, phase = st.get("slug", "?"), st.get("phase", "?")
    review = " (REVIEW.md questionnaire present — check for answers)" \
        if (feature_dir / "REVIEW.md").exists() else ""
    if phase == "requirements":
        return (f"spec awaits the user's review/approval{review}"
                if (feature_dir / "spec.md").exists()
                else "spec drafting in progress (/sdlc:requirements)")
    if phase == "plan":
        return (f"plan awaits the user's review/approval{review}"
                if (feature_dir / "plan.md").exists()
                else f"run /sdlc:plan {slug}")
    if phase in ("implement", "verify", "document"):
        return f"resume with /sdlc:{phase} {slug}"
    # An unrecognised phase is a broken state file, not a shipped feature —
    # say so instead of quietly filing it under "shipped".
    return "unrecognised phase — check with /sdlc:status"


def main():
    # SessionStart output goes to whatever console the user has; an ascii-only
    # stdout must not turn the board into a UnicodeEncodeError traceback.
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError, ValueError):
        pass
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    root = find_root(Path(payload.get("cwd") or "."))
    if root is None:
        sys.exit(0)
    rows = []
    for status_file in sorted((root / "specs").glob("*/status.json")):
        try:
            st = json.loads(status_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        phase = st.get("phase", "?")
        tasks = st.get("tasks") if isinstance(st.get("tasks"), dict) else {}
        progress = f" {tasks.get('done', 0)}/{tasks['total']}" if tasks.get("total") else ""
        track = f" [{st['track']}]" if st.get("track") == "quick" else ""
        if phase == "done":
            rows.append(f"- {st.get('slug')}: shipped{track}")
        else:
            rows.append(f"- {st.get('slug')}: {phase}{progress}{track} — {next_action(status_file.parent, st)}")
    if not rows:
        sys.exit(0)
    in_flight = sum(1 for r in rows if "shipped" not in r)
    print(f"SDLC workflow state for {root.name} ({in_flight} in flight):")
    print("\n".join(rows))
    print("Gates are hook-enforced; load the sdlc:sdlc-state skill before touching "
          "workflow state. /sdlc:status for details, /sdlc:dashboard for the board.")
    sys.exit(0)


if __name__ == "__main__":
    main()
