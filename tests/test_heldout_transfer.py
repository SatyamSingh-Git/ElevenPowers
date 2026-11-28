"""Test transfer: a test that pins the agent's change should also pass on the upstream fix."""
import subprocess

from eval import heldout_transfer as t
from tests.test_heldout_grading import _task

BEHAVIOUR = "from pkg.mod import value\n\n\ndef test_two():\n    assert value() == 2\n"
OWN_HELPER = "from pkg.mod import two\n\n\ndef test_helper():\n    assert two() == 2\n"
PINS_NOTHING = "from pkg.mod import value\n\n\ndef test_any():\n    assert value() > -1\n"


def _patch(task, tmp_path, source, tests):
    """The agent's patch: its source and test files, against the task's base."""
    work = tmp_path / "agent"
    subprocess.run(["git", "clone", "-q", task.source["repo"], str(work)], check=True)
    subprocess.run(["git", "-C", str(work), "checkout", "-q", task.source["base"]], check=True)
    (work / "pkg" / "mod.py").write_text(source, encoding="utf8")
    for name, body in tests.items():
        (work / "test" / name).write_text(body, encoding="utf8")
    subprocess.run(["git", "-C", str(work), "add", "-A"], check=True)
    return subprocess.run(["git", "-C", str(work), "diff", "--cached", task.source["base"]],
                          capture_output=True, text=True, check=True).stdout


def test_a_patch_splits_into_its_test_files_and_the_rest(tmp_path):
    task, _ = _task(tmp_path)
    patch = _patch(task, tmp_path, "def value():\n    return 2\n", {"test_agent.py": BEHAVIOUR})
    tests, files = t.split(patch)
    assert files == ["test/test_agent.py"] and "pkg/mod.py" not in tests and "test_two" in tests


def test_passed_reads_only_the_ids_pytest_reports_passed():
    output = ("PASSED test/test_a.py::test_x\nFAILED test/test_a.py::test_y - AssertionError\n"
              "PASSED test/test_a.py::test_p[a b]\nERROR test/test_b.py - ImportError\n1 failed, 2 passed\n")
    assert t.passed(output) == {"test/test_a.py::test_x", "test/test_a.py::test_p[a b]"}


def test_a_test_of_the_requested_behaviour_transfers_to_the_upstream_fix(tmp_path):
    task, _ = _task(tmp_path)
    patch = _patch(task, tmp_path, "def value():\n    return 1 + 1\n", {"test_agent.py": BEHAVIOUR})
    value = t.transfer(task, patch, tmp_path / "work")
    assert value["outcome"] == "transfers"
    assert value["pinning"] == ["test/test_agent.py::test_two"] == value["transferring"]


def test_a_test_of_the_agents_own_helper_does_not(tmp_path):
    task, _ = _task(tmp_path)
    source = "def two():\n    return 2\n\n\ndef value():\n    return two()\n"
    patch = _patch(task, tmp_path, source, {"test_agent.py": OWN_HELPER})
    value = t.transfer(task, patch, tmp_path / "work")
    assert (value["outcome"], value["pinning"], value["transferring"]) == (
        "none", ["test/test_agent.py::test_helper"], [])


def test_both_kinds_in_one_patch_is_partial(tmp_path):
    task, _ = _task(tmp_path)
    source = "def two():\n    return 2\n\n\ndef value():\n    return two()\n"
    patch = _patch(task, tmp_path, source, {"test_agent.py": BEHAVIOUR, "test_helper.py": OWN_HELPER})
    value = t.transfer(task, patch, tmp_path / "work")
    assert value["outcome"] == "partial"
    assert value["pinning"] == ["test/test_agent.py::test_two", "test/test_helper.py::test_helper"]
    assert value["transferring"] == ["test/test_agent.py::test_two"]


def test_a_test_that_also_passes_without_the_change_pins_nothing(tmp_path):
    task, _ = _task(tmp_path)
    patch = _patch(task, tmp_path, "def value():\n    return 2\n", {"test_agent.py": PINS_NOTHING})
    assert t.transfer(task, patch, tmp_path / "work")["outcome"] == "no pinning test"


def test_the_analysis_counts_outcomes_per_arm_and_compares_the_two_testing_arms_by_task():
    def row(task, arm, outcome, pinning=1, transferring=None):
        moved = pinning if transferring is None else transferring
        return {"task": task, "arm": arm, "outcome": outcome,
                "pinning": [f"p{i}" for i in range(pinning)], "transferring": [f"p{i}" for i in range(moved)]}
    rows = [row("a", "instructed", "transfers"), row("a", "instructed", "none", transferring=0),
            row("a", "assisted", "transfers"),
            row("b", "instructed", "transfers", pinning=2), row("b", "assisted", "partial", pinning=2, transferring=1),
            row("c", "instructed", "transfers"), row("c", "assisted", "transfers"),
            # A run with nothing to transfer is not a failed transfer: c stays tied.
            row("c", "assisted", "no pinning test", pinning=0),
            row("d", "instructed", "transfers"), row("d", "ordinary", "no pinning test", pinning=0),
            row("e", "assisted", "not measured", pinning=0)]
    value = t.analyse(rows)
    assert value["primary"]["differences"] == {"a": -0.5, "b": 1.0} and value["primary"]["tied"] == 1
    assert value["per_arm"]["instructed"] == {"runs": 5, "outcomes": {"transfers": 4, "none": 1},
                                              "pinning_tests": 6, "transferring_tests": 5}
    assert value["per_arm"]["assisted"]["outcomes"] == {"transfers": 2, "partial": 1, "no pinning test": 1,
                                                        "not measured": 1}
    assert list(value["per_arm"]) == ["ordinary", "instructed", "assisted"]
