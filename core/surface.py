"""What a project is actually capable of proving.

An obligation that no amount of good work can discharge is a design error, not a
standard. A project with no test suite cannot produce suite evidence; demanding
it guarantees a false block. This scans the repository once and reports which
kinds of proof are available, so obligations can be filtered to what is
achievable here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .evidence import IGNORED_DIRS

TEST_NAME = re.compile(r"(^|/)(tests?|spec|__tests__)(/|$)|(^|/)(test_[^/]+|[^/]+_test|[^/]+\.test|[^/]+\.spec|[^/]+_spec)\.")


@dataclass(frozen=True)
class Surface:
    tests: bool = False
    typecheck: bool = False
    build: bool = False
    benchmark: bool = False

    def supports(self, need: str) -> bool:
        return bool(getattr(self, need, False))


def _walk(root: Path, limit: int = 6000) -> list[str]:
    found: list[str] = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for name in filenames:
            found.append(str(Path(dirpath, name).relative_to(root)).replace("\\", "/"))
            if len(found) >= limit:
                return found
    return found


def detect(root: Path) -> Surface:
    files = _walk(root)
    names = set(files)

    tests = any(TEST_NAME.search(f) for f in files)

    typecheck = "tsconfig.json" in names or any(
        f.endswith(("mypy.ini", ".mypy.ini")) for f in files
    )
    build = False
    benchmark = any("bench" in f.lower() for f in files)

    pkg = root / "package.json"
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
        except (json.JSONDecodeError, OSError):
            scripts = {}
        tests = tests or "test" in scripts
        build = build or "build" in scripts
        typecheck = typecheck or "typecheck" in scripts or "tsconfig.json" in names
        benchmark = benchmark or "bench" in scripts

    if any(n in names for n in ("Cargo.toml", "go.mod", "Makefile", "pom.xml", "build.gradle")):
        build = True
    if "Cargo.toml" in names or "go.mod" in names:
        typecheck = True

    return Surface(tests=tests, typecheck=typecheck, build=build, benchmark=benchmark)
