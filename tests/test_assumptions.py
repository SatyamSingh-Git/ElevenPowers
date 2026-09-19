"""Claims about things nobody ran.

Design: `docs/design/unverified-assumptions.md`. The check exists because one
day in this repository produced seven defects of a single shape - a pattern
written to describe some producer's output, and the producer never run. Every
one was found by executing the real thing; none by thinking harder.

The forward case is the one that must stay silent, because a check that fires on
every pattern is indistinguishable from the feature being absent, and a check
that fires on none is the state that let those seven through.
"""

from __future__ import annotations

import subprocess

import pytest

from core import assumptions
from core.ledger import Ledger
from core.obligations import Claim


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "parser.py").write_text("PATTERNS = {}\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def add_pattern(repo, body, names_tool=True):
    """Write a pattern into `parser.py`, with or without naming its producer.

    The dispatch line matters. A pattern is only a claim about a runner's output
    if the code around it is about that runner, and §7c narrows the check to
    exactly that - so a fixture without it is testing a different feature.
    """
    dispatch = "if cmd.startswith('node --test'):\n    pass\n" if names_tool else ""
    (repo / "parser.py").write_text(
        f'import re\nCOUNT = re.compile(r"{body}")\n{dispatch}', encoding="utf-8")


def ledger_with(repo, output=""):
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"), touched=["parser.py"])
    if output:
        led.saw_output("node --test", output)
    return led


# --- the real case, rebuilt ------------------------------------------------

# Exactly the shape that shipped unverified: a TAP counter pattern, written
# from memory of what `node --test` prints.
TAP_PATTERN = r"^\s*#\s*(pass|fail)\s+\d+\s*$"
REAL_TAP = "1..3\n# tests 3\n# pass 2\n# fail 1\n"


def test_a_pattern_the_task_actually_saw_is_silent(repo):
    """Forward. The command was run, the output matched, nothing to say.

    Without this the check could be firing on every pattern ever written, which
    is the same as not having it.
    """
    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, REAL_TAP)
    assert assumptions.unverified(led) == []


def test_a_pattern_nothing_produced_is_named(repo):
    """The day's defect, caught before the agent says done.

    The pattern is written from memory; the command that would confirm it was
    never run. The ledger knows, and until now nobody asked it.
    """
    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, "Ran 3 checks, all good.\n")     # something else entirely
    found = assumptions.unverified(led)
    assert found == [TAP_PATTERN], found
    assert "run the thing and look" in " ".join(assumptions.wording(found, []))


def test_a_pattern_written_before_the_command_ran_is_still_verified(repo):
    """Order must not matter: looking first is the behaviour to encourage.

    The output is kept, so a pattern written after the command - or before it -
    is confirmed the same way. Checking only as output flowed past would have
    punished exactly the habit this is meant to reward.
    """
    led = ledger_with(repo, REAL_TAP)
    add_pattern(repo, TAP_PATTERN)                            # written afterwards
    assert assumptions.unverified(led) == []


# --- adversarial ------------------------------------------------------------

def test_running_nothing_at_all_is_not_an_accusation(repo):
    """Silence, not a complaint, when there is no evidence either way.

    A task that ran no commands cannot have confirmed anything, and saying "none
    of your patterns are verified" there is an accusation dressed as a finding.
    """
    add_pattern(repo, TAP_PATTERN)
    assert assumptions.unverified(ledger_with(repo)) == []


def test_a_pattern_matching_the_empty_string_is_never_reported(repo):
    """This module shipped one of these, so it is not hypothetical.

    `(?:x)?` matches every output ever captured, so it is confirmed by anything
    and cannot be reported. A guard skipping such patterns early was written
    here, and flipping it proved it did nothing - the assertion below holds with
    or without it - so the guard went rather than stay looking load-bearing.
    """
    add_pattern(repo, r"(?:(?:[^\s:]+:){1,2}[ \t]*)?")
    assert assumptions.unverified(ledger_with(repo, "anything at all\n")) == []


