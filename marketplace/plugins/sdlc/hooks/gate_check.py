"""SDLC gate: block ungated code changes.

PreToolUse hook for Edit|Write|NotebookEdit|Bash|PowerShell. Reads the hook
payload from stdin. Exit 0 = allow, exit 2 = block (stderr goes to the model).

Enforcement model:
- The SDLC root is derived from the TARGET PATH being written (walking up for
  a specs/ dir), falling back to the session cwd — so the gate holds no matter
  where the session is rooted.
- Code changes are allowed only while some feature is in an approved
  implement/verify phase. When every approved feature's plan.md has a
  parseable "## Affected files" section — or, for quick-track features
  without a plan.md, the spec's mini-plan has an "Affected files:" line —
  edits are additionally scoped to those files/directories (exact file, same
  directory, or listed directory prefix) — enforcing the plan-first scope
  discipline deterministically.
- Bash/PowerShell commands are screened with conservative write-pattern
  heuristics (redirects, tee, sed -i, Out-File/Set-Content). This cannot catch
  every write (e.g. inline python) — a documented residual gap.
- Fail-open philosophy: on any parse/resolve error the gate allows; it must
  never break unrelated work. specs/, lessons/, docs/, .claude/ and README
  are always writable.
"""

import json
import posixpath
import re
import sys
from pathlib import Path

ALWAYS_ALLOWED_TOP = {"specs", "lessons", "docs", ".claude"}

REDIRECT_RE = re.compile(r"(?:^|[^->\d])>{1,2}\s*([^\s;|&)]+)")
TEE_RE = re.compile(r"\btee\b(?:\s+-\w+)*\s+([^\s;|&]+)")
SED_I_RE = re.compile(r"\bsed\b[^;|&]*?-i\S*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s;|&]+)")
PS_WRITE_RE = re.compile(
    r"\b(?:Out-File|Set-Content|Add-Content)\b(?:\s+-(?!Path)\w+(?:\s+\S+)?)*"
    r"\s+(?:-Path\s+)?[\"']?([^\s\"';|&]+)", re.IGNORECASE)


def find_root(*starts) -> Path | None:
    for start in starts:
        if not start:
            continue
        try:
            p = Path(start).resolve()
        except OSError:
            continue
        for candidate in [p, *p.parents]:
            if (candidate / "specs").is_dir():
                return candidate
    return None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def gate_state(root: Path):
    """Return (has_features, approved_feature_dirs)."""
    status_files = list((root / "specs").glob("*/status.json"))
    approved = []
    for sf in status_files:
        st = load_json(sf)
        if not isinstance(st, dict):
            continue
        plan_ok = ((st.get("gates") or {}).get("plan_approved") or {}).get("approved") is True
        if st.get("phase") in ("implement", "verify") and plan_ok:
            approved.append(sf.parent)
    return bool(status_files), approved


def affected_entries(plan_path: Path) -> list[str]:
    """Path entries (posix, backtick-quoted) from the '## Affected files' section."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return []
    match = re.search(r"^## Affected files\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return []
    return _backtick_paths(match.group(1))


def mini_plan_entries(spec_path: Path) -> list[str]:
    """Quick-track fallback: paths from an 'Affected files:' line in spec.md."""
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []
    match = re.search(r"^Affected files:([^\n]*)$", text, re.M)
    if not match:
        return []
    return _backtick_paths(match.group(1))


def _backtick_paths(segment: str) -> list[str]:
    entries = re.findall(r"`([^`\n]+)`", segment)
    return [e.strip().replace("\\", "/").lstrip("./") for e in entries if e.strip()]


def rel_is_in_scope(rel: str, entries: list[str]) -> bool:
    rel = rel.replace("\\", "/")
    dirs = set()
    for entry in entries:
        entry = entry.rstrip("/")
        if rel == entry:
            return True
        if "." not in posixpath.basename(entry) and rel.startswith(entry + "/"):
            return True  # entry is a directory prefix
        dirs.add(posixpath.dirname(entry))
    return posixpath.dirname(rel) in dirs


BLOCK_NO_APPROVAL = (
    "SDLC gate: code change blocked - no feature is in an approved implement/verify "
    "phase. The spec and plan must be reviewed and explicitly approved by the user in "
    "conversation first (per the sdlc-state skill). Edits under specs/, lessons/, "
    "docs/ and .claude/ are always allowed. Do not bypass this by editing "
    "status.json - if the gate seems wrong, tell the user."
)
BLOCK_OUT_OF_SCOPE = (
    "SDLC gate: '{rel}' is not named in any approved plan's '## Affected files' "
    "section (quick track: the spec mini-plan's 'Affected files:' line). Scope "
    "discipline: add the file + reason there first, then make the edit. If this "
    "file genuinely belongs to the work, that update is one Edit away."
)


def check_target(target: Path, cwd: str) -> str | None:
    """Return a block message for this write target, or None to allow."""
    if not target.is_absolute():
        target = Path(cwd) / target
    root = find_root(target.parent, cwd)
    if root is None:
        return None
    try:
        rel = target.resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return None
    top = rel.split("/", 1)[0]
    if top in ALWAYS_ALLOWED_TOP or (("/" not in rel) and rel.upper().startswith("README")):
        return None
    has_features, approved = gate_state(root)
    if not has_features:
        return None
    if not approved:
        return BLOCK_NO_APPROVAL
    all_entries, parseable = [], True
    for feature_dir in approved:
        entries = affected_entries(feature_dir / "plan.md")
        if not entries:
            entries = mini_plan_entries(feature_dir / "spec.md")
        if not entries:
            parseable = False
        all_entries.extend(entries)
    if not parseable:
        return None  # fail open when any approved plan lacks a parseable section
    if rel_is_in_scope(rel, all_entries):
        return None
    return BLOCK_OUT_OF_SCOPE.format(rel=rel)


def _unquote_simple(match: re.Match) -> str:
    """Keep quoted single-path tokens; blank out quoted code/multi-word strings."""
    inner = match.group(0)[1:-1]
    return inner if re.fullmatch(r"[^\s;|&<>]*", inner) else " "


def command_targets(command: str) -> list[str]:
    sanitized = re.sub(r"'[^']*'|\"[^\"]*\"", _unquote_simple, command)
    targets = []
    for regex in (REDIRECT_RE, TEE_RE, SED_I_RE, PS_WRITE_RE):
        targets.extend(m.strip("\"'") for m in regex.findall(sanitized))
    junk = {"/dev/null", "nul", "NUL", "$null", "&1", "&2"}
    return [t for t in targets if t and t not in junk and not t.startswith("&")]


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or "."

    if tool_name in ("Bash", "PowerShell"):
        command = tool_input.get("command") or ""
        for raw in command_targets(command):
            message = check_target(Path(raw), cwd)
            if message:
                print(message, file=sys.stderr)
                sys.exit(2)
        sys.exit(0)

    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        sys.exit(0)
    message = check_target(Path(file_path), cwd)
    if message:
        print(message, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
