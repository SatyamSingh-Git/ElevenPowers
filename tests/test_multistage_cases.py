"""Multi-stage v2 cases: the format is enforced and every stage tree can be rebuilt."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from eval.multistage_cases import load, tree
from tests.multistage_fixture import make_case

ROOT = Path(__file__).resolve().parents[1]


def test_the_fixture_case_loads(tmp_path):
    assert load(make_case(tmp_path))["id"] == "fixture"


def _edit_json(path, change):
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def _forbidden_word(case):
    _edit_json(case / "case.json", lambda v: v["stages"][0].update(request="Update the docs too."))


def _too_few_cross_cutting(case):
    _edit_json(case / "case.json", lambda v: v["stages"][1].update(kind="self-contained"))


def _missing_group(case):
    (case / "oracle" / "groups" / "use.py").unlink()


def _fact_unchanged(case):
    _edit_json(case / "oracle" / "facts.json", lambda v: v.update({"3": v["2"]}))


def _no_dependent_variant(case):
    (case / "stages" / "2" / "dependent-missed.diff").unlink()


def _bad_window(case):
    _edit_json(case / "case.json", lambda v: v["stages"][0].update(dependent_missed_fails=["default_1"]))


def _three_groups_in_a_stage(case):
    (case / "oracle" / "groups" / "third.py").write_text("def test_third():\n    pass\n", encoding="utf-8")
    _edit_json(case / "case.json", lambda v: v["groups"].append({"id": "third", "since": 3, "until": 3}))


@pytest.mark.parametrize("breaks", [_forbidden_word, _too_few_cross_cutting, _missing_group, _fact_unchanged,
                                    _no_dependent_variant, _bad_window, _three_groups_in_a_stage])
def test_each_rule_is_refused(tmp_path, breaks):
    case = make_case(tmp_path)
    breaks(case)
    with pytest.raises(ValueError):
        load(case)


def _read(root, rel):
    return (root / rel).read_text(encoding="utf-8")


def test_trees_differ_by_variant(tmp_path):
    case = load(make_case(tmp_path))
    reference = tree(case, 2, tmp_path / "reference")
    assert "DEFAULT = 2" in _read(reference, "src/pkg/core.py")
    assert "| `default` | `2` |" in _read(reference, "docs/reference.md")
    assert "DEFAULT = 1" in _read(tree(case, 2, tmp_path / "no-op", "no-op"), "src/pkg/core.py")
    forgotten = tree(case, 2, tmp_path / "forgotten", "docs-forgotten")
    assert "DEFAULT = 2" in _read(forgotten, "src/pkg/core.py")
    assert "| `default` | `1` |" in _read(forgotten, "docs/reference.md")
    missed = tree(case, 2, tmp_path / "missed", "dependent-missed")
    assert "scaled_v1" in _read(missed, "src/pkg/use.py") and "scaled_v2" in _read(missed, "src/pkg/core.py")
    assert "DEFAULT = 0" in _read(tree(case, 0, tmp_path / "start"), "src/pkg/core.py")


def test_a_dependent_variant_on_a_self_contained_stage_is_refused(tmp_path):
    case = load(make_case(tmp_path))
    with pytest.raises(ValueError):
        tree(case, 5, tmp_path / "x", "dependent-missed")


def test_case_projects_are_never_collected(tmp_path):
    probe = ROOT / "eval" / "multistage_cases" / "_probe"
    try:
        shutil.copytree(make_case(tmp_path) / "start", probe)
        done = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                               "eval/multistage_cases"], cwd=ROOT, capture_output=True, text=True)
        assert "test_core.py" not in done.stdout, done.stdout
        assert done.returncode == 5, done.stdout + done.stderr
    finally:
        shutil.rmtree(probe, ignore_errors=True)
