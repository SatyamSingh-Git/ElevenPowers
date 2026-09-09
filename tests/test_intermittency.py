"""When repeated runs are worth demanding, and when they are an insult.

Stability is the most expensive obligation the runtime can ask for: twenty clean
runs of a command the agent must first identify. It was the commonest reason the
gate fired in live runs, and on 566 real bug reports the old rule demanded it of
26 percent of them, triggered by the word "race" inside pasted job adverts and
by "sometimes returns a string longer than the limit", which describes a
completely deterministic bug in conditional language.

Both halves are tested: the cases that must trigger it, and the ones that ruined
it.
"""

import pytest

from core.obligations import Claim, Risk, is_intermittent, obligations_for
from core.surface import Surface

INTERMITTENT = [
    ("fix the intermittent race in login", "names it plainly, and has no word for failure"),
    ("the auth test is flaky", "the one word everyone uses for this"),
    ("this test fails intermittently", ""),
    ("there is a race condition in the worker", ""),
    ("deadlock under load", ""),
    ("the parser is not thread-safe", ""),
    ("the suite sometimes fails and passes on retry", "an adverb, with the evidence for it"),
    ("CI is inconsistent: the build sometimes fails for no reason", ""),
]

DETERMINISTIC = [
    ("truncate(text, limit) sometimes returns a string longer than limit",
     "sometimes means for some inputs, which is every bug"),
    ("an upstream service that sometimes fails before succeeding",
     "the flakiness is in the world; the fix is deterministic"),
    ("the login page is broken", ""),
    ("occasionally users see the wrong avatar", "conditional, not nondeterministic"),
    ("fix the race", "bare race is a word in job adverts and prose"),
    ("create resume for this: Job needs concurrent systems and test automation",
     "pasted content that mentions concurrency"),
    ("the export is slow", ""),
]


@pytest.mark.parametrize("request_text,why", INTERMITTENT,
                         ids=[t[:28] for t, _ in INTERMITTENT])
def test_repeated_runs_are_demanded(request_text, why):
    assert is_intermittent(request_text), why


@pytest.mark.parametrize("request_text,why", DETERMINISTIC,
                         ids=[t[:28] for t, _ in DETERMINISTIC])
def test_repeated_runs_are_not_demanded(request_text, why):
    assert not is_intermittent(request_text), why


def test_the_obligation_follows_the_judgement():
    surface = Surface(tests=True)
    keys = lambda text: {  # noqa: E731
        o.key for o in obligations_for(Claim.BUG_FIXED, Risk.LOW, surface, text)
    }
    assert "stable" in keys("the auth test is flaky")
    assert "stable" not in keys("truncate sometimes returns too long a string")


def test_only_a_bug_fix_can_ask_for_it():
    """A feature request that mentions flakiness is not a flaky-bug task."""
    surface = Surface(tests=True)
    keys = {o.key for o in obligations_for(
        Claim.FEATURE_ADDED, Risk.LOW, surface, "add a retry for the flaky upload")}
    assert "stable" not in keys
