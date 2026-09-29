"""Saved experiment analyses must work without the original author's machine."""
import subprocess
import json
import sys
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAVED_INPUTS = (
    "b8-feedback/analyse.py", "b8-feedback/analysis-records.json",
    "b9-gate-tests/analyse.py", "b9-gate-tests/patches.json",
    "b7-mutants/blind-review/blind_key.json", "b7-mutants/blind-review/author_labels.json",
    "b7-mutants/blind-review/rater_opus.json", "b7-mutants/blind-review/rater_sonnet.json",
)


def saved_checkout(tmp_path):
    """Copy only the published analysis inputs, never ignored local run files."""
    saved = tmp_path / "checkout/results"
    for relative in SAVED_INPUTS:
        source = ROOT / "results" / relative
        if source.exists():
            target = saved / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    assert not (saved / "b8-feedback/runs").exists()
    return saved


@pytest.mark.parametrize("explicit_root", [False, True])
@pytest.mark.parametrize("folder,part,expected", [
    ("b8-feedback", "b8", "54/54 original survivors killed"),
    ("b9-gate-tests", "b8", "54/54 original survivors killed"),
    ("b9-gate-tests", "b9", "50/265 mutants survived"),
    ("b9-gate-tests", "raters", "raters present ['opus', 'sonnet']"),
])
def test_committed_results_work_from_another_directory(tmp_path, folder, part, expected, explicit_root):
    saved = saved_checkout(tmp_path)
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


@pytest.mark.parametrize("folder", ["b8-feedback", "b9-gate-tests"])
def test_empty_curated_b8_records_are_not_success(tmp_path, folder):
    saved = saved_checkout(tmp_path)
    (saved / "b8-feedback/analysis-records.json").write_text(
        json.dumps({"schema": 1, "records": []}), encoding="utf-8")
    result = subprocess.run([sys.executable, str(saved / folder / "analyse.py"), "b8"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert "missing" in result.stderr.lower()
