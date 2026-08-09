import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import taskler


@pytest.fixture
def store(tmp_path):
    return tmp_path / "tasks.json"


def test_add_assigns_incrementing_ids(store):
    first = taskler.add_task("one", store)
    second = taskler.add_task("two", store)
    assert (first["id"], second["id"]) == (1, 2)


def test_add_rejects_empty_title(store):
    with pytest.raises(ValueError):
        taskler.add_task("   ", store)


def test_tasks_persist_to_store(store):
    taskler.add_task("persist me", store)
    assert [t["title"] for t in taskler.load_tasks(store)] == ["persist me"]


def test_complete_marks_done(store):
    task = taskler.add_task("finish", store)
    taskler.complete_task(task["id"], store)
    assert taskler.load_tasks(store)[0]["done"] is True


def test_complete_unknown_id_raises(store):
    with pytest.raises(KeyError):
        taskler.complete_task(99, store)


def test_add_stores_due(store):
    task = taskler.add_task("pay rent", store, due="2026-08-15")
    assert task["due"] == "2026-08-15"
    assert taskler.load_tasks(store)[0]["due"] == "2026-08-15"


def test_add_invalid_due_raises_and_stores_nothing(store):
    with pytest.raises(ValueError):
        taskler.add_task("x", store, due="15.08.2026")
    assert taskler.load_tasks(store) == []


def test_add_without_due_has_no_due_key(store):
    task = taskler.add_task("no date", store)
    assert "due" not in task


def test_cli_add_due_persists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert taskler.main(["add", "pay rent", "--due", "2026-08-15"]) == 0
    assert taskler.load_tasks()[0]["due"] == "2026-08-15"


def test_cli_add_invalid_due_exits_2_and_stores_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        taskler.main(["add", "x", "--due", "15.08.2026"])
    assert excinfo.value.code == 2
    assert taskler.load_tasks() == []


def test_remove_deletes_and_persists(store):
    taskler.add_task("keep", store)
    doomed = taskler.add_task("doomed", store)
    removed = taskler.remove_task(doomed["id"], store)
    assert removed["title"] == "doomed"
    assert [t["title"] for t in taskler.load_tasks(store)] == ["keep"]


def test_remove_unknown_id_raises_and_store_unchanged(store):
    taskler.add_task("keep", store)
    before = store.read_text(encoding="utf-8")
    with pytest.raises(KeyError):
        taskler.remove_task(99, store)
    assert store.read_text(encoding="utf-8") == before


def test_remove_keeps_other_tasks_intact(store):
    taskler.add_task("first", store, due="2099-01-01")
    doomed = taskler.add_task("doomed", store)
    done = taskler.add_task("third", store)
    taskler.complete_task(done["id"], store)
    taskler.remove_task(doomed["id"], store)
    remaining = taskler.load_tasks(store)
    assert [(t["id"], t["title"], t["done"]) for t in remaining] == [
        (1, "first", False), (3, "third", True)]
    assert remaining[0]["due"] == "2099-01-01"


def test_cli_remove_yes_deletes_and_reports(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "keep"])
    taskler.main(["add", "doomed"])
    capsys.readouterr()
    assert taskler.main(["remove", "2", "--yes"]) == 0
    assert capsys.readouterr().out.strip() == "removed 2: doomed"
    assert [t["title"] for t in taskler.load_tasks()] == ["keep"]


def test_cli_remove_unknown_id_errors_store_unchanged(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "keep"])
    before = (tmp_path / "tasks.json").read_text(encoding="utf-8")
    capsys.readouterr()
    assert taskler.main(["remove", "99", "--yes"]) == 1
    assert "99" in capsys.readouterr().err
    assert (tmp_path / "tasks.json").read_text(encoding="utf-8") == before


@pytest.mark.parametrize("answer", ["y", "YES", " y "])
def test_cli_remove_confirmed_deletes(tmp_path, monkeypatch, capsys, answer):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "doomed"])
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    capsys.readouterr()
    assert taskler.main(["remove", "1"]) == 0
    assert "removed 1: doomed" in capsys.readouterr().out
    assert taskler.load_tasks() == []


@pytest.mark.parametrize("answer", ["n", "", "nope"])
def test_cli_remove_declined_aborts(tmp_path, monkeypatch, capsys, answer):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "survivor"])
    before = (tmp_path / "tasks.json").read_text(encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    capsys.readouterr()
    assert taskler.main(["remove", "1"]) == 1
    assert (tmp_path / "tasks.json").read_text(encoding="utf-8") == before


def test_cli_remove_eof_aborts(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "survivor"])
    before = (tmp_path / "tasks.json").read_text(encoding="utf-8")

    def no_stdin(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", no_stdin)
    capsys.readouterr()
    assert taskler.main(["remove", "1"]) == 1
    assert (tmp_path / "tasks.json").read_text(encoding="utf-8") == before


def test_cli_remove_prompt_shows_task_row(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "look at me", "--due", "2020-01-01"])
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", fake_input)
    capsys.readouterr()
    taskler.main(["remove", "1"])
    # overdue task: prompt row must match the list renderer, "!" included
    assert "! [ ] 1: look at me (2020-01-01)" in capsys.readouterr().out
    assert prompts == ["remove? [y/N] "]