def test_ordinary_strings_are_not_patterns(repo):
    """A message is not a claim about text, and must not be treated as one."""
    (repo / "parser.py").write_text(
        'MESSAGE = "could not read the configuration file"\n'
        'NAME = "typescript"\n', encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated output\n")) == []


def test_a_comment_is_not_a_claim(repo):
    """Adversarially: sample output pasted into a docstring is documentation."""
    (repo / "parser.py").write_text(
        '# the runner prints "^\\s*#\\s*(pass|fail)\\s+\\d+$" at the end\n'
        "VALUE = 1\n", encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated output\n")) == []


def test_an_unparseable_pattern_is_skipped_rather_than_guessed(repo):
    """Half-written code is not a finding."""
    (repo / "parser.py").write_text('BROKEN = "^(unclosed[\\d+"\n', encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated\n")) == []


# --- the vacuous probe, computed -------------------------------------------

def test_a_new_test_that_passes_on_the_base_tree_is_named(repo):
    """Four of these shipped in one day, caught only by flipping them by hand.

    `core/stress.py` already knows which tests were red on the base commit. A
    test the task added which is not among them ran green against code that did
    not contain the change.
    """
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_new.py", "parser.py"],
                 discrimination={"tests": "yes"},
                 failed_before=["tests/test_other.py::test_thing"],
                 passed_before=["tests/test_new.py::test_it"])
    assert assumptions.vacuous_tests(led) == ["tests/test_new.py"]
    assert "did not test this change" in " ".join(
        assumptions.wording([], ["tests/test_new.py"]))


def test_a_new_test_that_failed_on_the_base_tree_is_silent(repo):
    """Forward: red there, green here, which is the reproduction it should be."""
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_new.py"],
                 discrimination={"tests": "yes"},
                 failed_before=["tests/test_new.py::test_it"])
    assert assumptions.vacuous_tests(led) == []


def test_without_a_base_tree_run_nothing_is_claimed(repo):
    """Adversarially: no run, no accusation.

    The base tree may not have been asked at all - no declared command, no base
    commit, a runner that could not start. Reporting every new test as vacuous
    there would be the loudest possible way to say nothing.
    """
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 touched=["tests/test_new.py"])
    assert assumptions.vacuous_tests(led) == []

    asked = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                   base=git(repo, "rev-parse", "HEAD"),
                   touched=["tests/test_new.py"],
                   discrimination={"tests": "yes"}, failed_before=[])
    assert assumptions.vacuous_tests(asked) == [], (
        "nothing red on base is already reported as a discrimination verdict")

    # And the state the gate itself exists for, which neither case above
    # reaches: a ledger carrying red tests left from some earlier run, with no
    # base and no verdict of its own. Flipping the gate showed both cases above
    # passed without it; this is the one that makes it load-bearing.
    stale = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                   touched=["tests/test_new.py"],
                   failed_before=["tests/test_other.py::test_thing"])
    assert assumptions.vacuous_tests(stale) == [], (
        "accused a test without having asked the base tree in this task")


# --- available at step 7, pulled rather than pushed -------------------------

def test_an_unverified_pattern_is_visible_on_demand(repo):
    """Forward. The same fact as the end report, askable while it still helps.

    The median decisive error lands at step 7 of 27 and the recovery window is
    one step, so a fact only available at step 27 arrives after the run is
    already built on it. `ep_status` is the pull surface that already exists for
    exactly this reason.
    """
    from core.status import render

    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, "All files pass linting.\n")
    led.save()

    said = render(repo)
    assert "unchecked" in said, said
    assert "matched nothing you ran" in said, said


def test_a_verified_pattern_adds_no_section_at_all(repo):
    """Adversarial, and the one that keeps this usable.

    A status page that always carries an `unchecked` heading trains the reader
    to skip it. Nothing to say means nothing said - not an empty section.
    """
    from core.status import render

    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, REAL_TAP)
    led.save()
    assert "unchecked" not in render(repo)


def test_nothing_is_ever_injected_into_the_loop(repo):
    """Adversarial, and a measured decision rather than a stylistic one.

    A critic with AUROC 0.94 caused a 26 percentage point collapse when allowed
    to intervene, helping only where runs were already failing and harming ones
    that were succeeding (arXiv:2602.03338). This project blocked 75% of runs
    once on an unmeasured signal. So the check must reach `ep_status` and the
    end report, and must NOT reach a hook that speaks mid-trajectory.
    """
    from pathlib import Path

    hook = Path(__file__).resolve().parents[1] / "core" / "hook.py"
    source = hook.read_text(encoding="utf-8")
    assert "unverified(" not in source, (
        "an assumption check reached a mid-trajectory hook; "
        "intervening on a healthy run is measured to cost up to 26pp")
    assert "vacuous_tests(" not in source


# --- the narrowing: a pattern is not always a claim about a command ---------

# Most regexes in most repositories describe *data*, not a tool: an email
# validator, a phone format, a scrape of fetched HTML. No command will ever
# print something that matches them, so before §7c every one was reported on
# every run - and on a scraper or a client library that is most of the file.
VALIDATORS = r'''import re

EMAIL = re.compile(r"^[^@]+@[^@]+\.[a-z]{2,}$")
PHONE = re.compile(r"^\+?[0-9]{7,15}$")
'''


def test_a_validation_regex_in_a_file_naming_no_tool_is_silent(repo):
    """Adversarial. The check must not be a noise generator on ordinary code."""
    (repo / "validate.py").write_text(VALIDATORS, encoding="utf-8")
    led = ledger_with(repo, REAL_TAP)
    led.touched = ["validate.py"]
    assert assumptions.unverified(led) == []


def test_the_silence_is_caused_by_the_narrowing_and_not_by_nothing(repo):
    """The same file, with the narrowing removed, must be loud.

    Without this the test above passes whether the feature works or not - which
    is precisely the vacuous probe `vacuous_tests` was written to catch.
    """
    (repo / "validate.py").write_text(VALIDATORS, encoding="utf-8")
    base = git(repo, "rev-parse", "HEAD")
    loud = assumptions.patterns_added(repo, base, ["validate.py"], None)
    assert len(loud) == 2, loud


