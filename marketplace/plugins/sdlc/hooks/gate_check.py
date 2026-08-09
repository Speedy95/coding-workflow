"""SDLC gate: block ungated code changes.

PreToolUse hook for Edit|Write|NotebookEdit|Bash|PowerShell. Reads the hook
payload from stdin. Exit 0 = allow, exit 2 = block (stderr goes to the model).

Enforcement model:
- The SDLC root is derived from the TARGET PATH being written (walking up for a
  QUALIFYING specs/ dir — one holding metrics.jsonl or */status.json, so an
  unrelated api/specs/ folder cannot shadow the real root), falling back to the
  session cwd — so the gate holds no matter where the session is rooted.
- Code changes are allowed only while some feature is in an approved
  implement/verify phase; a document-phase feature unlocks only doc files
  (.md/.rst/.txt) within its scope — code is frozen once verified. Edits are
  additionally scoped to the approved plans' "## Affected files" entries — or,
  for quick-track features without a plan.md, the spec mini-plan's
  "Affected files:" line. Scope is the union across approved features that
  declare one; a feature that declares none contributes nothing (the gate only
  fails open when NO approved feature declares a scope).
- Bash/PowerShell commands are screened for writes (redirects, tee, sed -i,
  Out-File/Set-Content) AND for destructive operations (rm, mv, cp, truncate,
  dd, git checkout/restore, curl -o, Remove-Item/Move-Item/Copy-Item).
  Commands whose targets cannot be enumerated at all (git apply, patch) are
  refused inside a gated repo.
- Fail-open philosophy: on any parse/resolve error the gate allows; it must
  never break unrelated work. specs/, lessons/, docs/, .claude/ and root-level
  README*/CHANGELOG* are always writable.

Documented residual gaps: writes hidden inside quoted inline code (e.g.
`python -c "..."`); `cd dir && ...` compounds (relative targets are judged
against the payload cwd, not the cd'd directory); Bash-driven status.json
writes are not validated by the PostToolUse hook.
"""

import json
import os
import posixpath
import re
import sys
from pathlib import Path

ALWAYS_ALLOWED_TOP = {"specs", "lessons", "docs", ".claude"}
ALWAYS_ALLOWED_ROOT_PREFIXES = ("README", "CHANGELOG")
# Scratch output a gated run legitimately produces (test logs, captured stdout).
SCRATCH_EXTENSIONS = {".log", ".txt", ".out", ".tmp"}
# What the document phase may still touch inside its scope (code is frozen).
DOC_EXTENSIONS = {".md", ".rst", ".txt"}

# `[^->]` still rejects the `->` arrow and a second `>`; digits are allowed
# through so that `1> file` and `2> file` are screened like a bare `> file`.
REDIRECT_RE = re.compile(r"(?:^|[^->])>{1,2}\s*([^\s;|&)]+)")
# tee and sed -i write EVERY following file argument, so capture the whole tail
# of the segment and split it later (a single-token capture missed the rest).
TEE_RE = re.compile(r"\btee\b((?:\s+[^\s;|&]+)+)")
SED_I_RE = re.compile(r"\bsed\b[^;|&]*?-i\S*\s+(?:'[^']*'|\"[^\"]*\"|\S+)((?:\s+[^\s;|&]+)+)")
# The target flag may be spelled -Path, -LiteralPath or -FilePath; any other
# flag's value must not swallow a following flag (hence the (?!-) guard).
PS_WRITE_RE = re.compile(
    r"\b(?:Out-File|Set-Content|Add-Content)\b"
    r"(?:\s+-(?!Path\b|LiteralPath\b|FilePath\b)\w+(?:\s+(?!-)[^\s;|&]+)?)*"
    r"\s+(?:-(?:Path|LiteralPath|FilePath)\s+)?[\"']?([^\s\"';|&]+)", re.IGNORECASE)

SEGMENT_RE = re.compile(r"[;&|\n]+")
COMMAND_PREFIXES = {"sudo", "command", "env", "time", "nohup", "exec", "&&"}
PS_PATH_FLAGS = {"-path", "-literalpath", "-destination", "-outfile", "-filepath"}

WRITE, DESTROY = "write", "destroy"