def test_format_shows_due_and_orders_dated_first(store):
    taskler.add_task("undated one", store)
    taskler.add_task("later", store, due="2099-09-01")
    taskler.add_task("sooner", store, due="2099-08-10")
    lines = taskler.format_tasks(taskler.load_tasks(store)).splitlines()
    assert lines[0] == "[ ] 3: sooner (2099-08-10)"
    assert lines[1] == "[ ] 2: later (2099-09-01)"
    assert lines[2] == "[ ] 1: undated one"


def test_overdue_marked_and_sorted_first(store):
    taskler.add_task("old", store, due="2026-08-01")
    taskler.add_task("today-due", store, due="2026-08-02")
    lines = taskler.format_tasks(
        taskler.load_tasks(store), today=date(2026, 8, 2)
    ).splitlines()
    assert lines[0] == "! [ ] 1: old (2026-08-01)"
    assert lines[1] == "[ ] 2: today-due (2026-08-02)"


def test_done_tasks_never_marked_overdue(store):
    task = taskler.add_task("old", store, due="2026-08-01")
    taskler.complete_task(task["id"], store)
    out = taskler.format_tasks(taskler.load_tasks(store), include_done=True,
                               today=date(2026, 8, 2))
    assert "!" not in out


def test_pre_feature_store_shape_still_works(store):
    import json
    store.write_text(json.dumps([{"id": 1, "title": "legacy", "done": False}]),
                     encoding="utf-8")
    tasks = taskler.load_tasks(store)
    assert taskler.format_tasks(tasks) == "[ ] 1: legacy"
    taskler.complete_task(1, store)
    assert taskler.load_tasks(store)[0]["done"] is True


def test_all_lists_open_before_done(store):
    done = taskler.add_task("old chore", store, due="2026-07-01")
    taskler.complete_task(done["id"], store)
    taskler.add_task("buy milk", store)
    taskler.add_task("later", store, due="2099-09-01")
    taskler.add_task("sooner", store, due="2099-08-10")
    lines = taskler.format_tasks(taskler.load_tasks(store), include_done=True,
                                 today=date(2026, 8, 3)).splitlines()
    assert lines[0] == "[ ] 4: sooner (2099-08-10)"
    assert lines[1] == "[ ] 3: later (2099-09-01)"
    assert lines[2] == "[ ] 2: buy milk"
    assert lines[3] == "[x] 1: old chore (2026-07-01)"


def test_all_done_tasks_in_insertion_order_ignoring_due(store):
    first = taskler.add_task("done later-due", store, due="2099-09-01")
    second = taskler.add_task("done sooner-due", store, due="2099-08-01")
    taskler.complete_task(first["id"], store)
    taskler.complete_task(second["id"], store)
    lines = taskler.format_tasks(taskler.load_tasks(store),
                                 include_done=True).splitlines()
    assert lines[0] == "[x] 1: done later-due (2099-09-01)"
    assert lines[1] == "[x] 2: done sooner-due (2099-08-01)"


def test_done_overdue_renders_plain_and_last(store):
    overdue_done = taskler.add_task("shipped", store, due="2026-07-30")
    taskler.complete_task(overdue_done["id"], store)
    taskler.add_task("open task", store)
    lines = taskler.format_tasks(taskler.load_tasks(store), include_done=True,
                                 today=date(2026, 8, 3)).splitlines()
    assert lines[-1] == "[x] 1: shipped (2026-07-30)"


def test_cli_list_all_prints_open_then_done(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    taskler.main(["add", "old chore", "--due", "2026-07-01"])
    taskler.main(["done", "1"])
    taskler.main(["add", "buy milk"])
    capsys.readouterr()
    assert taskler.main(["list", "--all"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "[ ] 2: buy milk"
    assert lines[1] == "[x] 1: old chore (2026-07-01)"


def test_format_hides_done_by_default(store):
    taskler.add_task("open", store)
    done = taskler.add_task("closed", store)
    taskler.complete_task(done["id"], store)
    tasks = taskler.load_tasks(store)
    assert "closed" not in taskler.format_tasks(tasks)
    assert "closed" in taskler.format_tasks(tasks, include_done=True)
