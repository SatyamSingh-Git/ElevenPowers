import json
from pathlib import Path
import subprocess
import sys


def test_codex_generated_wiring_covers_every_supported_event():
    from core.hosts.codex import EVENTS
    from core.hosts.wiring import configuration
    config = configuration("codex", "python launcher.py")
    assert set(config["hooks"]) == set(EVENTS)
    assert config["hooks"]["Stop"][0]["hooks"][0]["timeout"] == 600
    assert config["hooks"]["PostToolUse"][0]["hooks"][0]["timeout"] == 120


def test_codex_bundle_is_self_contained(tmp_path):
    from core.hosts.package import build
    target = tmp_path / "elevenpowers"
    build("codex", target)
    manifest = json.loads((target / ".codex-plugin/plugin.json").read_text())
    assert manifest["name"] == "elevenpowers"
    assert (target / "core/verify.py").is_file()
    assert not (target / ".elevenpowers").exists()
    assert not list(target.rglob("__pycache__"))
    result = subprocess.run([sys.executable, str(target / "plugin/bin/ep_host.py"), "codex", "Stop"],
                            input=json.dumps({"cwd": str(tmp_path)}), text=True,
                            capture_output=True, cwd=tmp_path, timeout=20)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)


def test_gemini_timeouts_are_milliseconds_and_bundle_has_extension_manifest(tmp_path):
    from core.hosts.wiring import configuration
    from core.hosts.package import build
    from core.hosts.gemini import EVENTS
    config = configuration("gemini", "python launcher.py")
    assert set(config["hooks"]) == set(EVENTS)
    assert config["hooks"]["AfterAgent"][0]["hooks"][0]["timeout"] == 600000
    assert config["hooks"]["AfterTool"][0]["hooks"][0]["timeout"] == 120000
    bundle = build("gemini", tmp_path / "elevenpowers")
    assert json.loads((bundle / "gemini-extension.json").read_text())["name"] == "elevenpowers"
    assert not (bundle / ".codex-plugin").exists()
    assert "${extensionPath}" in (bundle / "hooks/hooks.json").read_text()


def test_cursor_flat_native_wiring_and_package(tmp_path):
    from core.hosts.wiring import configuration
    from core.hosts.package import build
    from core.hosts.cursor import EVENTS
    config = configuration("cursor", "python launcher.py")
    assert config["version"] == 1
    assert set(config["hooks"]) == set(EVENTS)
    assert config["hooks"]["stop"][0]["loop_limit"] == 2
    assert config["hooks"]["stop"][0]["timeout"] == 600
    assert "hooks" not in config["hooks"]["postToolUse"][0]
    bundle = build("cursor", tmp_path / "elevenpowers")
    manifest = json.loads((bundle / ".cursor-plugin/plugin.json").read_text())
    assert manifest["hooks"] == "./hooks/hooks.json"
    assert "CURSOR_PLUGIN_ROOT" in (bundle / "hooks/hooks.json").read_text()
