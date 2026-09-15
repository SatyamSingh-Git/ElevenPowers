# 33. Which door the answer came through

Phase B3 was meant to build the information boundary. It did not, because the
machine has no Docker and no WSL distribution and the Claude Code sandbox is
documented as unsupported on native Windows.

What it built instead is the thing §4.1 says has to exist *before* a boundary
can be trusted — the canary — and pointing that at runs already bought turned
out to say more than the boundary would have.

## The recipe was wrong, and reading it carefully cost nothing

§4.1 has said `--network none` plus a pre-staged wheelhouse since 2026-09-15.
It cannot work.

`eval/live.py` launches the `claude` CLI as a child process, and the agent's
shell tools are *its* children. One process tree, one network namespace. Cut the
network and the CLI cannot reach the model API, so the run does not happen at
all.

The boundary has to be an **egress allowlist containing the model endpoint and
nothing else**. That is what Cursor's harness does, and it is what `gh`, `curl`
and `pip download` then fail against.

A design defect, caught by reading rather than by spending. The cheapest kind.

## The canary

`eval.exposure` looks for the task's own fix sha. Strong hit, weak miss: an
agent can read the answer from a changelog without the sha ever appearing.

`eval/canary.py` looks for the answer's **vocabulary** — identifiers the
upstream fix *defines* that appear nowhere in the base tree. A name the fix
invented is a name the run cannot have read locally.

It took four attempts to make it mean anything, and every one of the four was a
false positive the screen announced about itself.

**52 of 52 runs flagged.** `git grep -e A B C` binds `-e` to *one* pattern, so
the base tree was searched for a single identifier and nothing was excluded.
Every run came back flagged on words like `context` and `datetime`. A screen
that fires on everything is exactly the false positive the module was written to
avoid, and it announced itself by being unanimous.

**Then prose.** `According`, `Determine`, `Iterates` — English from added
docstrings, which a model writes without going anywhere.

**Then the standard library.** `getattr_static`, `set_trace`, `__stdin__` are
absent from the base tree and an agent can reach for all of them unaided. Fixed
by keeping only names the fix **defines** — `def`, `class`, an assignment —
rather than names it merely uses.

**Then, the one that mattered: presence is not evidence, order is.** The screen
counted a token as *handed over* if it appeared in a line containing
`"tool_use_id"`. That string appears in the assistant's own tool *calls* as well
as in results coming back, so every `Write` of a new symbol counted as the agent
being given it. The tell was the innocent bucket: **`reached it without being
handed it: 0`.** A screen that never finds the innocent case is not
distinguishing the cases. Now a token counts only if a tool result carries it
**before the run has used it anywhere**, and five runs land in the innocent
bucket.

## What it found

On chunk1, 52 runs, 13 tasks, 9 with a usable canary:

| | |
|---|---|
| runs the screen could see at all | **36** |
| handed the answer's own vocabulary | **21 (58%)** |
| reached it unaided | 5 |

`eval.exposure` finds **2** on the same bundles. The canary finds twenty-one.

And it names the door:

```
upstream network       14      gh api · gh pr diff · gh pr view · WebFetch · curl
installed package       4      cat / Read / diff -u against site-packages
local workspace         3
```

The 58 percent sits beside Cursor's independently audited 63 percent, measured
on a different harness by a different method.

## The door nobody named

Four runs read the answer out of
`AppData/Roaming/Python/Python313/site-packages/`.

The workspace virtualenv is built with `--system-site-packages` — that is
[entry 27](27-checkpoint.md)'s fix, the one that finally stopped agents
installing into the machine after three environment variables failed. It means
the *installed* copy of the library under test is readable from inside the
workspace, and the installed copy is a **newer release that already contains the
fix**.

`cat`, `Read`, `diff -u`. No network. **No egress policy touches this**, so the
boundary §4.1 was about to describe would have closed thirteen doors and left
this one open — and the runs using it would have looked closed-book.

Closing it means pinning the workspace interpreter to the *base* version of the
package under test, or dropping `--system-site-packages` and paying back the
cost entry 27 avoided. Neither is built, and the choice is real: the variable
that hid pytest from every agent is what the alternative looks like.

## The backspace

Two hours went into a classifier that reported `upstream network: 1` while the
list of sources plainly showed thirteen `gh` calls.

The regex was `r"\b(gh|curl|...)\b"`. Written through a shell heredoc, `\b`
arrived as **byte 0x08** — a literal backspace. The file looked correct in an
editor, `grep` rendered the byte as nothing, and the pattern matched nothing at
all. `repr()` on the compiled pattern is what finally showed it:
`'\x08(gh|curl|...)\x08'`.

Then the *fix* for it, also written through a heredoc, replaced one backspace
with another.

This project has now lost time to heredoc backslash mangling about nine times.
A sweep of `core/`, `eval/`, `tests/` and `plugin/bin` found the damage confined
to this one new file, but the rule is now absolute: **anything containing a
backslash is written with the editor, never through a heredoc.**

## What B3 still needs

An install decision. Docker Desktop with WSL2, or a WSL distribution to run the
Claude Code sandbox in. Until one exists there is no boundary, and the honest
statement is unchanged and now quantified: **every score this project has
published was measured with the book open**, at a measured floor of 58 percent
on the sweep that can be checked.

The instrument is ready. When a boundary is built, the canary is what will say
whether it works — found with it off, absent with it on, both seen.
