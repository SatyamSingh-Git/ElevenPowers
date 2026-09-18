"""Claims about things nobody ran.

Design note: `docs/design/unverified-assumptions.md`.

One day's defects in this repository, every one of them the same shape: a
pattern was written describing some producer's output, and the producer was
never run. TAP counters, a monorepo's line prefix, how Go attaches methods, what
Rust names first, a grammar's spelling, how long a parse costs. Seven, found by
executing the real thing and reading what came back - **none** by thinking
harder about it.

That is not local. It is **API Knowledge Conflict**, 20.41% of hallucinations in
the largest taxonomy of the phenomenon (Zhang et al., arXiv:2409.20550, 1,380
annotated snippets), and the obvious remedy is measured to barely work: their
retrieval-augmented mitigation moved Pass@1 by 0.87 to 3.05 percentage points,
and other work finds that *even with oracle documentation retrieval* models
still misuse APIs, because documentation says **what** to call and not **how**
it behaves.

What does work is execution. So this module does not ask the agent to be
careful, and does not hand it more documentation. It asks the ledger a question
the ledger can answer:

    a pattern this task introduced, which never matched any output this task
    actually saw, is an assumption nobody verified

and a second one, from machinery `core/stress.py` already runs:

    a test this task added, which passes on the tree as it was, did not test
    this change

Both report. Neither refuses.
"""

from __future__ import annotations

import re
from pathlib import Path

# A string literal worth treating as a claim about text. Two or more of these,
# and it is a pattern rather than a message.
METACHARACTERS = ("^", "$", r"\d", r"\s", r"\w", r"\b", "[", "]", "(", ")",
                  "+", "*", "?", "|", "{")

# ...and at least one construct that only a regular expression has. Counting
# metacharacters alone is not enough, because *source code* is full of them:
# pointing the check at its own diff reported `def secret_santa(names):` and
# `import re\nCOUNT = re.compile(...)` - test fixtures holding code, which have
# brackets and parentheses and mean nothing about any tool's output.
#
# Measured before adopting rather than reasoned about: against all 67 pattern
# literals `core/` compiles, read out of the AST so concatenated pieces count,
# this rule loses **none** - and it drops **all seven** of the code fixtures the
# dogfood run falsely reported. `test_the_strong_rule_keeps_every_real_pattern_
# in_this_repo` re-measures it, so a future pattern shape cannot slip out.
STRONG = re.compile(
    r"\^|\$"                       # anchors
    r"|\\[dswbSWDBAZ]"             # a character class written as an escape
    r"|\|"                         # alternation
    r"|[*+]"                       # quantifiers
    r"|\{\d"                       # a counted quantifier, not an f-string brace
    r"|\(\?"                       # group flags, lookaround, named groups
    r"|\[\^"                       # a negated class
    r"|\[[^\]]{2,}\]"              # a character class with real content
)

# String literals on lines a diff added. Both quote styles, and Python's raw
# prefix, which is how nearly every regex in this repository is written.
LITERAL = re.compile(r"""(?:r|rb|br)?(?P<q>['"])(?P<body>(?:\\.|(?!(?P=q))[^\\])*)(?P=q)""")

MINIMUM = 6


# `python -m pytest` is a claim about pytest, not about python. Dropping the
# launcher is what keeps the word `python` in a docstring from vouching for
# every regex in the file that contains it.
LAUNCHERS = frozenset({"python", "python3", "py", "npx", "uv", "poetry",
                       "pipenv", "pdm", "sh", "bash", "zsh", "cmd", "pwsh",
                       "powershell", "env", "time", "sudo", "xargs",
                       "bundle", "dotnet"})

# Words that name a task rather than a tool. `npm test` must not make every file
# containing the word `test` look like it is describing npm's output.
NOT_A_NAME = frozenset({"test", "tests", "run", "build", "ci", "check", "start",
                        "lint", "exec", "install", "all", "src", "dist", "main"})


def _added_by_file(root: Path, base: str, paths: list[str]) -> dict[str, list[str]]:
    """The lines this task introduced, kept with the file they landed in.

    Per file rather than pooled, because a pattern is only a claim about a
    runner's output if the code around it is about that runner.
    """
    import subprocess

    if not base or not paths:
        return {}
    try:
        done = subprocess.run(["git", "diff", "-U0", base, "--", *paths], cwd=root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return {}
    if done.returncode != 0:
        return {}
    out: dict[str, list[str]] = {}
    where = ""
    for line in done.stdout.splitlines():
        if line.startswith("+++ "):
            where = line[4:].strip()
            where = where[2:] if where.startswith("b/") else where
            out.setdefault(where, [])
        elif line.startswith("+") and where:
            out[where].append(line[1:])

    # A file the task *created* is untracked, and `git diff base -- path` says
    # nothing about it at all. Every pattern in every new file was therefore
    # invisible to this check - including the new module that shipped alongside
    # it. The whole file is what the task added, so read the whole file.
    for raw in paths:
        path = raw.replace("\\", "/")
        if path in out:
            continue
        here = root / path
        exists = subprocess.run(["git", "cat-file", "-e", f"{base}:{path}"], cwd=root,
                                capture_output=True)
        if exists.returncode == 0 or not here.is_file():
            continue
        try:
            out[path] = here.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
    return out


def _tool_names(commands) -> set[str]:
    """What to call the things this task actually ran.

    The **first** token that is not a flag and not a launcher, reduced to a bare
    name: `node` from `node --test`, `pytest` from `python -m pytest tests/`,
    `turbo` from `turbo test`.

    First, rather than every token, because the rest of a command line is
    arguments. Taking them all made `git status` vouch for any file mentioning
    the word status, and `pytest tests/test_redact.py` vouch for anything
    mentioning test_redact - which widens the narrowing back out again.
    """
    names: set[str] = set()
    for command in commands:
        fallback = ""
        for token in str(command).split():
            if token.startswith("-") or "=" in token:
                continue
            bare = token.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
            bare = re.sub(r"\.(exe|cmd|bat|ps1|py|js|mjs|ts|sh)$", "", bare)
            if len(bare) < 2 or bare in NOT_A_NAME:
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_+.\-]+", bare):
                continue
            if bare in LAUNCHERS:
                fallback = fallback or bare
                continue
            names.add(bare)
            break
        else:
            # Nothing but launchers: `python` alone is still what ran.
            if fallback:
                names.add(fallback)
    return names


