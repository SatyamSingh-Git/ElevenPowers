"""Analysis for B7b / B8 / B9, written BEFORE the results were read.

Metrics fixed in advance, so the result cannot choose them:
  B8 (feedback)  - per run: fraction of the task's original survivors now killed.
                   Per task: mean over replicates, per arm. Primary comparison:
                   paired difference mutants - generic across tasks, exact sign
                   test. Validity: survive control after, no weakened tests,
                   source untouched, no tautological tests.
  B9 (gate arm)  - per task: mean survival fraction per arm over resolved
                   patches; paired difference gate - vanilla; exact sign test.
                   Plus vacuity (revert survived) and tests written, per arm.
  Raters         - raw agreement and Cohen's kappa, 4-way and MEANINGFUL-vs-not;
                   the gate's criterion is items BOTH blind raters call MEANINGFUL.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

S = Path("C:/Users/Satyam/AppData/Local/Temp/claude/e--ElevenPowers/cf4ea1a0-0d66-483c-af19-d5e4658f485a/scratchpad")


def sign_test(pos: int, neg: int) -> float:
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    p = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def kappa(a: list, b: list) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def b8():
    runs = []
    for rep, d in ((1, "b8"), (2, "b8-rep2")):
        for p in sorted((S / d).glob("*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            r["rep"] = rep
            runs.append(r)
    ok = [r for r in runs if not r.get("why")]
    bad = [r for r in runs if r.get("why")]
    print(f"\n=== B8 feedback: {len(ok)} usable runs, {len(bad)} failed ===")
    for r in bad:
        print(f"  FAILED {r['task']} {r['arm']} rep{r['rep']}: {r['why'][:90]}")
    invalid = [r for r in ok if not r["survive_ok_after"] or not r["baseline_green_after"]]
    for r in invalid:
        print(f"  INVALID (control after): {r['task']} {r['arm']} rep{r['rep']} "
              f"survive_ok={r['survive_ok_after']} baseline_green={r['baseline_green_after']}")
    valid = [r for r in ok if r not in invalid]
    cost = sum(r["cost"] for r in ok)
    print(f"  total cost ${cost:.2f} over {len(ok)} runs (${cost / max(1, len(ok)):.2f}/run)")
    print(f"  source touched (restored): {sum(bool(r['source_touched_and_restored']) for r in ok)} runs"
          f" | tautology markers: {sum(bool(r['tautology_markers']) for r in ok)} runs"
          f" | weakened (killed->survived): {sum(r['killed_now_survived'] for r in ok)} mutants"
          f" | new tests red on unmutated tree: {sum(r['new_red_on_unmutated_tree'] > 0 for r in ok)} runs")
    by = defaultdict(lambda: defaultdict(list))
    for r in valid:
        by[r["task"]][r["arm"]].append(r["survivors_now_killed"] / r["survivors_before"])
    tot = {a: [0, 0] for a in ("generic", "mutants")}
    for r in valid:
        tot[r["arm"]][0] += r["survivors_now_killed"]
        tot[r["arm"]][1] += r["survivors_before"]
    print(f"\n  {'task':<24}{'generic':>16}{'mutants':>16}")
    pos = neg = tie = 0
    for t in sorted(by):
        g, m = by[t].get("generic", []), by[t].get("mutants", [])
        gs = ", ".join(f"{x:.2f}" for x in g) or "-"
        ms = ", ".join(f"{x:.2f}" for x in m) or "-"
        print(f"  {t:<24}{gs:>16}{ms:>16}")
        if g and m:
            d = sum(m) / len(m) - sum(g) / len(g)
            pos += d > 1e-9
            neg += d < -1e-9
            tie += abs(d) <= 1e-9
    for a, (k, n) in tot.items():
        print(f"  {a:<8}: {k}/{n} original survivors killed ({k / max(1, n):.0%})")
    # The machine was heavily loaded during these runs (36 agents, 10 probe
    # shards). A suite that times out is counted as a kill, which would inflate
    # exactly the number above - so the timeout kills are counted and removed
    # in a sensitivity line rather than trusted.
    for a in ("generic", "mutants"):
        tk = sum(1 for r in valid if r["arm"] == a
                 for b, x in zip(r["before"], r["after"]) if b == "SURVIVED" and x == "killed (timeout)")
        k, n = tot[a]
        print(f"  {a:<8}: of those kills, {tk} were TIMEOUTS; excluding them: "
              f"{k - tk}/{n} ({(k - tk) / max(1, n):.0%})")
    print(f"  per task, mutants arm better {pos}, worse {neg}, tied {tie}; "
          f"exact two-sided sign test p = {sign_test(pos, neg):.3f}")


def b9():
    rows = []
    for p in sorted(S.glob("chunks_*.json")):
        rows += json.loads(p.read_text(encoding="utf-8"))
    ok = [r for r in rows if not r.get("why")]
    print(f"\n=== B9 gate vs vanilla (paired chunks sweep): {len(ok)} usable patches, "
          f"{len(rows) - len(ok)} failed ===")
    for r in rows:
        if r.get("why"):
            print(f"  FAILED {r['task']} {r['arm']}: {r['why'][:90]}")
    per = defaultdict(lambda: defaultdict(list))
    agg = {a: [0, 0] for a in ("gate", "vanilla")}
    vac = Counter()
    tests = defaultdict(list)
    timeouts = 0
    for r in ok:
        ms = [m for m in r["mutants"] if m["verdict"] != "not generated"]
        s = sum(m["verdict"] == "SURVIVED" for m in ms)
        timeouts += sum(m["verdict"] == "killed (timeout)" for m in ms)
        agg[r["arm"]][0] += s
        agg[r["arm"]][1] += len(ms)
        if ms:
            per[r["task"]][r["arm"]].append(s / len(ms))
        vac[r["arm"]] += not r["revert_killed"]
        tests[r["arm"]].append(len(r["tests_in_patch"]))
    for a, (s, n) in agg.items():
        k = sum(1 for r in ok if r["arm"] == a)
        print(f"  {a:<8}: {s}/{n} mutants survived ({s / max(1, n):.0%}) over {k} patches | "
              f"VACUOUS (revert survived): {vac[a]} | mean test files in patch: "
              f"{sum(tests[a]) / max(1, len(tests[a])):.2f}")
    pos = neg = tie = 0
    for t in per:
        g, v = per[t].get("gate", []), per[t].get("vanilla", [])
        if g and v:
            d = sum(g) / len(g) - sum(v) / len(v)
            pos += d > 1e-9       # gate survives MORE = gate worse
            neg += d < -1e-9
            tie += abs(d) <= 1e-9
    print(f"  per task (both arms present): gate survival higher on {pos}, lower on {neg}, tied {tie}; "
          f"sign test p = {sign_test(pos, neg):.3f}")
    print(f"  mutants counted as killed by TIMEOUT (load artefact check): {timeouts}")


def raters():
    key = {k["id"]: k for k in json.loads((S / "blind_key.json").read_text(encoding="utf-8"))}
    author = json.loads((S / "author_labels.json").read_text(encoding="utf-8"))["labels"]
    got = {}
    for name in ("opus", "sonnet"):
        p = S / f"rater_{name}.json"
        if p.exists():
            got[name] = {k: v["label"] for k, v in json.loads(p.read_text(encoding="utf-8")).items()}
    print(f"\n=== Blind review: raters present {sorted(got)} ===")
    ids = sorted(key)
    for name, lab in got.items():
        print(f"  {name:<7}: {dict(Counter(lab[i] for i in ids))}")
    print(f"  author : {dict(Counter(author[i] for i in ids))}  (unblinded, registered first)")
    pairs = [("opus", "sonnet"), ("opus", "author"), ("sonnet", "author")]
    table = {**got, "author": author}
    for a, b in pairs:
        if a in table and b in table:
            x = [table[a][i] for i in ids]
            y = [table[b][i] for i in ids]
            bx = [v == "MEANINGFUL" for v in x]
            by_ = [v == "MEANINGFUL" for v in y]
            print(f"  {a} vs {b}: agree {sum(p == q for p, q in zip(x, y))}/27, kappa {kappa(x, y):.2f}; "
                  f"MEANINGFUL-vs-not agree {sum(p == q for p, q in zip(bx, by_))}/27, kappa {kappa(bx, by_):.2f}")
    if len(got) == 2:
        both = [i for i in ids if got["opus"][i] == "MEANINGFUL" and got["sonnet"][i] == "MEANINGFUL"]
        eq = [i for i in ids if got["opus"][i] == "EQUIVALENT" and got["sonnet"][i] == "EQUIVALENT"]
        print(f"  BOTH blind raters MEANINGFUL: {len(both)}/27 | BOTH EQUIVALENT: {len(eq)}/27")
        split = [i for i in ids if len({got['opus'][i], got['sonnet'][i], author[i]}) > 1]
        for i in split:
            k = key[i]
            print(f"    {i} {k['task']:<22} {k['op']:<18} opus={got['opus'][i]:<10} "
                  f"sonnet={got['sonnet'][i]:<10} author={author[i]}")


if __name__ == "__main__":
    for part in (sys.argv[1:] or ["raters", "b8", "b9"]):
        {"raters": raters, "b8": b8, "b9": b9}[part]()
