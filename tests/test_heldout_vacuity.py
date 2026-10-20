"""VACUOUS as B7/B9 measured it: the tree's own tests cannot tell the patch from its absence."""
import difflib
import sys


def _base(root):
    # LF, as `git archive` writes a checkout; text mode on Windows hid a newline defect.
    (root / "pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf8", newline="\n")
    (root / "pkg" / "mod.py").write_text("def value():\n    return 1\n", encoding="utf8", newline="\n")
    (root / "tests" / "test_mod.py").write_text("from pkg.mod import value\n\n\ndef test_int():\n    assert isinstance(value(), int)\n",
                                                 encoding="utf8", newline="\n")
    return root


def _diff(path, before, after):
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), f"a/{path}", f"b/{path}"))


SOURCE = _diff("pkg/mod.py", "def value():\n    return 1\n", "def value():\n    return 2\n")
PINNING_TEST = "".join(difflib.unified_diff([], ["from pkg.mod import value\n", "\n", "\n", "def test_two():\n", "    assert value() == 2\n"],
                                            "/dev/null", "b/tests/test_two.py"))


def _check(tmp_path, patch):
    from eval.heldout_vacuity import vacuity
    return vacuity(_base(tmp_path / "base"), patch, python=sys.executable, env={"PYTHONPATH": "."},
                   test_dir="tests", work=tmp_path / "work")


def test_a_change_its_own_test_pins_is_not_vacuous(tmp_path):
    assert _check(tmp_path, SOURCE + PINNING_TEST) == {"vacuous": False, "reason": "revert killed"}


def test_a_change_no_test_can_detect_is_vacuous(tmp_path):
    assert _check(tmp_path, SOURCE) == {"vacuous": True, "reason": "revert survived"}


def test_a_patch_without_source_changes_is_not_scored(tmp_path):
    assert _check(tmp_path, PINNING_TEST)["vacuous"] is None


def test_a_patch_that_does_not_apply_is_not_scored(tmp_path):
    assert _check(tmp_path, _diff("pkg/missing.py", "x\n", "y\n")) == {"vacuous": None, "reason": "patch did not apply"}


def test_a_pinning_assertion_added_to_an_existing_test_file_is_kept_through_the_revert(tmp_path):
    before = "from pkg.mod import value\n\n\ndef test_int():\n    assert isinstance(value(), int)\n"
    after = before + "\n\ndef test_two():\n    assert value() == 2\n"
    assert _check(tmp_path, SOURCE + _diff("tests/test_mod.py", before, after)) == {"vacuous": False, "reason": "revert killed"}


def test_an_already_red_test_is_deselected_rather_than_counted_as_a_kill(tmp_path):
    from eval.heldout_vacuity import vacuity
    base = _base(tmp_path / "base")
    (base / "tests" / "test_broken.py").write_text("def test_broken():\n    assert False\n", encoding="utf8", newline="\n")
    value = vacuity(base, SOURCE, python=sys.executable, env={"PYTHONPATH": "."}, test_dir="tests", work=tmp_path / "work")
    assert value == {"vacuous": True, "reason": "revert survived"}


def test_a_suite_that_notices_a_no_op_edit_is_not_scored(tmp_path):
    from eval.heldout_vacuity import vacuity
    base = _base(tmp_path / "base")
    (base / "tests" / "test_noop.py").write_text(
        "import pkg.mod\n\n\ndef test_untouched():\n    assert not hasattr(pkg.mod, '_ep_probe_noop')\n", encoding="utf8", newline="\n")
    value = vacuity(base, SOURCE, python=sys.executable, env={"PYTHONPATH": "."}, test_dir="tests", work=tmp_path / "work")
    assert value == {"vacuous": None, "reason": "survive control failed"}