def _names_a_tool(lines: list[str], tools: set[str]) -> bool:
    """Does this file's new code mention something the task ran?

    Case-sensitive and on a word boundary: code names a tool in the spelling you
    would type into a shell.

    Escapes are blanked first, because the motivating case defeats a naive word
    boundary: `core/parsers.py` names node as `r"\\bnode\\s+--test\\b"`, and the
    character before `node` there is the `b` of `\\b`. Found by running it - the
    forward test went silent on the one file the check was built for.
    """
    body = re.sub(r"\\.", " ", "\n".join(lines))
    return any(re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", body)
               for name in tools)


def patterns_added(root: Path, base: str, paths: list[str],
                   tools: set[str] | None = None) -> list[str]:
    """Regular expressions this task introduced, as written.

    Deliberately literal-by-literal rather than clever. A pattern built by
    concatenation is read in pieces, and a piece that matches nothing is still
    worth asking about - which is how `TAP_PREFIX` would have been caught.

    With `tools`, only files whose new code names one of them contribute. Most
    regexes in most repositories are claims about *data* - an email validator, a
    phone format, an HTML scrape - and no command will ever print something that
    matches them. Without this narrowing the check reports every one of them,
    every run, which on a client library or a scraper is most of the file.
    """
    added = _added_by_file(root, base, paths)
    lines = [line for body in added.values()
             if tools is None or _names_a_tool(body, tools)
             for line in body]
    found: list[str] = []
    for line in lines:
        if line.lstrip().startswith(("#", "//", "*")):
            continue                      # a comment is not a claim about text
        for match in LITERAL.finditer(line):
            body = match.group("body")
            if len(body) < MINIMUM:
                continue
            if sum(1 for mark in METACHARACTERS if mark in body) < 2:
                continue
            if not STRONG.search(body):
                continue              # source code, not a claim about output
            try:
                re.compile(body)
            except re.error:
                continue                  # not a pattern, or not one yet
            # A pattern that matches the empty string needs no skip here: it
            # matches every captured output, so it is confirmed by anything and
            # never reported. A guard for it was written, and flipping it showed
            # it did nothing - removed rather than left looking load-bearing.
            if body not in found:
                found.append(body)
    return found


def unverified(ledger, root: Path | None = None) -> list[str]:
    """Patterns this task wrote that nothing it ran ever produced.

    The question is not "is this regex correct" - nobody can answer that from
    the text. It is "did anything you actually saw look like this", which the
    ledger can answer exactly, because it kept what the commands printed.
    """
    here = root if root is not None else ledger.root
    seen = "\n".join(str(item.get("text", "")) for item in ledger.outputs)
    if not seen.strip():
        # Nothing was captured, so nothing can be confirmed *or* denied. Saying
        # "none of your patterns are verified" when no command ran at all is an
        # accusation dressed as a finding.
        return []
    tools = _tool_names(item.get("command", "") for item in ledger.outputs)
    out = []
    for body in patterns_added(here, ledger.base, list(ledger.touched), tools):
        try:
            # MULTILINE, because a pattern anchored with ^ or $ is written to
            # read one line of a runner's output, and every such pattern in this
            # repository is compiled that way. Matching without it made the
            # forward case fail - the check accusing a pattern that had in fact
            # been confirmed, which is the one error it must never make.
            if not re.search(body, seen, re.MULTILINE):
                out.append(body)
        except re.error:
            continue
    return out


def vacuous_tests(ledger) -> list[str]:
    """Tests this task added that already passed on the tree as it was.

    `core/stress.py` runs the declared check against the base commit and records
    which tests were red there. A test the task added which is **not** among
    them ran green against code that did not yet contain the change - so
    whatever it is testing, it is not this change.

    Silent unless the base tree was actually asked. No run, no accusation.
    """
    from .surface import TEST_NAME

    if not ledger.discrimination or not ledger.base:
        return []
    red = set(ledger.failed_before)
    if not red:
        # The base tree was asked and nothing came back red. That is already
        # reported as a discrimination verdict; repeating it here as a
        # complaint about every new test would be the same fact twice.
        return []
    added = [p for p in ledger.touched if TEST_NAME.search(p)]
    files_red = {r.split("::")[0].replace("\\", "/") for r in red}
    return [p for p in added if p not in files_red]


def wording(patterns: list[str], tests: list[str]) -> list[str]:
    """The report lines, or none at all."""
    said = []
    if patterns:
        shown = ", ".join(repr(p[:48]) for p in patterns[:2])
        more = f" (+{len(patterns) - 2} more)" if len(patterns) > 2 else ""
        said.append(f"unverified: {shown}{more} matched nothing this task ran. "
                    f"A pattern is a claim about output; run the thing and look")
    if tests:
        shown = ", ".join(tests[:2])
        more = f" (+{len(tests) - 2} more)" if len(tests) > 2 else ""
        said.append(f"{shown}{more} passed on the tree as it was, so it did not "
                    f"test this change")
    return said
