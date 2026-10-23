"""A tiny but valid six-stage case, built with real git diffs.

Stages 1-4 rename the scaling helper and update its one caller, so leaving the
caller behind breaks the base group `use`. Stages 5-6 add helpers nothing calls.
Stage 5 is a bug fix whose reference adds a test; stage 6 removes stage 5's fact.
"""
import json
import subprocess
from pathlib import Path

GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"]
RULES = ("# Project rules\n\n"
         "1. Keep `docs/reference.md` current whenever behaviour changes.\n"
         "2. Add a `CHANGELOG.md` entry for every change.\n"
         "3. Every bug fix carries a test.\n"
         "4. Never edit `src/pkg/_generated.py`.\n")


def _name(stage):
    return f"scaled_v{min(stage, 4)}"


def _facts(stage):
    facts = {"default": str(stage)}
    if stage == 5:
        facts["extra_v5"] = "5"
    if stage == 6:
        facts["extra_v6"] = "6"
    return facts


def _files(stage, *, caller=None):
    extra = {5: "\n\ndef extra_v5():\n    return 5\n", 6: "\n\ndef extra_v6():\n    return 6\n"}.get(stage, "")
    rows = "".join(f"| `{k}` | `{v}` |\n" for k, v in _facts(stage).items())
    files = {
        "src/pkg/__init__.py": "",
        "src/pkg/_generated.py": "GENERATED = True\n",
        "src/pkg/core.py": f"DEFAULT = {stage}\n\n\ndef {_name(stage)}(x):\n    return x * DEFAULT\n{extra}",
        "src/pkg/use.py": f"from pkg import core\n\n\ndef apply(x):\n    return core.{caller or _name(stage)}(x)\n",
        "tests/test_core.py": "from pkg import use\n\n\ndef test_apply():\n    assert use.apply(0) == 0\n",
        "docs/reference.md": "# Reference\n\n| Name | Value |\n|---|---|\n" + rows,
        "CHANGELOG.md": "# Changelog\n\n## Unreleased\n\n" + "".join(f"- stage {n}\n" for n in range(1, stage + 1)),
        "CLAUDE.md": RULES,
    }
    if stage == 5:
        files["tests/test_extra.py"] = "from pkg import core\n\n\ndef test_extra():\n    assert core.extra_v5() == 5\n"
    if stage == 6:
        files["tests/test_extra.py"] = "from pkg import core\n\n\ndef test_extra():\n    assert core.extra_v6() == 6\n"
    return files


def _write(root, files):
    for path in [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]:
        path.unlink()
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body.encode("utf-8"))


def _git(root, *args):
    return subprocess.run([*GIT, *args], cwd=root, capture_output=True, check=True).stdout


def _diff(work, files):
    _write(work, files)
    _git(work, "add", "-A")
    return _git(work, "diff", "--cached", "--binary")


GROUPS = {
    "use": "from pkg import core, use\n\n\ndef test_use():\n    assert use.apply(3) == 3 * core.DEFAULT\n",
    "generated": "from pkg import _generated\n\n\ndef test_generated():\n    assert _generated.GENERATED is True\n",
}


def _groups():
    rows = [{"id": "use", "since": 0, "until": 6}, {"id": "generated", "since": 0, "until": 6}]
    bodies = dict(GROUPS)
    for n in range(1, 7):
        rows.append({"id": f"default_{n}", "since": n, "until": n})
        bodies[f"default_{n}"] = f"from pkg import core\n\n\ndef test_default():\n    assert core.DEFAULT == {n}\n"
        if n <= 4:
            rows.append({"id": f"name_{n}", "since": n, "until": 6 if n == 4 else n})
            bodies[f"name_{n}"] = f"from pkg import core\n\n\ndef test_name():\n    assert core.scaled_v{n}(2) == 2 * core.DEFAULT\n"
        else:
            rows.append({"id": f"extra_{n}", "since": n, "until": n})
            bodies[f"extra_{n}"] = f"from pkg import core\n\n\ndef test_extra():\n    assert core.extra_v{n}() == {n}\n"
    return rows, bodies


def make_case(root):
    case = Path(root) / "fixture"
    (case / "start").mkdir(parents=True)
    _write(case / "start", _files(0))
    work = Path(root) / "fixture-work"
    work.mkdir()
    _git(work, "init", "-q")
    _write(work, _files(0))
    _git(work, "add", "-A")
    _git(work, "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "0")
    stages = []
    for n in range(1, 7):
        folder = case / "stages" / str(n)
        folder.mkdir(parents=True)
        (folder / "reference.diff").write_bytes(_diff(work, _files(n)))
        _git(work, "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", str(n))
        cross = n <= 4
        if cross:
            (folder / "dependent-missed.diff").write_bytes(_diff(work, _files(n, caller=_name(n - 1))))
            _git(work, "reset", "-q", "--hard")
        stages.append({
            "request": (f"Set the multiplier to {n} and rename the scaling helper to scaled_v{n}." if cross else
                        "extra_v5 is missing and should return 5." if n == 5 else
                        "Replace extra_v5 with extra_v6, which returns 6, and set the multiplier to 6."),
            "kind": "cross-cutting" if cross else "self-contained",
            "bugfix": n == 5,
            "dependent_missed_fails": ["use"] if cross else [],
        })
    groups, bodies = _groups()
    (case / "oracle" / "groups").mkdir(parents=True)
    for name, body in bodies.items():
        (case / "oracle" / "groups" / f"{name}.py").write_bytes(body.encode("utf-8"))
    (case / "oracle" / "facts.json").write_text(json.dumps({str(n): _facts(n) for n in range(7)}), encoding="utf-8")
    (case / "case.json").write_text(json.dumps({
        "id": "fixture", "pythonpath": "src", "test_dir": "tests", "protected": "src/pkg/_generated.py",
        "docs": "docs/reference.md", "changelog": "CHANGELOG.md", "stages": stages, "groups": groups,
    }, indent=1), encoding="utf-8")
    return case