def test_a_tool_named_in_a_different_file_does_not_vouch(repo):
    """Adversarial. Attribution is per file, not pooled across the diff."""
    add_pattern(repo, TAP_PATTERN)
    (repo / "validate.py").write_text(VALIDATORS, encoding="utf-8")
    led = ledger_with(repo, "nothing that matches\n")
    led.touched = ["parser.py", "validate.py"]
    found = assumptions.unverified(led)
    assert TAP_PATTERN in found
    assert not [p for p in found if "@" in p], found


def test_an_escape_does_not_hide_the_tool_name():
    r"""`r"\bnode\s+--test\b"` names node, and a naive word boundary says no.

    The character before `node` there is the `b` of `\b`. The first version of
    this check used a plain lookbehind and went silent on `core/parsers.py` -
    the single file the whole feature was built for. Found by running it.
    """
    assert assumptions._names_a_tool([r'if re.search(r"\bnode\s+--test\b", cmd):'],
                                     {"node"})


def test_the_launcher_is_not_the_tool():
    """`python -m pytest` is a claim about pytest.

    Keeping `python` would let the word in any docstring vouch for every regex
    in the file that contains it, which is the narrowing undone.
    """
    assert assumptions._tool_names(["python -m pytest tests/ -q"]) >= {"pytest"}
    assert "python" not in assumptions._tool_names(["python -m pytest tests/ -q"])
    assert assumptions._tool_names(["node --test"]) == {"node"}
    assert "test" not in assumptions._tool_names(["npm test"])
    assert assumptions._tool_names([]) == set()


def test_a_pattern_in_a_file_the_task_created_is_not_invisible(repo):
    """`git diff base -- path` says nothing at all about an untracked file.

    So every pattern in every *new* module was exempt, silently - including the
    module that shipped with this narrowing. The whole file is what the task
    added, and it is read as such. Found by a flip control, not by reading it.
    """
    (repo / "runner.py").write_text(
        'import re\n'
        'def read(cmd):\n'
        '    if cmd.startswith("node --test"):\n'
        f'        return re.search(r"{TAP_PATTERN}", cmd)\n', encoding="utf-8")
    led = ledger_with(repo, "Ran 3 checks, all good.\n")
    led.touched = ["runner.py"]
    assert assumptions.unverified(led) == [TAP_PATTERN]


CODE_FIXTURES = [
    "def read(cmd):",
    "self.token_count = len(tokens)",
    "def secret_santa(names):",
    "if cmd.startswith('node --test'):",
]


@pytest.mark.parametrize("fixture", CODE_FIXTURES)
def test_source_code_in_a_string_is_not_a_pattern(repo, fixture):
    """Counting metacharacters alone reports test fixtures holding code.

    Found by pointing the check at its own diff: brackets and parentheses are
    what *source* is made of, so a fixture like `def secret_santa(names):` read
    as a claim about some tool's output. A literal must also contain a construct
    only a regex has. Measured against all 62 compiled patterns in `core/`
    before adopting: none is lost.
    """
    (repo / "runner.py").write_text(
        f'SAMPLE = "{fixture}"\nif cmd.startswith("node --test"):\n    pass\n',
        encoding="utf-8")
    led = ledger_with(repo, "nothing matching\n")
    led.touched = ["runner.py"]
    assert assumptions.unverified(led) == []


def test_the_strong_rule_keeps_every_real_pattern_in_this_repo():
    """The forward control on the narrowing above, run against real code.

    A rule that silences noise by silencing everything is the failure mode here,
    so it is measured rather than trusted: every regex this project actually
    compiles must still read as one.
    """
    import ast
    from pathlib import Path

    real = []
    for path in sorted(Path("core").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            called = node.func
            if not (isinstance(called, ast.Attribute) and called.attr == "compile"):
                continue
            # `a + b` and implicit concatenation both arrive as one expression;
            # take every string constant in it, which is how the module itself
            # reads a pattern built in pieces.
            real += [n.value for n in ast.walk(node.args[0])
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert len(real) > 40, f"the extractor stopped working: {len(real)}"
    lost = [p for p in real if not assumptions.STRONG.search(p)]
    assert lost == [], lost


TOOL_SHAPES = [
    ("node --test", {"node"}),
    ("python -m pytest tests/test_redact.py -q", {"pytest"}),
    ("git status --porcelain", {"git"}),
    ("turbo test", {"turbo"}),
    ("npm run build", {"npm"}),
    ("npx tsc --noEmit", {"tsc"}),
    ("go test ./...", {"go"}),
    ("bundle exec rspec", {"rspec"}),
    ("cargo test", {"cargo"}),
    ("python", {"python"}),
]


@pytest.mark.parametrize("command,expected", TOOL_SHAPES, ids=[c for c, _ in TOOL_SHAPES])
def test_the_tool_is_the_first_real_token(command, expected):
    """Ten runner shapes, read rather than remembered.

    Every one of these was run through the function before being written down,
    and two were wrong: `go test` returned nothing because a two-letter name was
    below the length floor, and `bundle exec rspec` returned bundle - the same
    launcher idiom as npx. Both are in the table above precisely so they stay
    fixed.
    """
    assert assumptions._tool_names([command]) == expected
