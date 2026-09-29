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
