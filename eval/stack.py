"""Assemble the composition baseline, and count what it costs before it runs.

The project's first goal was to combine the strengths of the systems it studied.
`docs/research/complementarity-matrix.md` section 6 specifies the stack that
tests whether that works: best-of-breed pieces installed together, measured
against each piece alone. It has never been built, so the claim that this project
beats composition has never been testable.

This builds it from local clones, and reports the census the matrix predicted
would be the problem: how much instruction text is loaded before a single
request arrives, how many routers compete to answer that request, how many hooks
fire on one stop, and how many state directories appear in the repository.

Usage:
    python -m eval.stack --repos DIR [--out DIR]
    python -m eval.stack --census-only
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_OUT = Path("build") / "stack"

# The recipe, verbatim from the matrix. Each entry is a strength being lifted,
# not a whole system: taking all of ECC would load 21,000 tokens of skill
# descriptions before anything happens, which is the dilution being measured.
@dataclass(frozen=True)
class Piece:
    system: str
    licence: str
    concern: str
    source: str
    dest: str
    note: str = ""


RECIPE = [
    Piece("superpowers", "MIT", "process procedures",
          "skills", "skills",
          "the whole skills library; it is designed to be installed as one"),
    Piece("superpowers", "MIT", "subagent handoff",
          "skills/subagent-driven-development/scripts", "scripts/superpowers", ""),
    # Without this the skills are inert: superpowers delivers its routing
    # pressure through a SessionStart injection, so cherry-picking the skill
    # bodies buys their token cost and none of their behaviour.
    Piece("superpowers", "MIT", "session bootstrap",
          "hooks", "hooks", "the SessionStart injector that makes the skills fire"),
    Piece("ecc", "MIT", "hard blocks",
          "scripts/hooks/block-no-verify.js", "scripts/ecc/block-no-verify.js", ""),
    Piece("ecc", "MIT", "hard blocks",
          "scripts/hooks/config-protection.js", "scripts/ecc/config-protection.js", ""),
    Piece("ecc", "MIT", "destructive classifier",
          "scripts/hooks/gateguard-fact-force.js", "scripts/ecc/gateguard-fact-force.js", ""),
    Piece("ecc", "MIT", "batched stop check",
          "scripts/hooks/post-edit-accumulator.js", "scripts/ecc/post-edit-accumulator.js", ""),
    Piece("ecc", "MIT", "batched stop check",
          "scripts/hooks/stop-format-typecheck.js", "scripts/ecc/stop-format-typecheck.js", ""),
    Piece("gstack", "MIT", "evidence ledger",
          "bin/gstack-evidence", "bin/gstack-evidence", ""),
    Piece("gstack", "MIT", "working-tree fingerprint",
          "bin/gstack-wtree", "bin/gstack-wtree", ""),
    Piece("gstack", "MIT", "stop-time verify gate",
          "bin/gstack-verify-gate", "bin/gstack-verify-gate", ""),
    Piece("spec-kit", "MIT", "large-feature artifacts",
          "presets/lean/commands", "commands",
          "the lean preset only: same artifact contract, about 5 percent of the text"),
    Piece("bmad", "MIT", "review procedure",
          "skills/bmad-build/step-04-review.md", "agents/blind-review.md",
          "blind-then-claims ordering, without the forced finding floor"),
]

# From the matrix's own exclusions list, with the reason each one is left out.
EXCLUDED = [
    ("ecc", "the full catalogue", "286 skill descriptions, about 13k tokens every turn"),
    ("gstack", "the full skills", "6.5k token preamble per invocation, macOS-first browser"),
    ("bmad", "the build pipeline", "uv dependency, three copies of the same pipeline"),
    ("continue", "the index", "IDE-bound, retrieval stages disabled"),
    ("swe-agent", "the tool bundles", "python-only, container-bound"),
    ("aider", "the repository map", "belongs to M3, where it is extended rather than copied"),
]

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)
DESCRIPTION = re.compile(r"^description:\s*(.+?)\s*$", re.M)


@dataclass
class Census:
    skills: int = 0
    commands: int = 0
    agents: int = 0
    always_on_words: int = 0
    on_demand_words: int = 0
    files: int = 0
    missing: list[str] = field(default_factory=list)

    @property
    def always_on_tokens(self) -> int:
        return int(self.always_on_words * 1.3)

    @property
    def on_demand_tokens(self) -> int:
        return int(self.on_demand_words * 1.3)


def describe(path: Path) -> str:
    """The frontmatter description, which is what a host puts in the system prompt."""
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    except OSError:
        return ""
    block = FRONTMATTER.match(head)
    if not block:
        return ""
    found = DESCRIPTION.search(block.group(1))
    return found.group(1).strip().strip('"') if found else ""


def words(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").split())
    except OSError:
        return 0


def build(repos: Path, out: Path) -> Census:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    census = Census()

    for piece in RECIPE:
        source = repos / piece.system / piece.source
        target = out / piece.dest
        if not source.exists():
            census.missing.append(f"{piece.system}/{piece.source}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)

    (out / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps({
        "name": "composition-baseline",
        "description": "Best-of-breed pieces from the studied systems, installed together.",
        "version": "0.1.0",
    }, indent=2), encoding="utf-8")
    (out / "NOTICE").write_text(notice(), encoding="utf-8")

    return measure(out, census)


def measure(out: Path, census: Census | None = None) -> Census:
    census = census or Census()
    for path in out.rglob("*"):
        if path.is_file():
            census.files += 1

    for skill in sorted(out.glob("skills/*/SKILL.md")):
        census.skills += 1
        census.always_on_words += len(describe(skill).split())
        census.on_demand_words += words(skill)
    for other in sorted(out.glob("skills/**/*.md")):
        if other.name != "SKILL.md":
            census.on_demand_words += words(other)

    # Superpowers injects one skill body at session start on every host, so it
    # is always-on cost rather than on-demand. The research card measured this
    # at about 680 tokens including the wrapper.
    bootstrap = out / "skills" / "using-superpowers" / "SKILL.md"
    if bootstrap.exists():
        census.always_on_words += words(bootstrap)

    for command in sorted(out.glob("commands/*.md")):
        census.commands += 1
        census.always_on_words += len(describe(command).split())
        census.on_demand_words += words(command)

    for agent in sorted(out.glob("agents/*.md")):
        census.agents += 1
        census.always_on_words += len(describe(agent).split())
        census.on_demand_words += words(agent)

    return census


# The matrix predicted five conflicts if these pieces were installed together.
# Each is a pattern that can be counted in the assembled text, so the prediction
# is checkable without running anything.
ROUTERS = re.compile(
    r"you MUST use this|MUST invoke|ABSOLUTELY MUST|before any (?:creative )?"
    r"(?:work|response|action)|1% chance|when in doubt", re.I,
)
REVIEW = re.compile(r"\breview(?:er|ing)?\b", re.I)
STATE_DIR = re.compile(r"[\"'`\s(](\.[a-z][a-z0-9_-]*|~/\.[a-z][a-z0-9_-]*)/")
STOP_HOOK = re.compile(r'"Stop"\s*:')


def conflicts(out: Path) -> dict:
    """Count the collisions that only appear once the pieces are together.

    Each piece is coherent alone. The question composition asks is what happens
    when three of them answer the same request, and that is not visible in any
    one repository.
    """
    routing: list[str] = []
    reviewers: list[str] = []
    dirs: dict[str, set[str]] = {}
    stops: list[str] = []

    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.suffix not in (".md", ".json", ".js", ".sh", ""):
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(out)).replace("\\", "/")
        if ROUTERS.search(body):
            routing.append(rel)
        if rel.startswith(("skills/", "agents/")) and REVIEW.search(rel):
            reviewers.append(rel)
        if STOP_HOOK.search(body):
            stops.append(rel)
        for found in STATE_DIR.findall(body):
            dirs.setdefault(found.rstrip("/"), set()).add(rel.split("/")[0])

    interesting = {
        d: sorted(who) for d, who in dirs.items()
        if d.startswith((".claude", ".superpowers", ".specify", ".gstack", ".bmad", "~/."))
    }
    return {
        "routing": routing,
        "reviewers": reviewers,
        "stop_hooks": stops,
        "state_dirs": interesting,
    }


def notice() -> str:
    lines = [
        "This directory is an assembled baseline, not original work. Every file",
        "under it comes from one of the projects below and keeps its own licence.",
        "It exists to measure whether combining these pieces beats using one of",
        "them, which is the question docs/research/complementarity-matrix.md",
        "section 6 poses and this repository had never answered.",
        "",
    ]
    for system in sorted({p.system for p in RECIPE}):
        pieces = [p for p in RECIPE if p.system == system]
        lines.append(f"{system} ({pieces[0].licence})")
        for piece in pieces:
            lines.append(f"    {piece.concern}: {piece.source}")
        lines.append("")
    lines.append("Deliberately excluded, with the reason:")
    for system, what, why in EXCLUDED:
        lines.append(f"    {system} {what}: {why}")
    return "\n".join(lines) + "\n"


def report(census: Census, out: Path) -> None:
    print(f"built              {out}")
    print(f"files              {census.files}")
    print(f"skills             {census.skills}")
    print(f"commands           {census.commands}")
    print(f"agents             {census.agents}")
    print(f"always-on          ~{census.always_on_tokens:,} tokens of descriptions, every turn")
    print(f"on demand          ~{census.on_demand_tokens:,} tokens if everything is read")
    if census.missing:
        print(f"missing            {len(census.missing)}")
        for what in census.missing:
            print(f"                   {what}")

    found = conflicts(out)
    print()
    print("conflicts the matrix predicted, counted in the assembled stack")
    print(f"  competing routers   {len(found['routing'])}")
    for rel in found["routing"][:8]:
        print(f"                      {rel}")
    print(f"  review mechanisms   {len(found['reviewers'])}")
    for rel in found["reviewers"]:
        print(f"                      {rel}")
    print(f"  stop-time hooks     {len(found['stop_hooks'])}  (plus this project's own)")
    print(f"  state directories   {len(found['state_dirs'])}")
    for where, who in sorted(found["state_dirs"].items()):
        print(f"                      {where:<16} from {', '.join(who)}")


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    out = Path(option("--out", str(DEFAULT_OUT)))
    if "--census-only" in argv:
        if not out.exists():
            print(f"nothing built at {out}")
            return 1
        report(measure(out), out)
        return 0

    repos = Path(option("--repos", ""))
    if not repos or not repos.exists():
        print("pass --repos DIR containing clones of the studied systems")
        return 1
    report(build(repos, out), out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
