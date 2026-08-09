---
type: lesson
inclusion: fileMatch
match: "tests/**"
tags: [testing, cli]
source: 003-remove-command
verified: 2026-08-03
---
# capsys does not capture input()'s prompt string
**Fact:** pytest's `capsys` never sees the prompt argument of
`input("remove? [y/N] ")` — and monkeypatched `input` replacements that
ignore their `prompt` parameter silently drop it too. A test asserting on
captured stdout can pass while the prompt text is wrong or missing.
**Why it matters:** 003's whole suite stayed green with the prompt literal
completely unpinned (verify finding F1) — a renamed or inverted prompt
(`delete? [Y/n]`) would have shipped unnoticed.
**Apply when:** testing any interactive prompt — have the `input` stub record
its `prompt` argument and assert on the recorded value, not on capsys. See
also [DEFAULT_STORE binds at def time](default-store-binds-at-def-time.md)
for another vacuous-pass trap in `main()`-path tests.
