"""eval/reverted.py: does recorded passing evidence discriminate on the corpus?

Every fixture is a real repository, a real patch and a real pytest run, in
both directions: a check that fails without the change, one that passes
anyway, and the cases that must not be read as either.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from eval import reverted
from eval.live import environment

BUGGY = {"src/calc.py": "def add(a, b):\n    return a - b\n"}
FIXED = {"src/calc.py": "def add(a, b):\n    return a + b\n"}
AGENT_SHAPED = 'cd "C:/Users/x/AppData/Local/Temp/tmpab12cd" && python -m pytest tests -q 2>&1 | tail -20'


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _bundle(tmp_path: Path, patched: dict[str, str], commands=(AGENT_SHAPED,), tools=None,
            base=BUGGY) -> Path:
    repo = tmp_path / "repo"
    for rel, body in base.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    for rel, body in patched.items():
        if body is None:
            (repo / rel).unlink()
            continue
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    _git(repo, "add", "-A")
    patch = subprocess.run(["git", "diff", "--cached", "--binary", base], cwd=repo,
                           capture_output=True, check=True).stdout

    bundle = tmp_path / "bundles" / "demo--gate--1"
    bundle.mkdir(parents=True)
    manifest = {"task": "demo", "base": {"repo": str(repo), "base": base}, "env": {"PYTHONPATH": "src"}}
    if tools is not None:
        manifest["environment"] = {"tools": tools}
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (bundle / "patch.diff").write_bytes(patch)
    evidence = [{"kind": "test_suite", "result": "pass", "command": c, "passed": 1, "failed": 0,
                 "counted": True} for c in commands]
    (bundle / "ledger.json").write_text(json.dumps({"evidence": evidence}), encoding="utf-8")
    return bundle


def _only(rows):
    assert len(rows) == 1, rows
    return rows[0]


@pytest.mark.parametrize("recorded, runnable", [
    (AGENT_SHAPED, "python -m pytest tests -q"),
    ('cd "C:/t/tmp1" && python -m pytest tests/test_a.py -k "x and not y" -q 2>&1', 'python -m pytest tests/test_a.py -k "x and not y" -q'),
    ("python -m pytest tests -q", "python -m pytest tests -q"),
])
def test_an_agent_shaped_command_is_reduced_to_the_check_it_ran(recorded, runnable):
    assert reverted.runnable(recorded) == (runnable, "")


@pytest.mark.parametrize("recorded", [
    "python - <<'EOF'\nopen('tests/x.py', 'w').write('')\nEOF",
    "python -m pytest tests -q > out.txt",
    "python -m pytest tests -q; rm -rf src",
    'cd "C:/t/tmp1" && pip install -e . && python -m pytest tests -q',
    "python -m pytest C:/Users/x/AppData/Local/Temp/tmpab12cd/tests -q",
    "python -m pytest --version",
    "ruff check .",
    "python -m pytest tests -q $(cat extra)",
])
def test_a_command_that_could_write_or_cannot_be_relocated_is_not_rerun(recorded):
    check, why = reverted.runnable(recorded)
    assert check is None and why


def test_a_check_that_fails_without_the_change_discriminates(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    row = _only(reverted.measure(_bundle(tmp_path, {**FIXED, "tests/test_calc.py": test}), tmp_path / "hold"))
    assert row["verdict"] == reverted.DISCRIMINATES, row
    assert row["how"] == "failing test"


def test_a_check_that_passes_without_the_change_is_vacuous(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 0) == 2\n"
    row = _only(reverted.measure(_bundle(tmp_path, {**FIXED, "tests/test_calc.py": test}), tmp_path / "hold"))
    assert row["verdict"] == reverted.VACUOUS, row


def test_a_test_the_patch_deleted_is_not_left_on_the_old_tree(tmp_path):
    """A red test the agent removed is not part of the check it recorded passing."""
    red_at_base = "from calc import add\n\ndef test_old():\n    assert add(2, 2) == 4\n"
    vacuous = "from calc import add\n\ndef test_new():\n    assert add(2, 0) == 2\n"
    bundle = _bundle(tmp_path, {**FIXED, "tests/test_old.py": None, "tests/test_new.py": vacuous},
                     base={**BUGGY, "tests/test_old.py": red_at_base})
    row = _only(reverted.measure(bundle, tmp_path / "hold"))
    assert row["verdict"] == reverted.VACUOUS, row


def test_a_carried_test_that_cannot_import_the_old_code_discriminates_by_import(tmp_path):
    fixed = {"src/calc.py": FIXED["src/calc.py"] + "\n\ndef mul(a, b):\n    return a * b\n"}
    test = "from calc import mul\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
    row = _only(reverted.measure(_bundle(tmp_path, {**fixed, "tests/test_calc.py": test}), tmp_path / "hold"))
    assert row["verdict"] == reverted.DISCRIMINATES, row
    assert row["how"] == "carried test cannot import the old code"


def test_a_fixture_that_raises_on_the_old_code_is_a_failing_test_not_an_import(tmp_path):
    """pytest prints `ERROR tests/x.py::test_a` for both; only one is a file that did not collect."""
    test = ("import pytest\nfrom calc import add\n\n\n@pytest.fixture\ndef four():\n"
            "    if add(2, 2) != 4:\n        raise RuntimeError('old code')\n    return 4\n\n\n"
            "def test_four(four):\n    assert four == 4\n")
    row = _only(reverted.measure(_bundle(tmp_path, {**FIXED, "tests/test_calc.py": test}), tmp_path / "hold"))
    assert (row["verdict"], row["how"]) == (reverted.DISCRIMINATES, "failing test"), row


def test_an_untouched_file_that_cannot_collect_on_the_old_tree_is_not_credited(tmp_path):
    """Only the patch's own tests may discriminate by import; anything else did not run."""
    fixed = {"src/calc.py": FIXED["src/calc.py"] + "\n\ndef mul(a, b):\n    return a * b\n"}
    untouched = "from calc import mul\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
    passing = "def test_ok():\n    assert True\n"
    bundle = _bundle(tmp_path, {**fixed, "tests/test_calc.py": passing},
                     base={**BUGGY, "tests/test_mul.py": untouched})
    row = _only(reverted.measure(bundle, tmp_path / "hold"))
    assert row["verdict"] == reverted.UNCHECKABLE, row
    assert row["why"].startswith("did not run on the old tree")


