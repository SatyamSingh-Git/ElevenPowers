"""Does our own evidence measure anything?

    python -m eval.discriminate --bundles results

PLAN §5.10 says a check is not evidence until it has been shown to
**discriminate** — that a record which would have passed anyway proves nothing
about the change it is attached to. Phase B2.1 asks that question of our own
ledger, against runs already paid for, for nothing.

It ran into a prior question first, and this module reports that one.

**A passing suite record was decided by the exit code alone.** `core/parsers.py`
counted the failures and then ignored them, taking `exit_code == 0` as the
verdict. A shell pipeline exits with the status of its *last* command, so
`python -m pytest tests -q 2>&1 | tail -80` returns `tail`'s zero however pytest
finished. 288 of the 295 passing suite records preserved in `results/` were run
through exactly that shape, and **123 of them carry `failed > 0`** — the worst
reading `failed=5, passed=0` and saying PASS.

That is a third fact in a family this project keeps rediscovering. R5
established that a completed process and an executed test are different things.
This adds that an executed test and a *passing* test are different things too.
Fixed in `core/parsers.py`; the probe is
`tests/test_audit_probes.py::test_a_suite_with_failures_is_not_a_passing_suite`,
and it was watched failing before the fix and passing after, with a control
asserting a genuinely green piped suite is still recorded green.

**Why the history can be corrected without re-running anything.** Every record
carries the counts the decision should have used. So the corrected result is a
pure function of data already on disk: no agent, no API, no test run. That is
the whole reason this measurement is free.

**What this can and cannot say.** It reports what the evidence layer recorded
and what it should have recorded. It does **not** establish that a false pass
caused a run to fail. Affected runs ran a median of five suite records against
two for unaffected ones, so exposure to the defect is confounded with how much
trouble a run was in — a struggling agent runs more suites, and more suites is
more chances to hit this. The causal arrow may point either way, and nothing
here separates them. `--verbose` prints the counts that make the confound
visible rather than burying it.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path


def recorded(bundle: Path) -> tuple[dict, dict, list[dict]] | None:
    """A run's manifest, grade and evidence, or None if it kept no ledger."""
    ledger, manifest = bundle / "ledger.json", bundle / "manifest.json"
    if not (ledger.exists() and manifest.exists()):
        return None
    try:
        man = json.loads(manifest.read_text(encoding="utf-8"))
        led = json.loads(ledger.read_text(encoding="utf-8"))
        grade = bundle / "grade.json"
        got = json.loads(grade.read_text(encoding="utf-8")) if grade.exists() else {}
    except (OSError, json.JSONDecodeError):
        return None
    return man, got, led.get("evidence") or []


def misrecorded(evidence: list[dict]) -> list[dict]:
    """Suite records that said PASS while holding a non-zero failure count.

    The counts are the record's own. Correcting them needs no execution, which
    is why the whole census costs nothing.
    """
    return [r for r in evidence
            if r.get("kind") == "test_suite"
            and r.get("result") == "pass"
            and (r.get("failed") or 0) > 0]


def swallows_exit_code(command: str) -> bool:
    """Would this command's exit status be somebody else's?

    Only pipelines are counted. `&&` chains report the last command's status
    too, but there the last command is usually the one that matters, whereas a
    pipe into `tail` is always a formatting step standing between the runner and
    the verdict.
    """
    return "|" in (command or "")


def census(root: Path) -> dict:
    runs = []
    suites = piped = wrong = 0
    worst = (0, "", "")
    for manifest in sorted(root.rglob("manifest.json")):
        found = recorded(manifest.parent)
        if not found:
            continue
        man, got, evidence = found
        passing = [r for r in evidence
                   if r.get("kind") == "test_suite" and r.get("result") == "pass"]
        bad = misrecorded(evidence)
        suites += len(passing)
        piped += sum(swallows_exit_code(r.get("command", "")) for r in passing)
        wrong += len(bad)
        for r in bad:
            if (r.get("failed") or 0) > worst[0]:
                worst = (r["failed"], r.get("passed", 0), man.get("task", "?"))
        runs.append({
            "task": man.get("task"), "arm": man.get("arm"),
            "outcome": got.get("outcome"),
            "suites": len([r for r in evidence if r.get("kind") == "test_suite"]),
            "wrong": len(bad),
        })
    return {"runs": runs, "passing_suites": suites, "piped": piped,
            "wrong": wrong, "worst": worst}


def report(root: Path, verbose: bool) -> int:
    data = census(root)
    runs, total = data["runs"], data["passing_suites"]
    if not runs:
        print(f"no bundles with a preserved ledger under {root}")
        return 1

    affected = [r for r in runs if r["wrong"]]
    print(f"runs with a preserved ledger : {len(runs)}")
    print(f"passing suite records        : {total}")
    if total:
        print(f"  behind a pipe              : {data['piped']} ({data['piped']/total:.0%})")
        print(f"  PASS with failures counted : {data['wrong']} ({data['wrong']/total:.0%})")
    failed, passed, task = data["worst"]
    if failed:
        print(f"  worst single record        : failed={failed}, passed={passed} ({task})")
    print(f"runs carrying at least one   : {len(affected)} of {len(runs)} "
          f"({len(affected)/len(runs):.0%})")

    print("\noutcome, by whether the run carried a falsely-passing suite record:")
    for label, group in (("carried one", affected),
                         ("carried none", [r for r in runs if not r["wrong"]])):
        counts = Counter(r["outcome"] for r in group)
        print(f"  {label:13s} n={len(group):3d}  " +
              "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    # The comparison above is the tempting one and it is not clean. Say so here,
    # with the number that makes it not clean, rather than in a footnote.
    a = [r["suites"] for r in affected] or [0]
    u = [r["suites"] for r in runs if not r["wrong"]] or [0]
    print(f"\nsuite records run, median    : {statistics.median(a):.0f} when affected, "
          f"{statistics.median(u):.0f} when not")
    print("A run that never ran a failing suite cannot exhibit this defect, and a run in")
    print("trouble runs more suites. Exposure is confounded with difficulty, so the")
    print("outcome split above is NOT evidence that the defect caused the failures.")

    if verbose:
        print("\nruns that did not resolve and carried at least one:")
        for r in sorted(affected, key=lambda r: (r["outcome"] or "", r["task"] or "")):
            if r["outcome"] != "resolved":
                print(f"  {r['task']:24s} {r['arm']:8s} {r['outcome']:10s} "
                      f"suites={r['suites']:3d} wrong={r['wrong']}")

    print("\nWhat this changes: for every affected run, the obligation \"the related test")
    print("suite passes\" could be met by a suite that did not pass. Those runs were not")
    print("measuring what the ledger says they measured. Fixed in core/parsers.py; the")
    print("probe is in tests/test_audit_probes.py and was seen to flip.")
    print("\nStill unanswered, and the actual §5.10 question: of the records that really")
    print("did pass, how many would have passed with the change reverted? That needs")
    print("execution against the base tree, not arithmetic on saved counts.")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rest = [a for a in argv[1:] if not a.startswith("-")]
    if "--bundles" not in argv or not rest:
        print(__doc__)
        return 1
    return report(Path(rest[0]), "--verbose" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
