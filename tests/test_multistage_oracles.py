"""Multi-stage v2 oracles, run against the fixture case's real stage trees."""
import pytest

from eval.multistage_cases import load, tree
from eval.multistage_oracles import facts, groups, regressions, rules, stale
from tests.multistage_fixture import make_case


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    return load(make_case(tmp_path_factory.mktemp("multistage")))


@pytest.mark.parametrize("stage", range(7))
def test_reference_tree_passes_its_groups(case, tmp_path, stage):
    got = groups(case, stage, tree(case, stage, tmp_path / "t"))
    assert got and set(got.values()) == {"passed"}, got


def test_a_missed_dependent_fails_an_earlier_group(case, tmp_path):
    previous = groups(case, 1, tree(case, 1, tmp_path / "one"))
    current = groups(case, 2, tree(case, 2, tmp_path / "two", "dependent-missed"))
    assert current["use"] == "failed"
    assert regressions(case, 2, previous, current) == ["use"]


def test_a_new_group_failing_is_not_a_regression(case, tmp_path):
    previous = groups(case, 1, tree(case, 1, tmp_path / "one"))
    current = groups(case, 2, tree(case, 2, tmp_path / "noop", "no-op"))
    assert current["default_2"] == "failed"
    assert regressions(case, 2, previous, current) == []


def test_a_conftest_in_the_tree_does_not_pass_a_failing_group(case, tmp_path):
    missed = tree(case, 2, tmp_path / "t", "dependent-missed")
    hook = "def pytest_sessionfinish(session, exitstatus):\n    session.exitstatus = 0\n"
    (missed / "conftest.py").write_text(hook, encoding="utf-8")
    (missed / "src" / "conftest.py").write_text(hook, encoding="utf-8")
    assert groups(case, 2, missed)["use"] == "failed"


def test_a_hanging_candidate_times_out(case, tmp_path):
    root = tree(case, 1, tmp_path / "t")
    (root / "src" / "pkg" / "use.py").write_text("while True:\n    pass\n", encoding="utf-8")
    assert groups(case, 1, root, seconds=5)["use"] == "timeout"


def test_stale_facts(case, tmp_path):
    assert stale(case, 3, tree(case, 3, tmp_path / "ref")) == []
    assert stale(case, 3, tree(case, 3, tmp_path / "forgot", "docs-forgotten")) == ["default"]
    gone = tree(case, 5, tmp_path / "gone")
    (gone / "docs" / "reference.md").unlink()
    assert stale(case, 5, gone) == ["default", "extra_v5"]
    prose = tree(case, 2, tmp_path / "prose")
    (prose / "docs" / "reference.md").write_text("The default is 2.\n", encoding="utf-8")
    assert stale(case, 2, prose) == ["default"]
    crlf = tree(case, 4, tmp_path / "crlf")
    doc = crlf / "docs" / "reference.md"
    doc.write_bytes(doc.read_bytes().replace(b"\n", b"\r\n"))
    assert stale(case, 4, crlf) == []
    kept = tree(case, 6, tmp_path / "kept")
    with (kept / "docs" / "reference.md").open("a", encoding="utf-8") as handle:
        handle.write("| `extra_v5` | `5` |\n")
    assert stale(case, 6, kept) == ["extra_v5"]


def test_facts_reads_backticked_rows_only():
    text = "| Name | Value |\r\n|---|---|\r\n| `a` | `1` | why |\r\n| b | 2 |\r\n|`c`|``|\r\n"
    assert facts(text) == {"a": "1", "c": ""}


def test_rules_count_changelog_entries_and_guard_the_protected_file(case, tmp_path):
    before, after = tree(case, 1, tmp_path / "b"), tree(case, 2, tmp_path / "a")
    got = rules(case, 2, before, after)
    assert (got["changelog"], got["protected"], got["test_with_fix"]) == (1, True, None)
    log = after / "CHANGELOG.md"
    log.write_text(log.read_text(encoding="utf-8").replace("## Unreleased", "## Next"), encoding="utf-8")
    (after / "src" / "pkg" / "_generated.py").write_text("GENERATED = False\n", encoding="utf-8")
    got = rules(case, 2, before, after)
    assert (got["changelog"], got["protected"]) == (0, False)


def test_a_crlf_changelog_counts_the_same(case, tmp_path):
    before, after = tree(case, 1, tmp_path / "b"), tree(case, 2, tmp_path / "a")
    for root in (before, after):
        log = root / "CHANGELOG.md"
        log.write_bytes(log.read_bytes().replace(b"\n", b"\r\n"))
    assert rules(case, 2, before, after)["changelog"] == 1


def test_a_bug_fix_counts_only_with_a_test_that_pins_it(case, tmp_path):
    before = tree(case, 4, tmp_path / "b")
    assert rules(case, 5, before, tree(case, 5, tmp_path / "a"))["test_with_fix"] is True
    bare = tree(case, 5, tmp_path / "bare")
    (bare / "tests" / "test_extra.py").unlink()
    assert rules(case, 5, before, bare)["test_with_fix"] is False
