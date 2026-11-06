"""The analysis fixed in docs/superpowers/specs/2026-11-06-wild-followup-fixes-design.md.

Standard library only. Reads prs.csv and files.jsonl, prints the result and
writes summary.json.
"""
import csv
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1]))
from core.evidence import SOURCE_SUFFIXES  # noqa: E402
from core.surface import TEST_NAME  # noqa: E402

SEED = 20261106
SESOI = 1.5
AGENTS = ["OpenAI_Codex", "Devin", "Copilot", "Cursor", "Claude_Code"]


def classify(files):
    """(changes source, touches a test, changed source lines) by the runtime's own rules."""
    source = [f for f in files if Path(f["filename"]).suffix in SOURCE_SUFFIXES
              and not TEST_NAME.search(f["filename"])]
    tested = any(TEST_NAME.search(f["filename"]) for f in files)
    return bool(source), tested, sum(f["additions"] + f["deletions"] for f in source)


def missed_layout(files):
    """A test file TEST_NAME cannot see: C# `*.Tests` projects, Java `*Test.java` outside test/."""
    return any(("Tests/" in f["filename"] and f["filename"].endswith(".cs"))
               or f["filename"].endswith(("Test.java", "Tests.java")) for f in files)


def mantel_haenszel(strata):
    """Mantel-Haenszel odds ratio, Robins-Breslow-Greenland 95% CI, and the PRs that contributed."""
    sum_r = sum_s = pr = psqr = qs = 0.0
    used = 0
    for rows in strata:
        a = sum(1 for e, y in rows if e and y)
        b = sum(1 for e, y in rows if e and not y)
        c = sum(1 for e, y in rows if not e and y)
        d = sum(1 for e, y in rows if not e and not y)
        n = a + b + c + d
        if not (a + b) or not (c + d):
            continue
        used += n
        r, s, p, q = a * d / n, b * c / n, (a + d) / n, (b + c) / n
        sum_r += r
        sum_s += s
        pr += p * r
        psqr += p * s + q * r
        qs += q * s
    if not sum_r or not sum_s:
        return None
    odds = sum_r / sum_s
    se = math.sqrt(pr / (2 * sum_r ** 2) + psqr / (2 * sum_r * sum_s) + qs / (2 * sum_s ** 2))
    return {"or": odds, "lo": math.exp(math.log(odds) - 1.96 * se),
            "hi": math.exp(math.log(odds) + 1.96 * se), "prs": used}


