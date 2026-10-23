"""Every state a held-out run's edits passed through, replayed from its transcript."""
import json

import pytest

from eval.heldout_checkpoints import better, change, edits

WORK = "E:\\batch\\slot\\work"


def _transcript(*events):
    return "\n".join(json.dumps(event) for event in events)


def _use(id, name, **input):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": id, "name": name, "input": input}]}}


def _result(id, error=None):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": id, "is_error": error,
                                                     "content": "done"}]}}


def test_successful_edits_inside_the_workspace_are_kept_in_order():
    transcript = _transcript(
        {"type": "system", "subtype": "init", "cwd": WORK},
        _use("1", "Edit", file_path=WORK + "\\src\\a.py", old_string="x", new_string="y", replace_all=False),
        _result("1"),
        _use("2", "Write", file_path="C:\\Temp\\scratch.py", content="print()"),
        _result("2"),
        _use("3", "Edit", file_path=WORK + "\\tests\\t.py", old_string="a", new_string="b", replace_all=False),
        _result("3", error=True),
        _use("4", "Bash", command="pytest"),
        _result("4"),
        _use("5", "Write", file_path=WORK + "\\src\\new.py", content="z = 1\n"),
        _result("5"),
    )
    assert [(path, step["name"]) for path, step in edits(transcript)] == [("src/a.py", "Edit"), ("src/new.py", "Write")]


def test_an_edit_replaces_one_occurrence_or_every_one(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x = 1\nx = 1\n")
    change(tmp_path, "a.py", {"name": "Edit", "input": {"old_string": "x = 1\nx", "new_string": "y = 2\nx",
                                                        "replace_all": False}})
    assert (tmp_path / "a.py").read_bytes() == b"y = 2\nx = 1\n"
    change(tmp_path, "a.py", {"name": "Edit", "input": {"old_string": "= ", "new_string": "== ", "replace_all": True}})
    assert (tmp_path / "a.py").read_bytes() == b"y == 2\nx == 1\n"


def test_an_edit_to_a_crlf_file_keeps_its_line_endings(tmp_path):
    (tmp_path / "a.py").write_bytes(b"a = 1\r\nb = 2\r\n")
    change(tmp_path, "a.py", {"name": "Edit", "input": {"old_string": "a = 1\nb", "new_string": "a = 3\nb",
                                                        "replace_all": False}})
    assert (tmp_path / "a.py").read_bytes() == b"a = 3\r\nb = 2\r\n"


def test_a_write_creates_the_file_and_its_folders(tmp_path):
    change(tmp_path, "pkg/new.py", {"name": "Write", "input": {"content": "z = 1\n"}})
    assert (tmp_path / "pkg" / "new.py").read_bytes() == b"z = 1\n"


def test_an_edit_that_no_longer_matches_is_an_error_not_a_silent_skip(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x = 1\n")
    with pytest.raises(ValueError):
        change(tmp_path, "a.py", {"name": "Edit", "input": {"old_string": "missing", "new_string": "y",
                                                            "replace_all": False}})


def test_trees_that_differ_only_in_line_endings_are_the_same_candidate(tmp_path):
    from eval.heldout_checkpoints import same_files
    a, b = tmp_path / "a", tmp_path / "b"
    for root, body in ((a, b"x = 1\ny = 2\n"), (b, b"x = 1\r\ny = 2\r\n")):
        (root / "src").mkdir(parents=True)
        (root / "src" / "m.py").write_bytes(body)
    assert same_files(a, b, ["src/m.py", "src/gone.py"])
    (b / "src" / "m.py").write_bytes(b"x = 1\r\ny = 3\r\n")
    assert not same_files(a, b, ["src/m.py"])
    (b / "src" / "gone.py").write_bytes(b"")
    (b / "src" / "m.py").write_bytes(b"x = 1\ny = 2\n")
    assert not same_files(a, b, ["src/m.py", "src/gone.py"])


def test_the_files_a_patch_touches_are_read_from_its_headers():
    from eval.heldout_checkpoints import touched
    patch = ("diff --git a/src/m.py b/src/m.py\nindex 1..2 100644\n--- a/src/m.py\n+++ b/src/m.py\n"
             "diff --git a/tests/new.py b/tests/new.py\nnew file mode 100644\n")
    assert touched(patch) == {"src/m.py", "tests/new.py"}


def test_a_state_is_graded_in_a_folder_that_exists(tmp_path, monkeypatch):
    # materialise writes the task's archive beside the tree it builds.
    from types import SimpleNamespace
    from eval import heldout_checkpoints as c

    def grade_patch(task, patch, work):
        assert work.parent.is_dir()
        return SimpleNamespace(resolved=False, outcome="unfixed")

    monkeypatch.setattr(c, "grade_patch", grade_patch)
    assert c.grade(None, "", tmp_path / "state-0") == ("unfixed", None)


@pytest.mark.parametrize("states, final, expected", [
    ([("resolved", False), ("unfixed", None)], ("unfixed", None), True),
    ([("resolved", True), ("resolved", False)], ("resolved", False), False),
    ([("resolved", False), ("resolved", True)], ("resolved", True), True),
    ([("regressed", None), ("resolved", True)], ("resolved", True), False),
    ([("unfixed", None)], ("regressed", None), False),
])
def test_a_better_state_is_one_that_resolved_and_was_pinned_where_the_final_was_not(states, final, expected):
    assert better(states, final) is expected
