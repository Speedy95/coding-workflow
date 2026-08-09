---
type: lesson
inclusion: fileMatch
match: "tests/**"
tags: [testing, cli]
source: 001-due-dates
verified: 2026-08-03
---
# DEFAULT_STORE binds at def time — CLI tests must chdir
**Fact:** `add_task`/`load_tasks` capture `DEFAULT_STORE` as a default
parameter value, which is evaluated at `def` time — monkeypatching
`taskler.DEFAULT_STORE` does NOT redirect calls made through `main()`. Since
`DEFAULT_STORE` is the relative path `tasks.json`, the working test approach is
`monkeypatch.chdir(tmp_path)`.
**Why it matters:** a CLI test written with `monkeypatch.setattr(taskler,
"DEFAULT_STORE", ...)` passes vacuously against the real cwd or corrupts a
stray tasks.json.
**Apply when:** writing any test that goes through `main()`, or touching how
the store path is resolved. See also
[capsys does not capture input()'s prompt](capsys-does-not-capture-input-prompt.md)
for another way `main()`-path tests pass vacuously.
