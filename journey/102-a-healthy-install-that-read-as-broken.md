# 102 — A healthy install that read as broken

*2026-11-12. Item 4 of the build list: two-minute onboarding.*

Before changing anything, setup was run the way a new person would run it:
on a fresh copy of cachetools, a real project with a `tests/` folder.

## What it said

Forty lines. A block of host checks was printed twice. The dashes came out
as `?` boxes in a Windows console. It opened with "Pipeline health:
attention; task verification: UNVERIFIED", then six "Next action" lines.
Every one of them meant the same thing: nothing has happened yet, because
no session has started.

It never said which test command it would run. Asked directly, discovery
had found none. cachetools has no `pytest.ini` and no
`[tool.pytest.ini_options]`, and those are what discovery looks for. So
this person would get no test verification, and nothing in the output told
them.

## What it says now

A dozen lines:

- what was installed, where, and in which mode;
- the checks it found;
- other agents' rules it will deliver;
- declared rules, and how many files it read;
- only problems a person can act on, each with the command that fixes it;
- the next step.

For cachetools, the one problem is the missing test command, with a line
to paste: `ep_setup.py claude --project … --tests "your test command"`.

`--tests` writes only `commands.tests`. It does not use `save`, because
`save` writes the effective configuration, which would freeze every
discovered command into the file. An unreadable config file is refused,
not overwritten.

## What was decided against

**Guessing pytest from a `tests/` folder.** That would have made cachetools
work with no extra line. It would also run a guessed command on every task
in every project that only looks like it. Discovery stays where it was,
and the summary names the gap instead.

## Found on the way

- Every suggested command now quotes paths in the platform's own way. A
  test with a space in the project path failed first, with the path cut at
  the space.
- The installation guide still said completion runs test strength
  automatically, which [101](101-the-agent-waited-for-a-report-it-never-read.md)
  had made untrue.
- The `\n` in a changelog line written through a heredoc became a real
  newline twice in two days. Both times `check.py` caught the broken map.
