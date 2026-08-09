"""taskler - a tiny JSON-file-backed task list CLI.

Usage:
    python taskler.py add "Buy milk"
    python taskler.py list [--all]
    python taskler.py done 1
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

DEFAULT_STORE = Path("tasks.json")


def load_tasks(store: Path = DEFAULT_STORE) -> list[dict]:
    if not store.exists():
        return []
    return json.loads(store.read_text(encoding="utf-8"))


def save_tasks(tasks: list[dict], store: Path = DEFAULT_STORE) -> None:
    store.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def _validate_due(due: str) -> str:
    try:
        if date.fromisoformat(due).isoformat() == due:
            return due
    except ValueError:
        pass
    raise ValueError(f"invalid due date {due!r}: expected YYYY-MM-DD")


def add_task(title: str, store: Path = DEFAULT_STORE, due: str | None = None) -> dict:
    title = title.strip()
    if not title:
        raise ValueError("task title must not be empty")
    if due is not None:
        due = _validate_due(due)
    tasks = load_tasks(store)
    task = {"id": max((t["id"] for t in tasks), default=0) + 1, "title": title, "done": False}
    if due is not None:
        task["due"] = due
    tasks.append(task)
    save_tasks(tasks, store)
    return task


def complete_task(task_id: int, store: Path = DEFAULT_STORE) -> dict:
    tasks = load_tasks(store)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks, store)
            return task
    raise KeyError(f"no task with id {task_id}")


def remove_task(task_id: int, store: Path = DEFAULT_STORE) -> dict:
    tasks = load_tasks(store)
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            save_tasks(tasks, store)
            return task
    raise KeyError(f"no task with id {task_id}")


def format_tasks(tasks: list[dict], include_done: bool = False,
                 today: date | None = None) -> str:
    today = today or date.today()
    visible = [t for t in tasks if include_done or not t["done"]]
    if not visible:
        return "(no tasks)"
    open_tasks = [t for t in visible if not t["done"]]
    done_tasks = [t for t in visible if t["done"]]
    dated = sorted((t for t in open_tasks if t.get("due")), key=lambda t: t["due"])
    undated = [t for t in open_tasks if not t.get("due")]
    lines = []
    for t in dated + undated + done_tasks:
        line = f"[{'x' if t['done'] else ' '}] {t['id']}: {t['title']}"
        due = t.get("due")
        if due:
            line += f" ({due})"
            if not t["done"] and date.fromisoformat(due) < today:
                line = "! " + line
        lines.append(line)
    return "\n".join(lines)


def _due_argument(value: str) -> str:
    try:
        return _validate_due(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskler", description="tiny task list")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title")
    p_add.add_argument("--due", type=_due_argument, default=None,
                       help="due date as YYYY-MM-DD")

    p_list = sub.add_parser("list", help="list open tasks")
    p_list.add_argument("--all", action="store_true", help="include completed tasks")

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)

    p_remove = sub.add_parser("remove", help="delete a task")
    p_remove.add_argument("id", type=int)
    p_remove.add_argument("--yes", action="store_true",
                          help="delete without asking for confirmation")

    args = parser.parse_args(argv)

    if args.command == "add":
        task = add_task(args.title, due=args.due)
        print(f"added {task['id']}: {task['title']}")
    elif args.command == "list":
        print(format_tasks(load_tasks(), include_done=args.all))
    elif args.command == "done":
        task = complete_task(args.id)
        print(f"done {task['id']}: {task['title']}")
    elif args.command == "remove":
        tasks = load_tasks()
        target = next((t for t in tasks if t["id"] == args.id), None)
        if target is None:
            print(f"error: no task with id {args.id}", file=sys.stderr)
            return 1
        if not args.yes:
            print(format_tasks([target], include_done=True))
            try:
                answer = input("remove? [y/N] ")
            except EOFError:
                answer = ""
            if answer.strip().lower() not in ("y", "yes"):
                return 1
        remove_task(args.id)
        print(f"removed {target['id']}: {target['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
