"""Multi-stage v2 cases: the format is enforced and every stage tree can be rebuilt."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from eval.multistage_cases import load, tree
from tests.multistage_fixture import make_case, make_v3_case

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


def test_v2_cases_load_as_v2_and_the_v3_fixture_as_v3(tmp_path):
    assert load(make_case(tmp_path / "two"))["profile"] == "v2"
    case = load(make_v3_case(tmp_path / "three"))
    assert case["profile"] == "v3" and len(case["stages"]) == 8


def _quiet(n, change):
    return lambda case: _edit_json(case / "case.json", lambda v: change(v["stages"][n - 1]["quiet"][0]))


V3_BREAKS = {
    "7 stages": lambda case: _edit_json(case / "case.json", lambda v: v["stages"].pop()),
    "cross-cutting": lambda case: _edit_json(case / "case.json", lambda v: v["stages"][4].update(kind="self-contained")),
    "bug fix": lambda case: _edit_json(case / "case.json", lambda v: v["stages"][5].update(bugfix=False)),
    "quiet dependent": lambda case: _edit_json(case / "case.json", lambda v: v["stages"][1].pop("quiet")),
    "kind": _quiet(2, lambda q: q.update(kind="hidden")),
    "kinds": lambda case: _edit_json(case / "case.json", lambda v: [s["quiet"][0].update(kind="copy")
                                                                     for s in v["stages"] if "quiet" in s]),
    "fails": _quiet(2, lambda q: q.update(fails=["default_3"])),
    "no fails": _quiet(2, lambda q: q.update(fails=[])),
    "diff": lambda case: (case / "stages" / "3" / "quiet-0.diff").unlink(),
    "touches": _quiet(2, lambda q: q.update(file="src/pkg/core.py")),
}


@pytest.mark.parametrize("rule", V3_BREAKS)
def test_each_v3_rule_is_refused(tmp_path, rule):
    case = make_v3_case(tmp_path)
    V3_BREAKS[rule](case)
    with pytest.raises(ValueError, match=rule):
        load(case)


def test_the_quiet_variant_reverts_only_the_dependent(tmp_path):
    case = load(make_v3_case(tmp_path))
    reference, quiet = tree(case, 2, tmp_path / "reference"), tree(case, 2, tmp_path / "quiet", "quiet")
    differ = sorted(p.relative_to(quiet).as_posix() for p in quiet.rglob("*")
                    if p.is_file() and p.read_bytes() != (reference / p.relative_to(quiet)).read_bytes())
    assert differ == ["src/pkg/parse.py"] and "SEP_IN = ';'" in _read(quiet, "src/pkg/parse.py")
    with pytest.raises(ValueError):
        tree(case, 6, tmp_path / "self", "quiet")


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
