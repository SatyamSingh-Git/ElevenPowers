"""Repository selection must preserve real inputs and exclude generated noise."""
import subprocess

from core.evidence import source_files


def git(root, *args):
    return subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", *args],
                          cwd=root, check=True, capture_output=True)


def test_git_ignores_generated_data_but_keeps_tracked_and_new_source(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text("generated/\ntracked.json\n")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated/noise.json").write_text("{}")
    (tmp_path / "tracked.json").write_text("{}")
    git(tmp_path, "add", "-f", "tracked.json")
    (tmp_path / "new.py").write_text("x = 1")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/ci.yml").write_text("name: ci")
    assert source_files(tmp_path) == [".github/ci.yml", "new.py", "tracked.json"]


def test_git_scan_stays_in_selected_root(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "outer.py").write_text("x = 1")
    child = tmp_path / "child"
    child.mkdir()
    (child / "inner.py").write_text("x = 2")
    assert source_files(child) == ["inner.py"]


def test_git_scan_does_not_enter_nested_repository(tmp_path):
    git(tmp_path, "init", "-q")
    nested = tmp_path / "nested"
    nested.mkdir()
    git(nested, "init", "-q")
    (nested / "private.py").write_text("x = 1")
    (tmp_path / "own.py").write_text("x = 2")
    assert source_files(tmp_path) == ["own.py"]


def test_budget_reports_truncation_and_exact_boundary_is_complete(tmp_path):
    from core.evidence import scan_sources
    for name in ("a.py", "b.py", "c.py"):
        (tmp_path / name).write_text("abc")
    result = scan_sources(tmp_path, limit=2)
    assert result.files == ["a.py", "b.py"]
    assert not result.complete
    assert "file limit" in " ".join(result.issues)
    assert scan_sources(tmp_path, limit=3).complete
    result = scan_sources(tmp_path, max_bytes=5)
    assert not result.complete
    assert "byte limit" in " ".join(result.issues)


def test_partial_scan_cannot_be_fresh_and_is_reported(tmp_path, monkeypatch):
    from core import evidence
    from core.parsers import parse
    from core.ledger import Ledger
    from core.obligations import Claim
    from core.report import gate_message
    (tmp_path / "app.py").write_text("x=1")
    monkeypatch.setattr(evidence, "scan_sources", lambda *a, **kw:
                        evidence.SourceScan(["app.py"], ["file limit exceeded"], 3))
    receipt = parse("npm test", "", 0, tmp_path)[0]
    assert receipt.freshness(tmp_path) is evidence.Freshness.STALE
    assert receipt.coverage_issues == ["file limit exceeded"]
    assert evidence.Evidence.from_dict(receipt.to_dict()).coverage_issues
    ledger = Ledger(root=tmp_path, claims=[Claim.FEATURE_ADDED], evidence=[receipt])
    assert "coverage" in gate_message(ledger).lower()


def test_empty_scan_is_invalidated_by_new_source(tmp_path):
    from core.evidence import Freshness
    from core.parsers import parse
    receipt = parse("npm test", "", 0, tmp_path)[0]
    assert receipt.freshness(tmp_path) is Freshness.FRESH
    (tmp_path / "new.py").write_text("x=1")
    assert receipt.freshness(tmp_path) is Freshness.STALE


def test_git_failure_is_visible_even_when_fallback_finds_source(tmp_path, monkeypatch):
    from core import evidence
    (tmp_path / ".git").mkdir()
    (tmp_path / "app.py").write_text("x=1")
    monkeypatch.setattr(evidence, "_git_sources", lambda root: None)
    result = evidence.scan_sources(tmp_path)
    assert result.files == ["app.py"]
    assert not result.complete


def test_source_symlink_is_not_followed(tmp_path):
    import pytest
    from core.evidence import scan_sources
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("secret")
    root = tmp_path / "project"
    root.mkdir()
    try:
        (root / "linked.py").symlink_to(outside / "secret.py")
    except OSError:
        pytest.skip("symlink creation not permitted")
    result = scan_sources(root)
    assert result.files == []
    assert not result.complete


def test_project_scan_policy_roundtrips_and_applies(tmp_path):
    from core.config import Config, load, save
    from core.evidence import scan_sources
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated/data.json").write_text("{}")
    (tmp_path / "app.py").write_text("x=1")
    save(tmp_path, Config(scan={"exclude": ["generated/"], "max_files": 1, "max_bytes": 8}))
    assert load(tmp_path).scan["max_files"] == 1
    scan = scan_sources(tmp_path)
    assert scan.files == ["app.py"]
    assert scan.complete
    (tmp_path / "new.py").write_text("y=1")
    assert not scan_sources(tmp_path).complete


def test_invalid_budget_is_visible_not_a_crash(tmp_path):
    import json
    from core.evidence import scan_sources
    (tmp_path / ".elevenpowers").mkdir()
    (tmp_path / ".elevenpowers/config.json").write_text(json.dumps({"scan": {"max_files": -1}}))
    assert not scan_sources(tmp_path).complete


def test_missing_root_is_incomplete(tmp_path):
    from core.evidence import scan_sources
    assert not scan_sources(tmp_path / "missing").complete


def test_unreadable_snapshot_cannot_be_fresh(tmp_path, monkeypatch):
    from core import evidence
    from core.parsers import parse
    (tmp_path / "app.py").write_text("x=1")
    monkeypatch.setattr(evidence, "_digest", lambda root, rel: "missing")
    receipt = parse("npm test", "", 0, tmp_path)[0]
    assert "unreadable" in " ".join(receipt.coverage_issues)
    assert receipt.freshness(tmp_path) is evidence.Freshness.STALE


def test_git_nested_ignore_negation_and_tracked_edit_invalidate(tmp_path):
    from core.evidence import Freshness
    from core.parsers import parse
    git(tmp_path, "init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/.gitignore").write_text("*.json\n!keep.json\n")
    (tmp_path / "src/noise.json").write_text("{}")
    (tmp_path / "src/keep.json").write_text("{}")
    receipt = parse("npm test", "", 0, tmp_path)[0]
    assert receipt.observed == ["src/keep.json"]
    (tmp_path / "src/noise.json").write_text('{"ignored":true}')
    assert receipt.freshness(tmp_path) is Freshness.FRESH
    (tmp_path / "src/keep.json").write_text('{"changed":true}')
    assert receipt.freshness(tmp_path) is Freshness.STALE


def test_subproject_inherits_git_ignore_rules(tmp_path):
    from core.evidence import scan_sources
    git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text("generated/\nscratch/\n")
    child = tmp_path / "child"
    (child / "generated").mkdir(parents=True)
    (child / "generated/noise.json").write_text("{}")
    (child / "real.py").write_text("x=1")
    scan = scan_sources(child)
    assert scan.complete
    assert scan.files == ["real.py"]
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "own.py").write_text("x=1")
    assert scan_sources(scratch).files == ["own.py"]
