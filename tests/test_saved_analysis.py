"""Saved experiment analyses must work without the original author's machine."""
import subprocess
import sys
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("explicit_root", [False, True])
@pytest.mark.parametrize("folder,part,expected", [
    ("b8-feedback", "b8", "54/54 original survivors killed"),
    ("b9-gate-tests", "b9", "50/265 mutants survived"),
    ("b9-gate-tests", "raters", "raters present ['opus', 'sonnet']"),
])
def test_committed_results_work_from_another_directory(tmp_path, folder, part, expected, explicit_root):
    saved = tmp_path / "checkout/results"
    for name in ("b8-feedback", "b9-gate-tests", "b7-mutants/blind-review"):
        shutil.copytree(ROOT / "results" / name, saved / name)
    result = subprocess.run(
        [sys.executable, str(saved / folder / "analyse.py"), part]
        + (["--results-root", str(saved)] if explicit_root else []),
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


@pytest.mark.parametrize("part", ["b8", "b9", "raters"])
def test_missing_inputs_fail_instead_of_reporting_empty_success(tmp_path, part):
    result = subprocess.run(
        [sys.executable, str(ROOT / "results/b9-gate-tests/analyse.py"),
         part, "--results-root", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "missing" in result.stderr.lower()
