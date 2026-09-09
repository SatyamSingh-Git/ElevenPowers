"""The test that would have caught the class of defect this phase was about.

Twice now a piece of this project was correct, unit-tested, and never called,
because the subscription that was supposed to deliver its events did not cover
them. No test of a handler can find that: the handler works. What was missing
was a test of the join between the runtime and its host.
"""

import json
from pathlib import Path

import pytest

from core import hook, wiring
from core.doctor import checks

HOOKS_JSON = Path(__file__).resolve().parents[1] / "plugin" / "hooks" / "hooks.json"


def test_the_checked_in_subscription_matches_the_runtime():
    assert json.loads(HOOKS_JSON.read_text(encoding="utf-8")) == wiring.hooks_json()


def test_every_subscribed_event_has_a_handler():
    assert set(wiring.EVENTS) == set(hook.HANDLERS)


def test_every_handler_is_reachable_by_name():
    for name in hook.HANDLERS.values():
        assert callable(getattr(hook, name))


@pytest.mark.parametrize("tool", wiring.RECORDED)
def test_every_recorded_tool_is_delivered_to_post_tool_use(tool):
    assert tool in wiring.EVENTS["PostToolUse"].split("|")


@pytest.mark.parametrize("tool", wiring.GUARDED)
def test_every_guarded_tool_is_delivered_to_pre_tool_use(tool):
    assert tool in wiring.EVENTS["PreToolUse"].split("|")


def test_failing_commands_are_subscribed_separately():
    """A failing tool call raises its own event, and that is the one that matters."""
    assert "PostToolUseFailure" in wiring.EVENTS
    assert "Bash" in wiring.EVENTS["PostToolUseFailure"].split("|")


def test_the_doctor_passes_on_a_healthy_checkout(tmp_path):
    failing = [c.name for c in checks(tmp_path) if not c.ok]
    assert not failing


def test_the_doctor_notices_a_drifted_subscription(tmp_path):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
    failed = [c for c in checks(tmp_path, plugin=tmp_path) if not c.ok]
    assert any("hooks.json" in c.name for c in failed)
