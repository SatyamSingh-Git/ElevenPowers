# 103 — The command was already written down

*2026-11-13. Follows [102](102-a-healthy-install-that-read-as-broken.md).*

The new setup summary said "No test command found" on cachetools. That was
true, and half the held-out projects would have said the same. None of the
six was undecided, though. Each wrote its test run down in `tox.ini`, a
`Makefile` or a CI workflow, a file discovery did not read.

## Copying it was not enough

Each declaration was first run as written, in the project's own prepared
environment. Five passed. cachetools' tox line exited 4, because it asks for
`--cov` and pytest-cov was not installed outside tox. A test command that
fails is worse than none: under `strict` it sends the agent back for nothing.

So the line is reduced to what is the project's and not the tool's: the
runner, and the paths it names. With that, cachetools ran 366 tests green.
The other four new commands passed too: oauthlib (722 tests),
more-itertools, pycparser and tomli.

## What the rehearsal caught

Pointed at this repository as a control, the reader found `python -m pytest`.
It found it in the wrong place: a workflow step `python -m pip install
pytest`, where `pytest` is a package name. A line that installs is now not a
test run.

After that, this repository correctly finds its real suite in `tests.yml`.
That raised a second problem. This session runs with ElevenPowers installed,
and the full suite here takes hours, which the user has ruled out on this
machine. Its untracked local config now sets `"tests": ""`. That is the
existing switch for turning one need off.

## Also pinned

- **A refused line stops the search.** `cd sub && pytest` in a Makefile does
  not fall through to a bare `pytest` in CI, which would collect different
  tests.
- **tox's `changedir`.** Found by a mutant that survived: the `cd` check was
  redundant and protected nothing. The real gap was the directory change tox
  makes on its own.
