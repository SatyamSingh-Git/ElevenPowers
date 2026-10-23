"""The rehearsal accepts a sound case and names the check a broken one fails."""
import json
import shutil

import pytest

from eval.multistage_rehearse import main, rehearse
from tests.multistage_fixture import make_case


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return make_case(tmp_path_factory.mktemp("multistage"))


def _copy(built, tmp_path):
    return shutil.copytree(built, tmp_path / "fixture")


def test_the_fixture_rehearses_usable(built, tmp_path):
    report = rehearse(_copy(built, tmp_path), tmp_path / "work")
    assert report["usable"], [s for s in report["stages"] if not all(s["checks"].values())]
    assert [s["stage"] for s in report["stages"]] == list(range(7))


def _edit_json(path, change):
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def _wrong_group(case):
    (case / "oracle" / "groups" / "default_2.py").write_text(
        "from pkg import core\n\n\ndef test_default():\n    assert core.DEFAULT == 99\n", encoding="utf-8")


def _docs_disagree(case):
    _edit_json(case / "oracle" / "facts.json", lambda v: v["2"].update(default="9"))


def _fact_never_documented(case):
    _edit_json(case / "oracle" / "facts.json", lambda v: [v[n].update(phantom="1") for n in ("2", "3")])


def _protected_is_edited(case):
    _edit_json(case / "case.json", lambda v: v.update(protected="src/pkg/core.py"))


def _dependent_changes_nothing(case):
    (case / "stages" / "2" / "dependent-missed.diff").write_bytes(b"")


def _new_group_already_passes(case):
    (case / "oracle" / "groups" / "default_3.py").write_text("def test_default():\n    pass\n", encoding="utf-8")


@pytest.mark.parametrize("breaks, stage, check", [
    (_wrong_group, 2, "reference_groups"),
    (_docs_disagree, 2, "reference_docs"),
    (_protected_is_edited, 1, "reference_rules"),
    (_dependent_changes_nothing, 2, "dependent_missed"),
    (_fact_never_documented, 3, "docs_forgotten"),
    (_new_group_already_passes, 3, "no_op"),
])
def test_a_broken_case_is_unusable(built, tmp_path, breaks, stage, check):
    case = _copy(built, tmp_path)
    breaks(case)
    report = rehearse(case, tmp_path / "work")
    assert not report["usable"]
    assert report["stages"][stage]["checks"][check] is False


def test_the_command_writes_its_report_and_fails_on_an_unusable_case(built, tmp_path):
    cases = tmp_path / "cases"
    shutil.copytree(built, cases / "fixture")
    out = tmp_path / "rehearsal.json"
    assert main(["--cases", str(cases), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["fixture"]["usable"] is True
    _new_group_already_passes(cases / "fixture")
    assert main(["--cases", str(cases), "--case", "fixture", "--out", str(out)]) == 1
