"""Changed names come from a real git diff; a quiet dependent names none of them."""
import subprocess

from eval.multistage_quiet import changed_names, named

GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"]


def _diff(tmp_path, before, after):
    """Write `before`, commit, write `after`; return the stage n-1 tree and the diff between them."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run([*GIT, "init", "-q"], cwd=root, check=True)
    for rel, body in before.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding="utf-8")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "0"], cwd=root, check=True)
    snapshot = tmp_path / "before"
    subprocess.run([*GIT, "worktree", "add", "-q", str(snapshot)], cwd=root, check=True)
    for rel, body in after.items():
        target = root / rel
        if body is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    diff = subprocess.run([*GIT, "diff", "--cached"], cwd=root, capture_output=True, check=True).stdout.decode()
    return snapshot, diff


MONEY = "def total(items):\n    return sum(items)\n\n\ndef other():\n    return 1\n"


def test_a_function_whose_body_changes_is_a_changed_name(tmp_path):
    before, diff = _diff(tmp_path, {"m.py": MONEY}, {"m.py": MONEY.replace("sum(items)", "round(sum(items), 2)")})
    names = changed_names(diff, before, exclude="dep.py")
    assert "total" in names and "other" not in names


def test_a_function_appended_below_another_does_not_change_it(tmp_path):
    grown = MONEY + "\n\ndef extra():\n    return 3\n"
    before, diff = _diff(tmp_path, {"m.py": MONEY}, {"m.py": grown})
    assert changed_names(diff, before, exclude="dep.py") == set()
    longer = MONEY.replace("    return 1\n", "    value = 1\n    return value\n")
    before, diff = _diff(tmp_path / "b", {"m.py": MONEY}, {"m.py": longer})
    assert changed_names(diff, before, exclude="dep.py") == {"other"}


def test_a_body_that_only_loses_a_line_is_changed(tmp_path):
    source = "def total(items):\n    items = list(items)\n    return sum(items)\n"
    before, diff = _diff(tmp_path, {"m.py": source}, {"m.py": source.replace("    items = list(items)\n", "")})
    assert changed_names(diff, before, exclude="dep.py") == {"total"}


def test_a_method_added_to_a_class_after_a_blank_line_changes_the_class(tmp_path):
    source = "class Ledger:\n    def a(self):\n        return 1\n"
    before, diff = _diff(tmp_path, {"m.py": source}, {"m.py": source + "\n    def b(self):\n        return 2\n"})
    assert changed_names(diff, before, exclude="dep.py") == {"Ledger"}


def test_a_renamed_identifier_is_net_removed_only_when_gone(tmp_path):
    source = "def f():\n    old_name = 1\n    kept = 2\n    return old_name + kept\n"
    changed = "def f():\n    new_name = 1\n    kept = 3\n    return new_name + kept\n"
    before, diff = _diff(tmp_path, {"m.py": source}, {"m.py": changed})
    names = changed_names(diff, before, exclude="dep.py")
    assert "old_name" in names and "kept" not in names and "new_name" not in names


def test_short_literals_are_ignored_and_long_ones_kept(tmp_path):
    source = "SEP = ','\nKIND = 'format_money'\n"
    before, diff = _diff(tmp_path, {"m.py": source}, {"m.py": "SEP = ';'\nKIND = 'format_cash'\n"})
    names = changed_names(diff, before, exclude="dep.py")
    assert "format_money" in names and "," not in names


def test_a_module_constant_changed_is_a_changed_name(tmp_path):
    before, diff = _diff(tmp_path, {"m.py": "SEP = ','\nOTHER = 1\n"}, {"m.py": "SEP = ';'\nOTHER = 1\n"})
    names = changed_names(diff, before, exclude="dep.py")
    assert "SEP" in names and "OTHER" not in names


def test_a_new_file_and_a_deleted_file_do_not_crash(tmp_path):
    before, diff = _diff(tmp_path, {"m.py": MONEY, "gone.py": "def vanished():\n    return 0\n"},
                         {"new.py": "def fresh():\n    return 2\n", "gone.py": None})
    names = changed_names(diff, before, exclude="dep.py")
    assert "vanished" in names and "fresh" not in names


def test_the_dependents_own_hunks_are_excluded(tmp_path):
    before, diff = _diff(tmp_path, {"m.py": MONEY, "dep.py": "def report():\n    return 'unit_old'\n"},
                         {"m.py": MONEY.replace("sum(items)", "sum(items) * 2"),
                          "dep.py": "def report():\n    return 'unit_new'\n"})
    names = changed_names(diff, before, exclude="dep.py")
    assert "total" in names and "report" not in names and "unit_old" not in names


def test_a_non_python_dependent_naming_it_is_found(tmp_path):
    registry = tmp_path / "registry.json"
    registry.write_text('{"money": "format_money"}', encoding="utf-8")
    assert named({"format_money", "absent"}, registry) == ["format_money"]


def test_whole_words_only(tmp_path):
    dependent = tmp_path / "parse.py"
    dependent.write_text("SEP_IN = ','\nseparator = SEP_IN\n", encoding="utf-8")
    assert named({"SEP", "SEP_IN"}, dependent) == ["SEP_IN"]