def test_a_pass_that_does_not_reproduce_today_is_not_classified(tmp_path):
    """The forward control: drift in the environment must not read as vacuity or as discrimination."""
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 5\n"
    row = _only(reverted.measure(_bundle(tmp_path, {**FIXED, "tests/test_calc.py": test}), tmp_path / "hold"))
    assert row["verdict"] == reverted.UNCHECKABLE
    assert row["why"].startswith("does not reproduce on the patched tree")


def test_a_recorded_toolchain_that_differs_is_refused_without_running(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    tools = {"pytest": {"state": "observed", "version": "0.0.1", "source": "installed_probe"}}
    bundle = _bundle(tmp_path, {**FIXED, "tests/test_calc.py": test}, tools=tools)
    row = _only(reverted.measure(bundle, tmp_path / "hold"))
    assert row["verdict"] == reverted.UNCHECKABLE
    assert row["why"].startswith("toolchain differs")
    assert not (tmp_path / "hold").exists() or not any((tmp_path / "hold").iterdir())


def test_the_toolchain_stratum_is_reported_not_pooled(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    matched = environment()["tools"]
    row = _only(reverted.measure(_bundle(tmp_path / "m", {**FIXED, "tests/test_calc.py": test}, tools=matched),
                                 tmp_path / "hold-m"))
    assert (row["verdict"], row["toolchain"]) == (reverted.DISCRIMINATES, "matched")
    row = _only(reverted.measure(_bundle(tmp_path / "u", {**FIXED, "tests/test_calc.py": test}),
                                 tmp_path / "hold-u"))
    assert (row["verdict"], row["toolchain"]) == (reverted.DISCRIMINATES, "unrecorded")


def test_one_command_recorded_many_times_is_measured_once(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    again = 'cd "C:/t/tmpzz" && python -m pytest tests -q'
    row = _only(reverted.measure(_bundle(tmp_path, {**FIXED, "tests/test_calc.py": test},
                                         commands=(AGENT_SHAPED, again)), tmp_path / "hold"))
    assert row["records"] == 2


def test_the_funnel_keeps_every_record_it_did_not_measure(tmp_path):
    test = "from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"
    bundle = _bundle(tmp_path, {**FIXED, "tests/test_calc.py": test},
                     commands=(AGENT_SHAPED, "ruff check ."))
    ledger = json.loads((bundle / "ledger.json").read_text(encoding="utf-8"))
    ledger["evidence"] += [
        {"kind": "test_suite", "result": "fail", "command": AGENT_SHAPED, "passed": 0, "failed": 1, "counted": True},
        {"kind": "test_suite", "result": "pass", "command": "python -m pytest --version", "passed": 0, "failed": 0, "counted": True},
    ]
    (bundle / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    funnel = reverted.funnel([bundle])
    assert funnel["records"] == 4
    assert funnel["passing"] == 3
    assert funnel["passing test records that ran tests"] == 2
    assert funnel["re-executable"] == 1
    assert funnel["excluded"]["not re-executable: not a pytest run"] == 1
    assert sum(funnel["excluded"].values()) == funnel["records"] - funnel["re-executable"]