# ── root discovery ──────────────────────────────────────────────────────────

def is_sdlc_root(candidate: Path) -> bool:
    """True when candidate/specs is a real SDLC board, not just a specs/ folder.

    Twin of the identical check in session_state.py — hooks cannot share a
    module (no package on sys.path), so keep the two definitions in sync.
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


def find_root(*starts) -> Path | None:
    for start in starts:
        if not start:
            continue
        try:
            p = Path(start).resolve()
        except OSError:
            continue
        for candidate in [p, *p.parents]:
            if is_sdlc_root(candidate):
                return candidate
    return None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def gate_state(root: Path):
    """Return (has_features, approved_feature_dirs, documenting_feature_dirs).

    Code unlocks only during implement/verify. A document-phase feature is
    tracked separately: once verification_passed, shipped code must equal
    verified code, so document only unlocks DOC files within its scope.
    """
    status_files = list((root / "specs").glob("*/status.json"))
    approved, documenting = [], []
    for sf in status_files:
        st = load_json(sf)
        if not isinstance(st, dict):
            continue
        plan_ok = ((st.get("gates") or {}).get("plan_approved") or {}).get("approved") is True
        if not plan_ok:
            continue
        if st.get("phase") in ("implement", "verify"):
            approved.append(sf.parent)
        elif st.get("phase") == "document":
            documenting.append(sf.parent)
    return bool(status_files), approved, documenting


# ── plan scope ──────────────────────────────────────────────────────────────

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
    entries = []
    for raw in re.findall(r"`([^`\n]+)`", segment):
        entry = raw.strip().replace("\\", "/")
        if entry.startswith("./"):
            entry = entry[2:]
        # A traversing entry cannot describe a path inside the repo; dropping it
        # is safer than normalizing it into some other in-repo path.
        if not entry or ".." in entry.split("/"):
            continue
        entries.append(entry)
    return entries


def rel_is_in_scope(rel: str, entries: list[str]) -> bool:
    rel = rel.replace("\\", "/")
    dirs = set()
    for entry in entries:
        # A trailing slash always means "directory"; the no-dot heuristic is the
        # fallback for legacy entries written without one (it misreads src/v1.2).
        is_dir = entry.endswith("/") or "." not in posixpath.basename(entry.rstrip("/"))
        entry = entry.rstrip("/")
        if not entry:
            continue
        if rel == entry:
            return True
        if is_dir and rel.startswith(entry + "/"):
            return True
        if not is_dir:
            parent = posixpath.dirname(entry)
            if parent:  # a root-level entry must not unlock the whole repo root
                dirs.add(parent)
    return posixpath.dirname(rel) in dirs


# ── verdicts ────────────────────────────────────────────────────────────────

BLOCK_NO_APPROVAL = (
    "SDLC gate: code change blocked - no feature is in an approved implement/verify "
    "phase. (A document-phase feature unlocks only doc files - .md/.rst/.txt - within "
    "its scope; code is frozen once verified.) The spec and plan must be reviewed and "
    "explicitly approved by the user in conversation first (per the sdlc-state skill). "
    "Edits under specs/, lessons/, docs/ and .claude/ are always allowed. Do not "
    "bypass this by editing status.json - if the gate seems wrong, tell the user."
)
BLOCK_OUT_OF_SCOPE = (
    "SDLC gate: '{rel}' is not named in any approved plan's '## Affected files' "
    "section (quick track: the spec mini-plan's 'Affected files:' line). Scope "
    "discipline: add the file + reason there first, then make the edit. If this "
    "file genuinely belongs to the work, that update is one Edit away."
)
BLOCK_OPAQUE = (
    "SDLC gate: '{verb}' cannot be scope-checked - the gate cannot tell which files it "
    "writes, so it cannot confirm they are in an approved plan's scope. Use Edit/Write "
    "for files inside this repo (they are gated per file), or run this outside the "
    "SDLC repo."
)


def check_target(target: Path, cwd: str, scratch_ok: bool = False) -> str | None:
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
    if top in ALWAYS_ALLOWED_TOP:
        return None
    if "/" not in rel and rel.upper().startswith(ALWAYS_ALLOWED_ROOT_PREFIXES):
        return None
    has_features, approved, documenting = gate_state(root)
    if not has_features:
        return None
    ext = posixpath.splitext(rel)[1].lower()
    # Document phase: the retro's own DOC work, scoped to the feature — code
    # stays frozen once verified (shipped must equal verified).
    if documenting and ext in DOC_EXTENSIONS:
        entries, any_parseable = _scope_union(documenting)
        if not any_parseable or rel_is_in_scope(rel, entries):
            return None
    if not approved:
        return BLOCK_NO_APPROVAL
    # Redirected scratch output (test logs, captured stdout) is not a code
    # change — but the exemption applies only once something is approved;
    # before that, every enumerable write stays gated.
    if scratch_ok and ext in SCRATCH_EXTENSIONS:
        return None
    entries, any_parseable = _scope_union(approved)
    if not any_parseable:
        return None  # fail open only when NO approved feature declares a scope
    if rel_is_in_scope(rel, entries):
        return None
    return BLOCK_OUT_OF_SCOPE.format(rel=rel)


def _scope_union(feature_dirs) -> tuple[list[str], bool]:
    all_entries, any_parseable = [], False
    for feature_dir in feature_dirs:
        entries = affected_entries(feature_dir / "plan.md")
        if not entries:
            entries = mini_plan_entries(feature_dir / "spec.md")
        if entries:
            any_parseable = True
            all_entries.extend(entries)
    return all_entries, any_parseable


def check_opaque(cwd: str) -> bool:
    """True when an unenumerable write should be refused (a gated repo is in play)."""
    root = find_root(cwd)
    return root is not None and gate_state(root)[0]


# ── command screening ───────────────────────────────────────────────────────

# Marks a space inside a quoted path so it survives whitespace tokenization;
# restored in command_targets before the path is resolved.
QUOTED_SPACE = "\x00"


def _unquote_simple(match: re.Match) -> str:
    """Keep quoted path-like tokens (spaces sentinel-preserved); blank quoted code."""
    inner = match.group(0)[1:-1]
    if re.fullmatch(r"[^;|&<>]*", inner):
        return inner.replace(" ", QUOTED_SPACE).replace("\t", QUOTED_SPACE)
    return " "


def _restore_spaces(token: str) -> str:
    return token.replace(QUOTED_SPACE, " ")


def _positionals(args: list[str], value_flags=frozenset()) -> list[str]:
    """Non-flag arguments, skipping the value that follows a value-taking flag."""
    out, skip = [], False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg.startswith("-"):
            if arg.lower() in value_flags:
                skip = True
            continue
        out.append(arg)
    return out


def _flag_values(args: list[str], flags) -> list[str]:
    out = []
    for i, arg in enumerate(args):
        name = arg.lower().split("=", 1)[0]
        if name not in flags:
            continue
        if "=" in arg:
            out.append(arg.split("=", 1)[1])
        elif i + 1 < len(args):
            out.append(args[i + 1])
    return out


def segment_targets(segment: str, cwd: str = ".") -> list[tuple[str, str]]:
    """(target, kind) pairs written or destroyed by one command segment."""
    targets = []
    for regex in (REDIRECT_RE, PS_WRITE_RE):
        targets.extend((m, WRITE) for m in regex.findall(segment))
    for regex in (TEE_RE, SED_I_RE):
        for blob in regex.findall(segment):
            targets.extend((t, WRITE) for t in blob.split() if not t.startswith("-"))

    tokens = segment.split()
    for i, token in enumerate(tokens):
        verb = token.rsplit("/", 1)[-1].lower()
        args = tokens[i + 1:]
        if verb == "rm":
            targets.extend((t, DESTROY) for t in _positionals(args))
        elif verb == "truncate":
            targets.extend((t, DESTROY) for t in
                           _positionals(args, {"-s", "--size", "-r", "--reference"}))
        elif verb == "dd":
            targets.extend((a.split("=", 1)[1], DESTROY)
                           for a in args if a.lower().startswith("of="))
        elif verb == "mv":
            # every positional is either a destroyed source or the destination
            targets.extend((t, DESTROY) for t in _positionals(args, {"-t", "--target-directory"}))
            targets.extend((t, DESTROY) for t in _flag_values(args, {"-t", "--target-directory"}))
        elif verb == "cp":
            positional = _positionals(args, {"-t", "--target-directory"})
            targets.extend((t, WRITE) for t in positional[-1:])
            targets.extend((t, WRITE) for t in _flag_values(args, {"-t", "--target-directory"}))
        elif verb == "curl":
            targets.extend((t, WRITE) for t in _flag_values(args, {"-o", "--output"}))
        elif verb == "git":
            targets.extend(_git_targets(args, cwd))
        elif verb in ("remove-item", "move-item"):
            targets.extend((t, DESTROY) for t in _positionals(args, PS_PATH_FLAGS))
            targets.extend((t, DESTROY) for t in _flag_values(args, PS_PATH_FLAGS))
        elif verb == "copy-item":
            positional = _positionals(args, PS_PATH_FLAGS)
            targets.extend((t, WRITE) for t in positional[-1:])
            targets.extend((t, WRITE) for t in _flag_values(args, {"-destination"}))
        elif verb in ("invoke-webrequest", "invoke-restmethod"):
            targets.extend((t, WRITE) for t in _flag_values(args, {"-outfile"}))
    return targets


# Global git flags that take a separate value (git -C dir checkout ...) —
# their value must not be mistaken for the subcommand.
GIT_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def _git_targets(args: list[str], cwd: str = ".") -> list[tuple[str, str]]:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GIT_VALUE_FLAGS else 1
    if i >= len(args):
        return []
    subcommand, rest = args[i], args[i + 1:]
    if subcommand not in ("checkout", "restore"):
        return []
    if "--" in rest:
        paths = _positionals(rest[rest.index("--") + 1:])
    elif subcommand == "restore":
        paths = _positionals(rest, {"--source", "-s"})
    else:
        # git DWIMs `checkout <arg>` into a file revert when <arg> is not a
        # ref. Approximate that here: screen args that exist as paths
        # (branch names almost never name an existing file).
        candidates = _positionals(rest, {"-b", "-B", "--orphan"})
        paths = [p for p in candidates
                 if Path(cwd, _restore_spaces(p)).exists()]
    return [(p, DESTROY) for p in paths]


def opaque_verb(segment: str) -> str | None:
    """Name the command in this segment whose write targets cannot be enumerated."""
    tokens = segment.split()
    for i, token in enumerate(tokens):
        verb = token.rsplit("/", 1)[-1].lower()
        args = tokens[i + 1:]
        if verb == "git" and next((a for a in args if not a.startswith("-")), "") == "apply":
            return "git apply"
        if verb == "patch" and ("-i" in args or "<" in segment):
            return "patch"
    return None


def _segments(command: str) -> list[str]:
    sanitized = re.sub(r"'[^']*'|\"[^\"]*\"", _unquote_simple, command)
    sanitized = sanitized.replace(">|", ">")  # noclobber override is a plain redirect
    return SEGMENT_RE.split(sanitized)


def command_targets(command: str, cwd: str = ".") -> list[tuple[str, str]]:
    junk = {"/dev/null", "nul", "NUL", "$null", "&1", "&2"}
    targets = []
    for segment in _segments(command):
        for raw, kind in segment_targets(segment, cwd):
            target = _restore_spaces(raw.strip("\"'"))
            if target and target not in junk and not target.startswith("&"):
                targets.append((target, kind))
    return targets


def resolve_shell_path(raw: str) -> str:
    """Rewrite Git Bash's /c/Users/... into C:/Users/... before resolving."""
    if os.name == "nt":
        match = re.match(r"^/([A-Za-z])/(.*)$", raw)
        if match:
            return f"{match.group(1)}:/{match.group(2)}"
    return raw


# ── entry point ─────────────────────────────────────────────────────────────

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
        for raw, kind in command_targets(command, cwd):
            message = check_target(Path(resolve_shell_path(raw)), cwd, scratch_ok=(kind == WRITE))
            if message:
                print(message, file=sys.stderr)
                sys.exit(2)
        for segment in _segments(command):
            verb = opaque_verb(segment)
            if verb and check_opaque(cwd):
                print(BLOCK_OPAQUE.format(verb=verb), file=sys.stderr)
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
