"""How much of a live result is the agent, and how much is chance.

Usage: python -m eval.noise pass1.json pass2.json [--arm vanilla]
       python -m eval.noise runs.json --calibrate [--arm vanilla]

Two runs of the identical configuration should agree. They do not: on the first
sixteen-task suite, one plain pass resolved eleven and another resolved fifteen,
with four tasks changing answer in between. An effect worth detecting is smaller
than that, so any single-pass comparison between arms is reading noise.

This is the measurement the plan called for in week one, for exactly this
reason, and skipping it cost two arm comparisons that could never have meant
anything. It reports the flip rate, sorts tasks by whether they discriminate at
all, and says how many paired runs an honest answer would take.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

Z_ALPHA = 1.96      # two-sided 0.05
Z_BETA = 0.8416     # 80 percent power


def outcomes(path: Path, arm: str) -> dict[str, bool]:
    runs = json.loads(path.read_text(encoding="utf-8"))
    return {r["task"]: bool(r["resolved"]) for r in runs if r["arm"] == arm}


def paired_runs_needed(flip_rate: float, share_favouring: float = 0.75) -> tuple[int, int]:
    """Paired runs to detect an effect, given how often a task changes answer.

    Only pairs where the two arms disagree carry information, and how often that
    happens is bounded by how often a task's outcome moves at all. The usual
    McNemar sizing applies: with `share_favouring` of the discordant pairs going
    the treatment's way, detecting that at 0.05 and 80 percent power needs
    ((z_a + z_b) / (2 * share - 1)) ** 2 of them.
    """
    edge = 2 * share_favouring - 1
    if edge <= 0:
        return 0, 0
    discordant = ((Z_ALPHA + Z_BETA) / edge) ** 2
    if flip_rate <= 0:
        return int(discordant + 0.5), 0
    return int(discordant + 0.5), int(discordant / flip_rate + 0.5)


def report(first: dict[str, bool], second: dict[str, bool], arm: str) -> None:
    shared = sorted(set(first) & set(second))
    if not shared:
        print("no tasks in common")
        return

    flipped = [t for t in shared if first[t] != second[t]]
    always = [t for t in shared if first[t] and second[t]]
    never = [t for t in shared if not first[t] and not second[t]]
    flip_rate = len(flipped) / len(shared)

    print(f"arm                {arm}")
    print(f"tasks in common    {len(shared)}")
    print(f"pass one resolved  {sum(first[t] for t in shared)}/{len(shared)}"
          f"  ({sum(first[t] for t in shared) / len(shared):.0%})")
    print(f"pass two resolved  {sum(second[t] for t in shared)}/{len(shared)}"
          f"  ({sum(second[t] for t in shared) / len(shared):.0%})")
    print(f"changed answer     {len(flipped)}/{len(shared)}  ({flip_rate:.0%})"
          f"   on identical settings")
    print()
    print("what each task is worth measuring with")
    print(f"  always resolved  {len(always):>2}  {', '.join(always) or '-'}")
    print(f"  unstable         {len(flipped):>2}  {', '.join(flipped) or '-'}")
    print(f"  never resolved   {len(never):>2}  {', '.join(never) or '-'}")
    print()
    print("A task the baseline always resolves cannot show an improvement, and one it")
    print("never resolves is only useful if an arm can actually overturn it. The rest")
    print("of the suite is noise generators.")

    discordant, pairs = paired_runs_needed(flip_rate)
    print()
    print(f"to detect an arm winning three of every four disagreements, at 0.05 and")
    print(f"80 percent power: {discordant} discordant pairs, which at this flip rate")
    print(f"means about {pairs} paired runs, so {pairs * 2} agent runs per comparison.")


def calibrate(path: Path, arm: str = "vanilla", low: float = 0.3, high: float = 0.7) -> None:
    """Per-task resolve rate over repeated plain passes, and what each is worth.

    A task the baseline always resolves cannot show an improvement, and one it
    never resolves can only be overturned by an arm that is genuinely better at
    the underlying work. Neither is useless, but a suite made mostly of the first
    kind cannot measure anything, which is what the first sixteen tasks turned
    out to be.
    """
    runs = json.loads(path.read_text(encoding="utf-8"))
    by_task: dict[str, list[bool]] = {}
    for run in runs:
        if run["arm"] == arm:
            by_task.setdefault(run["task"], []).append(bool(run["resolved"]))

    rows = sorted(((t, sum(r) / len(r), len(r)) for t, r in by_task.items()),
                  key=lambda x: x[1])
    useful = [t for t, rate, _ in rows if low <= rate <= high]
    ceiling = [t for t, rate, _ in rows if rate > high]
    floor = [t for t, rate, _ in rows if rate < low]

    print(f"{'task':<18}{'resolved':>10}{'passes':>8}  verdict")
    for task, rate, n in rows:
        verdict = ("discriminates" if low <= rate <= high else
                   "no headroom" if rate > high else "rarely or never resolved")
        print(f"{task:<18}{rate:>9.0%}{n:>8}  {verdict}")
    print()
    print(f"discriminating   {len(useful):>2} of {len(rows)}")
    print(f"no headroom      {len(ceiling):>2}   {', '.join(ceiling) or '-'}")
    print(f"rarely resolved  {len(floor):>2}   {', '.join(floor) or '-'}")
    if rows:
        share = len(useful) / len(rows)
        print()
        print(f"{share:.0%} of this suite carries information."
              f"  {'usable' if share >= 0.5 else 'not usable as a measuring instrument yet'}")


def main(argv: list[str]) -> int:
    files = [a for a in argv[1:] if not a.startswith("--")]
    arm = argv[argv.index("--arm") + 1] if "--arm" in argv else "vanilla"
    if "--calibrate" in argv:
        if not files:
            print(__doc__)
            return 1
        calibrate(Path(files[0]), arm)
        return 0
    if len(files) < 2:
        print(__doc__)
        return 1
    report(outcomes(Path(files[0]), arm), outcomes(Path(files[1]), arm), arm)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
