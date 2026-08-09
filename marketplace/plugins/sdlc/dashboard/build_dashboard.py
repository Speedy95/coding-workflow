"""SDLC dashboard: overview board + artifact reader for one repo's specs/ state.

Stdlib only. Two modes from the same template:

    python build_dashboard.py [repo_root] [-o output.html]   # static snapshot
    python build_dashboard.py [repo_root] --serve [--port N] # live local board

Static mode embeds all state (including spec/plan/verification/lesson markdown)
into one self-contained dashboard.html — safe to open, commit, or publish via
CI. Serve mode starts a localhost-only stdlib http server that re-scans specs/
on every poll, so the board updates while agents move features.

Design: "signal box" strip board. Features are grouped by who is blocked
(needs review → in progress → shipped); each strip expands into a dossier with
the gate ledger and the actual artifacts rendered as markdown in the browser.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PHASES = ["requirements", "plan", "implement", "verify", "document"]
ARTIFACT_FILES = ["spec.md", "plan.md", "verification.md"]
MAX_ARTIFACT_BYTES = 120_000


# ── scanning ────────────────────────────────────────────────────────────────

def find_root(start: Path) -> Path | None:
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "specs").is_dir():
            return candidate
    return None


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:MAX_ARTIFACT_BYTES]
    except OSError:
        return None


def feature_next(feature_dir: Path, slug: str, phase: str) -> dict:
    if phase == "requirements":
        if not (feature_dir / "spec.md").exists():
            return {"cmd": f"/sdlc:requirements", "label": "spec in progress", "hint": "", "kind": "run"}
        return {"cmd": f"approve the spec for {slug}", "label": "approve spec",
                "hint": "review the spec, then tell Claude:", "kind": "review"}
    if phase == "plan":
        if not (feature_dir / "plan.md").exists():
            return {"cmd": f"/sdlc:plan {slug}", "label": "/sdlc:plan", "hint": "", "kind": "run"}
        return {"cmd": f"approve the plan for {slug}", "label": "approve plan",
                "hint": "review the plan, then tell Claude:", "kind": "review"}
    if phase in ("implement", "verify", "document"):
        return {"cmd": f"/sdlc:{phase} {slug}", "label": f"/sdlc:{phase}", "hint": "resume with", "kind": "run"}
    if phase == "done":
        return {"cmd": "", "label": "", "hint": "", "kind": "done"}
    return {"cmd": "/sdlc:status", "label": "/sdlc:status", "hint": "unknown phase — check with", "kind": "run"}


def state_text(phase: str, nxt: dict, updated: str, tasks: dict | None = None) -> str:
    if nxt["kind"] == "review":
        return ("awaiting spec review" if phase == "requirements" else "awaiting plan review")
    if nxt["kind"] == "done":
        return f"shipped {short_date(updated)}".strip()
    verb = {"requirements": "drafting spec", "plan": "planning", "implement": "implementing",
            "verify": "verifying", "document": "documenting"}.get(phase, phase)
    if phase == "implement" and tasks and tasks.get("total"):
        return f"{verb} · {tasks['done']}/{tasks['total']} tasks"
    return verb


def short_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d")
    except (ValueError, AttributeError, TypeError):
        return ""


def scan(root: Path) -> dict:
    features = []
    for status_file in sorted((root / "specs").glob("*/status.json")):
        try:
            st = json.loads(status_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = st.get("slug", status_file.parent.name)
        phase = st.get("phase", "?")
        nxt = feature_next(status_file.parent, slug, phase)
        artifacts = {}
        for name in ARTIFACT_FILES:
            content = read_text(status_file.parent / name) if (status_file.parent / name).exists() else None
            if content is not None:
                artifacts[name] = content
        features.append({
            "slug": slug,
            "feature": st.get("feature", ""),
            "phase": phase,
            "updatedAt": st.get("updatedAt", ""),
            "updatedShort": short_date(st.get("updatedAt", "")),
            "gates": st.get("gates", {}),
            "artifacts": artifacts,
            "next": nxt,
            "track": st.get("track", "full"),
            "group": {"review": "review", "done": "shipped"}.get(nxt["kind"], "progress"),
            "stateText": state_text(phase, nxt, st.get("updatedAt", ""), st.get("tasks")),
        })

    lessons = []
    lessons_dir = root / "lessons"
    if lessons_dir.is_dir():
        for lesson_file in sorted(lessons_dir.glob("*.md")):
            if lesson_file.name.upper() == "INDEX.MD":
                continue
            content = read_text(lesson_file)
            if content:
                lessons.append({"name": lesson_file.name, "content": content})

    metrics = []
    metrics_file = root / "specs" / "metrics.jsonl"
    if metrics_file.exists():
        for line in (read_text(metrics_file) or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                metrics.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    verify_events = [e for e in metrics if e.get("event") == "verify"]
    green_rate = (f"{round(100 * sum(1 for e in verify_events if e.get('testsGreenFirstTry')) / len(verify_events))}%"
                  if verify_events else "–")

    return {
        "repo": root.name,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "stats": {
            "needsYou": sum(1 for f in features if f["group"] == "review"),
            "inFlight": sum(1 for f in features if f["group"] != "shipped"),
            "shipped": sum(1 for f in features if f["group"] == "shipped"),
            "firstTryGreen": green_rate,
            "lessons": len(lessons),
        },
        "features": features,
        "lessons": lessons,
    }


# ── template ────────────────────────────────────────────────────────────────

TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"

def _template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")



def build_html(state: dict | None, serve: bool, repo_name: str) -> str:
    payload = "null" if serve else json.dumps(state).replace("</", "<\\/")
    return (_template()
            .replace("__REPO__", repo_name)
            .replace("__SERVE__", "true" if serve else "false")
            .replace("__STATE__", payload))


# ── serve mode ──────────────────────────────────────────────────────────────

def make_handler(root: Path):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, ctype: str, body: bytes):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8",
                           build_html(None, serve=True, repo_name=root.name).encode("utf-8"))
            elif path == "/state.json":
                self._send(200, "application/json", json.dumps(scan(root)).encode("utf-8"))
            else:
                self._send(404, "text/plain", b"not found")

        def log_message(self, *args):
            pass

    return DashboardHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SDLC dashboard: static snapshot or live local board")
    parser.add_argument("root", nargs="?", default=".", help="repo root (or any dir inside it)")
    parser.add_argument("-o", "--output", help="static mode: output path (default <root>/dashboard.html)")
    parser.add_argument("--serve", action="store_true", help="serve a live board instead of writing a file")
    parser.add_argument("--port", type=int, default=8645, help="port for --serve (default 8645)")
    args = parser.parse_args(argv)

    root = find_root(Path(args.root))
    if root is None:
        print(f"error: no specs/ directory found at or above {Path(args.root).resolve()}", file=sys.stderr)
        return 1

    if args.serve:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(root))
        print(f"serving {root.name} at http://127.0.0.1:{args.port} (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0

    state = scan(root)
    out = Path(args.output) if args.output else root / "dashboard.html"
    out.write_text(build_html(state, serve=False, repo_name=root.name), encoding="utf-8")
    print(f"wrote {out} ({len(state['features'])} feature(s), {len(state['lessons'])} lesson(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
