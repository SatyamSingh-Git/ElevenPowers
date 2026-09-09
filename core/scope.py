"""Noticing when an edit has wandered away from the task.

Scope cannot be declared up front. Nobody knows which files a change will touch
before making it, and a guard built on a guessed list would spend its life
questioning correct work. So scope is derived from what the task has already
established: the files the agent read, the files it edited, and the areas the
request itself named.

Everything here is a suspicion rather than a rule, so the guard asks and the
person decides. The failure it exists to catch is an agent quietly editing part
of the codebase it never looked at, which is where silent regressions come from.
"""

from __future__ import annotations

import re
from pathlib import Path

MANIFESTS = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "poetry.lock",
    "uv.lock", "Pipfile", "Pipfile.lock", "go.mod", "go.sum", "Cargo.toml",
    "Cargo.lock", "Gemfile", "Gemfile.lock", "composer.json", "composer.lock",
    "pom.xml", "build.gradle", "build.gradle.kts", "Makefile", "justfile",
    "tsconfig.json", "Dockerfile", "docker-compose.yml",
}
PROSE = {".md", ".rst", ".txt", ".adoc"}
# Words that carry no information about which part of a codebase something is.
# Container directories say only that a repository has structure, and generic
# filenames repeat in every module, so matching on either makes two unrelated
# files look like neighbours.
CONTAINERS = {
    "src", "lib", "app", "apps", "pkg", "packages", "services", "modules",
    "crates", "cmd", "internal", "workspaces", "projects", "libs",
}
GENERIC = {
    "config", "configs", "util", "utils", "helper", "helpers", "common",
    "constant", "constants", "type", "types", "index", "init", "main", "base",
    "core", "shared", "misc", "setup", "model", "models", "schema", "schemas",
}
WORDS = {"the", "and", "for", "with", "from", "into", "that", "this", "test",
         "tests", "spec", "specs", "fix", "add", "update", "change"}
STOP = CONTAINERS | GENERIC | WORDS


def normalise(path: str, root: Path | None = None) -> str:
    """A repository-relative path with forward slashes."""
    text = str(path).replace("\\", "/")
    if root is not None:
        try:
            text = str(Path(path).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
        except (ValueError, OSError):
            pass
    return text.lstrip("./")


def tokens(text: str) -> set[str]:
    """Meaningful words in a path or a sentence, lowercased and singularised.

    A request saying "date helpers" should match `dates.py`, so trailing
    plurals are trimmed before comparison.
    """
    parts = re.split(r"[^A-Za-z0-9]+|(?<=[a-z])(?=[A-Z])", text)
    out = set()
    for part in parts:
        word = part.lower()
        if len(word) <= 2 or word in STOP:
            continue
        out.add(_singular(word))
    return out


def _singular(word: str) -> str:
    """Just enough stemming to match a plural in a request to a singular file.

    The "es" ending only drops both letters after a sibilant, as in boxes or
    matches. Applying it everywhere turned "dates" into "dat", which then
    matched nothing.
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("ses", "xes", "zes", "ches", "shes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def basename_tokens(path: str) -> set[str]:
    """Tokens of the filename alone.

    Directory structure is what `area` compares. Including it here as well made
    two files in different packages of a monorepo look related because both
    paths contained the word "packages".
    """
    return tokens(normalise(path).split("/")[-1])


def area(path: str) -> tuple[str, ...]:
    """The part of the tree a file belongs to.

    Test trees mirror source trees, so `tests/auth/test_session.py` is treated as
    living in the same area as `src/auth/session.py`. Without that, editing a
    test for the code you just changed would look like wandering.
    """
    parts = [p for p in normalise(path).split("/")[:-1] if p]
    trimmed = [p for p in parts if p.lower() not in {"src", "lib", "tests", "test", "spec", "__tests__"}]
    return tuple(trimmed[:2]) if trimmed else tuple(parts[:1])


def is_manifest(path: str) -> bool:
    name = normalise(path).split("/")[-1]
    return name in MANIFESTS or name.endswith((".lock", ".lockb"))


def is_prose(path: str) -> bool:
    return Path(normalise(path)).suffix.lower() in PROSE


def unrelated(target: str, seen: list[str], request: str, exists: bool) -> str:
    """Why this edit looks like drift, or an empty string if it does not.

    Silent unless every reason to stay quiet is exhausted, because the cost of
    interrupting good work is higher than the cost of missing one stray edit.
    """
    if not seen:
        return ""                      # nothing established yet
    if not exists:
        return ""                      # creating a file is not wandering
    path = normalise(target)
    if is_manifest(path) or is_prose(path):
        return ""
    known = {normalise(s) for s in seen}
    if path in known:
        return ""                      # already read or edited

    if area(path) and any(area(path) == area(s) for s in known):
        return ""                      # same part of the tree as the work so far

    if tokens(request) & tokens(path):
        return ""                      # the request names this file or its area

    here = basename_tokens(path)
    for other in known:
        if here & basename_tokens(other):
            return ""                  # shares a name with something touched

    where = "/".join(area(path))
    place = f"is in {where}, which" if where else "is somewhere"
    return (
        f"{path} {place} this task has not read or edited, "
        f"and the request does not mention it. Edit it anyway, or read it first."
    )
