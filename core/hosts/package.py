"""Build a portable native bundle without local state, caches or dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from .bridge import adapter
from .wiring import configuration


def build(platform: str, target: Path) -> Path:
    adapter(platform)
    target = Path(target).resolve()
    if target.exists():
        raise ValueError("bundle destination already exists; choose an empty new path")
    source = Path(__file__).resolve().parents[1]
    if target == source or source in target.parents:
        raise ValueError("bundle destination cannot be inside the runtime source")
    target.mkdir(parents=True)
    shutil.copytree(source, target / "core", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    launchers = target / "plugin/bin"
    launchers.mkdir(parents=True)
    for item in (source.parent / "plugin/bin").glob("*.py"):
        shutil.copy2(item, launchers / item.name)
    manifest = {"name": "elevenpowers", "version": "0.1.0", "description": "Repository-aware verification and durable command evidence."}
    manifest.update(author={"name": "ElevenPowers contributors"}, interface={
        "displayName": "ElevenPowers", "shortDescription": "Verify repository work with durable evidence.",
        "longDescription": "Automatically discover project checks, record command outcomes and verify completion.",
        "developerName": "ElevenPowers contributors", "category": "Productivity",
        "capabilities": [], "defaultPrompt": "Check the verification status of this project.",
    })
    manifest_path = target / ("gemini-extension.json" if platform == "gemini" else ".codex-plugin/plugin.json")
    if platform == "gemini":
        manifest = {k: manifest[k] for k in ("name", "version", "description")}
    if platform == "cursor":
        manifest_path = target / ".cursor-plugin/plugin.json"
        manifest = {k: manifest[k] for k in ("name", "version", "description", "author")}
        manifest["hooks"] = "./hooks/hooks.json"
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Python resolves the host-provided root; no shell-specific variable syntax.
    command = 'python -c "import os,runpy;runpy.run_path(os.path.join(os.environ[\'PLUGIN_ROOT\'],\'plugin\',\'bin\',\'ep_host.py\'),run_name=\'__main__\')"'
    if platform == "gemini":
        command = 'python "${extensionPath}/plugin/bin/ep_host.py"'
    if platform == "cursor":
        command = 'python "${CURSOR_PLUGIN_ROOT}/plugin/bin/ep_host.py"'
    hooks_path = target / "hooks/hooks.json"
    hooks_path.parent.mkdir()
    hooks_path.write_text(json.dumps(configuration(platform, command), indent=2) + "\n", encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(build(args.platform, args.destination))


if __name__ == "__main__":
    main()
