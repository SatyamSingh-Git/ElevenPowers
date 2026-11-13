# The test command a project already declares

*2026-11-13. Follows [journey 102](../../../journey/102-a-healthy-install-that-read-as-broken.md).*

## Why

Discovery finds a Python test command only from `pytest.ini` or
`[tool.pytest.ini_options]`. It found none in 6 of the 12 held-out projects:
cachetools, iniconfig, more-itertools, oauthlib, pycparser and tomli. Those
users get no test verification until they declare one by hand.

Every one of the six already says how it runs its tests. It is written in a
file discovery does not read, so each was run as written in its own prepared
environment (2026-11-12):

| project | declared in | as written | runner and paths only |
|---|---|---|---|
| cachetools | `tox.ini` | **exit 4**: `--cov` needs pytest-cov | passes, 366 tests |
| iniconfig | workflow | passes, 54 | passes |
| more-itertools | `tox.ini`, `Makefile` | passes | passes |
| oauthlib | `tox.ini` | passes, 722 | passes |
| pycparser | `Makefile` `test:` | passes | passes |
| tomli | workflow | passes | passes |

So the project's own declaration is the right source, but copying it word for
word can fail outside the tool that owns it. A failing test command is worse
than none: under `strict` it sends the agent back for nothing.

## Borrowed

- **tox's own file format.** `[testenv]` `commands` in `tox.ini`, read with
  the standard library's `configparser`.
- **make's target syntax.** The first recipe line of a `test:` target.
- **GitHub Actions `run:` steps.** Only those that invoke pytest or unittest.

What this adds: it keeps the runner and the paths the project names, and drops
what belongs to the owning tool. That covers placeholders such as `{posargs}`
and `{envpython}`, make variables, plugin flags such as `--cov`, and wrappers
such as `uv run --with …`.

## Behaviour

- **Only when existing discovery found no `tests` command.** Manifest
  discovery and explicit `commands.tests` keep winning.
- **Sources, in order:** `tox.ini`, then `Makefile`, then
  `.github/workflows/*.yml|yaml`. The first source naming pytest or unittest
  wins.
- **Reduction:**
  - pytest (`pytest`, `py.test`, `python -m pytest`) becomes
    `python -m pytest` followed by its arguments that are existing paths in
    the project. Options are dropped.
  - unittest (`python -m unittest`, `python3 -m unittest`) becomes
    `python -m unittest`, plus `discover` when the project used it. Its other
    options are dropped.
- **Refused, so no command:**
  - a line that changes directory (`cd`, or a workflow step with
    `working-directory:`);
  - a line that runs anything other than one test runner after `&&` or `;`;
  - any runner other than pytest or unittest.
- **Bounded:**
  - files over 256 KiB are skipped;
  - at most 20 workflow files are read;
  - nothing is executed during discovery.
- **Said out loud.** The setup summary names the source:
  `tests: python -m pytest tests (from tox.ini)`.

## Non-goals

- No guessing from a `tests/` folder. A project with no declaration still
  gets "No test command found" and the `--tests` line.
- No tox, nox or hatch invocation. Those create environments and may use the
  network.
- Languages other than Python. npm, Cargo and Go are already found from their
  manifests.

## Checks

- **Forward:** each of the six projects gets a command, and it passes in its
  own environment.
- **Controls:** the six projects that already had a command keep exactly the
  one they had. A project with no declaration gets none.
- **Adversarial fixtures:** `cd sub && pytest`, a `test:` target that runs
  `tox`, a workflow step with `working-directory:`, flags and placeholders,
  a commented-out line, and an oversized file.
