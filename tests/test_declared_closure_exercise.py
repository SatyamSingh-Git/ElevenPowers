"""Actual Python/Node checks through the real launchers; no model sessions."""
import shutil

import pytest

NATIVE = {"declared": ["ABSENT", "ABSENT", "CURRENT", "STALE", "FAILED", "INCOMPLETE"],
          "delivery": "emitted", "followups": ["current", "failed", "incomplete"]}
REPLAY = {**NATIVE, "delivery": "intent", "followups": ["no-emission"] * 3}


@pytest.mark.parametrize("language", ["python", "javascript"])
@pytest.mark.parametrize("mode", ["native-control", "replay"])
def test_closure_exercise_keeps_declared_states_and_delivery_stages_apart(tmp_path, language, mode):
    from eval.declared_closure import case
    if language == "javascript" and not shutil.which("node"):
        pytest.skip("Node unavailable")

    value = case(tmp_path / "case", "claude", language, mode)

    expected = NATIVE if mode == "native-control" else REPLAY
    assert value["declared"] == expected["declared"]
    assert value["delivery_after_generic"] == expected["delivery"]
    assert value["followups"] == expected["followups"]
    assert value["model_consumption"] == "unproven" and value["model_calls"] == 0
    assert value["qualified"], value["requirements"]


@pytest.mark.parametrize("host", ["codex", "gemini", "cursor", "copilot"])
def test_closure_exercise_runs_through_every_host_adapter(tmp_path, host):
    from eval.declared_closure import case

    value = case(tmp_path / "case", host, "python", "native-control")

    assert value["followups"] == NATIVE["followups"]
    assert value["qualified"], value["requirements"]


def test_closure_exercise_refuses_an_existing_destination(tmp_path):
    from eval.declared_closure import exercise

    (tmp_path / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="new"):
        exercise(tmp_path)
    assert (tmp_path / "keep.txt").read_text() == "keep"
