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
    """One pass over the suite, as task to outcome.

    A file holding replicates is not a pass, and collapsing one to its last run
    would answer the flip-rate question with a quarter of the data and no sign
    that anything was dropped. `--calibrate` is the mode that reads replicates.
    """
    runs = json.loads(path.read_text(encoding="utf-8"))
    mine = [r["task"] for r in runs if r["arm"] == arm]
    repeated = sorted({t for t in mine if mine.count(t) > 1})
    if repeated:
        raise ValueError(
            f"{path.name} holds repeated {arm} runs of {', '.join(repeated[:4])}"
            " — that is not one pass. Use --calibrate to read replicates.")
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


def discordant_pairs_needed(share_favouring: float = 0.75) -> int:
    """Disagreeing pairs an effect of this shape needs, at 0.05 and 80 percent."""
    edge = 2 * share_favouring - 1
    return int(((Z_ALPHA + Z_BETA) / edge) ** 2 + 0.5) if edge > 0 else 0


def runs_for(discordance: float, share_favouring: float = 0.75) -> int:
    """Paired runs, given a **measured** rate of between-arm disagreement.

    Not derived from the within-arm flip rate. `paired_runs_needed` did that, on
    the reasoning that a task must be able to change answer before the arms can
    disagree about it, and the reasoning is wrong: a baseline that fails
    deterministically and a treatment that succeeds deterministically flip never
    and disagree always. Zero flip rate, complete discordance. The flip rate
    neither bounds nor estimates discordance, so dividing by it produced a run
    count with nothing behind it.

    Discordance has to come from a pilot that runs both arms. There is no way to
    get it from one.
    """
    needed = discordant_pairs_needed(share_favouring)
    return int(needed / discordance + 0.5) if discordance > 0 else 0


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

    discordant = discordant_pairs_needed()
    print()
    print("to detect an arm winning three of every four disagreements, at 0.05 and")
    print(f"80 percent power: {discordant} pairs where the two arms disagree.")
    print()
    print("This does not convert into a number of runs from the flip rate above, and")
    print("it used to. Flipping is within one arm; disagreement is between two, and a")
    print("baseline that fails every time against a treatment that succeeds every time")
    print("flips never and disagrees always. Run both arms on a pilot, measure how")
    print("often they actually disagree, and put that through `runs_for`.")


def calibrate(path: Path, arm: str = "vanilla", low: float = 0.3, high: float = 0.7) -> None:
    """Per-task resolve rate over repeated plain passes, and what each is worth.

    Only one band is useless. A task the baseline always resolves cannot show an
    improvement, ever. A task it never resolves is prime headroom: if an arm can
    overturn it that is exactly the evidence being sought, and if no arm can, it
    costs one run to find out.

    Three passes cannot classify a task on their own. One of these moved from 67
    percent to 0 between two calibrations of identical settings, so the rates
    here are estimates and the band matters more than the number.
    """
    runs = json.loads(path.read_text(encoding="utf-8"))
    by_task: dict[str, list[bool]] = {}
    for run in runs:
        if run["arm"] == arm:
            by_task.setdefault(run["task"], []).append(bool(run["resolved"]))

    rows = sorted(((t, sum(r) / len(r), len(r)) for t, r in by_task.items()),
                  key=lambda x: x[1])
    useful = [t for t, rate, _ in rows if rate <= high]
    ceiling = [t for t, rate, _ in rows if rate > high]

    print(f"{'task':<18}{'resolved':>10}{'passes':>8}  verdict")
    for task, rate, n in rows:
        verdict = ("no headroom, cannot show an improvement" if rate > high else
                   "headroom: an arm has to overturn it" if rate < low else
                   "discriminates")
        print(f"{task:<18}{rate:>9.0%}{n:>8}  {verdict}")
    print()
    print(f"carries information  {len(useful):>2} of {len(rows)}")
    print(f"no headroom          {len(ceiling):>2}   {', '.join(ceiling) or '-'}")
    if rows:
        share = len(useful) / len(rows)
        print()
        print(f"{share:.0%} of this suite can move."
              f"  {'usable' if share >= 0.75 else 'not usable as a measuring instrument yet'}")


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
