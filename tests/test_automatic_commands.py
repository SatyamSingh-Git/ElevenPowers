"""Installation should activate useful defaults without project-specific setup."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.config import Config, load, save
from core.evidence import Kind, Result, scan_sources
from core.parsers import parse


def package(root, scripts, **extra):
    (root / "package.json").write_text(json.dumps({"scripts": scripts, **extra}), encoding="utf-8")


@pytest.mark.parametrize("manager", ["npm", "pnpm", "yarn", "bun"])
def test_manifest_commands_are_automatic_and_follow_package_manager(tmp_path, manager):
    package(tmp_path, {"ci": "node quality.mjs", "test": "node --test", "build": "builder", "typecheck": "checker"},
            packageManager=manager + "@1.0.0")
    config = load(tmp_path)
    assert config.commands["tests"] == f"{manager} run ci"
    assert config.commands["build"] == f"{manager} run build"
    receipt = parse(f"{manager} run ci", "# pass 4\n# fail 0", 0, tmp_path)[0]
    assert receipt.kind is Kind.SUITE and receipt.result is Result.PASS
    assert not (tmp_path / ".elevenpowers/config.json").exists()


def test_explicit_commands_and_disables_win_over_discovery(tmp_path):
    package(tmp_path, {"ci": "checks", "build": "builder"})
    save(tmp_path, Config(commands={"tests": "custom-check", "build": ""}))
    config = load(tmp_path)
    assert config.commands == {"tests": "custom-check"}
    path = tmp_path / ".elevenpowers/config.json"
    path.write_text(json.dumps({"auto_detect": False}), encoding="utf-8")
    assert load(tmp_path).commands == {}


@pytest.mark.parametrize("filename,contents,command", [
    ("pyproject.toml", "[tool.pytest.ini_options]\ntestpaths = ['tests']", "python -m pytest"),
    ("pytest.ini", "[pytest]\n", "python -m pytest"),
    ("Cargo.toml", '[package]\nname = "probe"\nversion = "0.1.0"', "cargo test"),
    ("go.mod", "module example.org/probe\n", "go test ./..."),
])
def test_other_project_manifests_supply_conventional_tests(tmp_path, filename, contents, command):
    (tmp_path / filename).write_text(contents, encoding="utf-8")
    assert load(tmp_path).command_for("tests") == command


@pytest.mark.parametrize("contents", ['[]', '{"scripts": []}', '{broken'])
def test_malformed_manifest_is_not_executed_or_a_crash(tmp_path, contents):
    (tmp_path / "package.json").write_text(contents, encoding="utf-8")
    assert load(tmp_path).commands == {}


def test_ambiguous_managers_require_override(tmp_path):
    package(tmp_path, {"test": "checks"})
    (tmp_path / "yarn.lock").touch()
    (tmp_path / "pnpm-lock.yaml").touch()
    assert load(tmp_path).commands == {}


def test_automatic_verification_runs_shared_command_once(tmp_path, monkeypatch):
    from core import verify
    from core.ledger import Ledger
    save(tmp_path, Config(commands={"tests": "all-checks", "typecheck": "all-checks"}))
    monkeypatch.setattr(verify, "dischargeable", lambda ledger: ["tests", "typecheck"])
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "checks complete", "")
    monkeypatch.setattr(verify, "run_command", run)
    # Avoid replacing Git's subprocess calls used for evidence snapshots.
    monkeypatch.setattr(verify, "parse", lambda *args, **kwargs: [])
    verify.discharge(Ledger(root=tmp_path))
    assert calls == ["all-checks"]


def test_frontend_build_does_not_hide_python_test_command(tmp_path):
    package(tmp_path, {"build": "tailwind"})
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    assert load(tmp_path).commands == {"build": "npm run build", "tests": "python -m pytest"}


def test_test_evidence_does_not_launch_unrelated_benchmarks(tmp_path, monkeypatch):
    from core import stress
    from core.ledger import Ledger
    from core.obligations import Claim
    package(tmp_path, {"test": "checks", "build": "builder", "bench": "expensive"})
    ledger = Ledger(root=tmp_path, claims=[Claim.BUG_FIXED], base="base")
    ledger.add(parse("npm run test", "# pass 1\n# fail 0", 0, tmp_path))
    calls = []
    monkeypatch.setattr(stress, "_inputs_stamp", lambda *args: "inputs")
    def old_tree(root, base, command, **kwargs):
        calls.append(command)
        return True, "# pass 1\n# fail 0"
    monkeypatch.setattr(stress, "on_the_old_tree", old_tree)
    stress.stress(ledger)
    assert calls == ["npm run test"]


def test_tap_result_lines_are_not_counted_as_go_packages(tmp_path):
    package(tmp_path, {"ci": "node --test"})
    receipt = parse("npm run ci", "TAP version 13\nok 1 - works\n1..1\n# pass 1\n# fail 0\n", 0, tmp_path)[0]
    assert receipt.passed == 1