def _lcomb(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]]."""
    n, row, col = a + b + c + d, a + b, a + c

    def logp(x):
        return _lcomb(row, x) + _lcomb(n - row, col - x) - _lcomb(n, col)

    observed = logp(a)
    return min(1.0, sum(math.exp(logp(x)) for x in range(max(0, col - (n - row)), min(row, col) + 1)
                        if logp(x) <= observed + 1e-9))


def _solve(matrix, vector):
    k = len(vector)
    m = [row[:] + [v] for row, v in zip(matrix, vector)]
    for i in range(k):
        pivot = max(range(i, k), key=lambda r: abs(m[r][i]))
        m[i], m[pivot] = m[pivot], m[i]
        for r in range(k):
            if r != i and m[i][i]:
                factor = m[r][i] / m[i][i]
                m[r] = [x - factor * y for x, y in zip(m[r], m[i])]
    return [m[i][k] / m[i][i] for i in range(k)]


def logistic(xs, ys, iterations=60):
    """Newton-Raphson logistic regression; coefficients and Wald standard errors."""
    k = len(xs[0])
    beta = [0.0] * k
    hessian = None
    for _ in range(iterations):
        hessian = [[0.0] * k for _ in range(k)]
        gradient = [0.0] * k
        for x, y in zip(xs, ys):
            eta = max(-30.0, min(30.0, sum(b * v for b, v in zip(beta, x))))
            p = 1 / (1 + math.exp(-eta))
            w = p * (1 - p)
            for j in range(k):
                gradient[j] += (y - p) * x[j]
                for col in range(k):
                    hessian[j][col] += w * x[j] * x[col]
        step = _solve(hessian, gradient)
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-9:
            break
    errors = [math.sqrt(max(_solve(hessian, [1.0 if r == j else 0.0 for r in range(k)])[j], 0.0))
              for j in range(k)]
    return beta, errors


def by_repo(prs, outcome):
    groups = defaultdict(list)
    for pr in prs:
        groups[pr["repo"]].append((pr["no_test"], outcome(pr)))
    return list(groups.values())


def permuted(prs, rng):
    """Follow-up-fix labels shuffled within each repository."""
    groups = defaultdict(list)
    for pr in prs:
        groups[pr["repo"]].append(pr)
    out = {}
    for rows in groups.values():
        labels = [pr["event"] for pr in rows]
        rng.shuffle(labels)
        out.update({pr["pr_id"]: y for pr, y in zip(rows, labels)})
    return out


def planted(prs, odds_ratio, rng):
    """Synthetic outcomes at the observed base rate, with *no test* raising the odds by odds_ratio."""
    base = sum(pr["event"] for pr in prs) / len(prs)
    odds = base / (1 - base)
    out = {}
    for pr in prs:
        o = odds * (odds_ratio if pr["no_test"] else 1)
        out[pr["pr_id"]] = rng.random() < o / (1 + o)
    return out


def main():
    labels = {r["pr_id"]: r for r in csv.DictReader(open(HERE / "prs.csv", encoding="utf-8"))}
    latest = {}
    for line in (HERE / "files.jsonl").read_text(encoding="utf-8").splitlines():
        if line:
            record = json.loads(line)
            latest[record["pr_id"]] = record
    fetched = list(latest.values())
    drops = Counter()
    prs = []
    for record in fetched:
        row = labels[record["pr_id"]]
        if record["files"] is None:
            drops["file list not fetchable"] += 1
            continue
        if record["capped"]:
            drops["file list capped at 3,000"] += 1
            continue
        source, tested, size = classify(record["files"])
        if not source:
            drops["no non-test source change"] += 1
            continue
        prs.append({"pr_id": record["pr_id"], "repo": row["repo"], "agent": row["agent"],
                    "event": row["ver_event"] == "1", "no_test": not tested, "size": size,
                    "missed_layout": not tested and missed_layout(record["files"])})
    drops["not yet fetched"] = len(labels) - len(fetched)

    a = sum(1 for p in prs if p["no_test"] and p["event"])
    b = sum(1 for p in prs if p["no_test"] and not p["event"])
    c = sum(1 for p in prs if not p["no_test"] and p["event"])
    d = sum(1 for p in prs if not p["no_test"] and not p["event"])
    rng = random.Random(SEED)

    # Forward: an association planted at twice the odds has to be found.
    forward = mantel_haenszel(by_repo(prs, lambda p, o=planted(prs, 2.0, rng): o[p["pr_id"]]))
    power = {}
    for ratio in (SESOI, 2.0):
        found = 0
        for _ in range(200):
            outcome = planted(prs, ratio, rng)
            result = mantel_haenszel(by_repo(prs, lambda p, o=outcome: o[p["pr_id"]]))
            found += bool(result and result["lo"] > 1)
        power[str(ratio)] = found / 200

    primary = mantel_haenszel(by_repo(prs, lambda p: p["event"]))
    # Adversarial: the same pipeline on labels shuffled within repositories.
    extreme = total = 0
    for _ in range(1000):
        outcome = permuted(prs, rng)
        result = mantel_haenszel(by_repo(prs, lambda p, o=outcome: o[p["pr_id"]]))
        if result is None:
            continue
        total += 1
        extreme += abs(math.log(result["or"])) >= abs(math.log(primary["or"])) - 1e-12
    by_agent = defaultdict(list)
    for p in prs:
        by_agent[p["agent"]].append((p["no_test"], p["event"]))
    agent_mh = mantel_haenszel(list(by_agent.values()))

    xs = [[1.0, float(p["no_test"]), math.log1p(p["size"])]
          + [float(p["agent"] == agent) for agent in AGENTS[1:]] for p in prs]
    beta, errors = logistic(xs, [float(p["event"]) for p in prs])
    adjusted = {"or": math.exp(beta[1]), "lo": math.exp(beta[1] - 1.96 * errors[1]),
                "hi": math.exp(beta[1] + 1.96 * errors[1]), "size_or_per_log_line": math.exp(beta[2])}

    if primary["lo"] > 1:
        reading = "supports the premise: go to the dynamic stage"
    elif primary["hi"] < 1:
        reading = "PRs with a test draw more follow-up fixes"
    elif primary["hi"] < SESOI:
        reading = "no support at the smallest effect of interest"
    else:
        reading = "inconclusive: the interval covers both 1 and 1.5"

    summary = {
        "population": len(prs), "drops": dict(drops), "repositories": len({p["repo"] for p in prs}),
        "table": {"no_test_fix": a, "no_test_clean": b, "test_fix": c, "test_clean": d},
        "rates": {"no_test": a / (a + b) if a + b else None, "test": c / (c + d) if c + d else None},
        "primary_mh_by_repo": primary, "permutation_p": extreme / total if total else None,
        "permutations": total, "forward_planted_or2": forward, "power": power,
        "fisher_pooled_p": fisher(a, b, c, d), "mh_by_agent": agent_mh, "logistic_size_agent": adjusted,
        "no_test_with_missed_layout": sum(p["missed_layout"] for p in prs),
        "reading": reading,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
