"""SPIKE - gate arm against vanilla arm, on the PAIRED chunks sweep.

results/chunks is the one place both arms ran the same tasks, with the same
model, in the same sweep - so a difference between them is the arm and not a
sweep or a model. Every resolved patch in it goes through the B7 probe.

The question: do agents working under this project's gate write tests that pin
their change better than agents working without it? That is the central claim
("the gate improves the work"), measured on test quality rather than on the
resolve rate that never moved.

    python chunks_probe.py 3/10 out3.json
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/Satyam/AppData/Local/Temp/claude/e--ElevenPowers/cf4ea1a0-0d66-483c-af19-d5e4658f485a/scratchpad")
import agent_probe  # noqa: E402  (imports probe, which points EP_MINED at prevalence)

os.environ["EP_MINED"] = "E:/ep-corpus/paired.json"   # the corpus that defines all 25 chunk tasks
from eval.mined import load as load_mined  # noqa: E402

RESULTS = Path("E:/ElevenPowers/results")


def bundles():
    out = []
    for m in sorted((RESULTS / "chunks").rglob("manifest.json")):
        b = m.parent
        g, p = b / "grade.json", b / "patch.diff"
        if not (g.exists() and p.exists()) or p.stat().st_size == 0:
            continue
        man = json.loads(m.read_text(encoding="utf-8"))
        if json.loads(g.read_text(encoding="utf-8")).get("outcome") != "resolved":
            continue
        out.append((man["task"], man["arm"], man.get("model_asked") or man.get("model"), b))
    return out


def main():
    shard, n = map(int, sys.argv[1].split("/"))
    out = Path(sys.argv[2])
    tasks = {t.name: t for t in load_mined()}
    mine = bundles()[shard::n]
    report = []
    with tempfile.TemporaryDirectory(prefix=f"ep-chunks-{shard}-", ignore_cleanup_errors=True) as tmp:
        for task_name, arm, model, bundle in mine:
            # One directory per PATCH, not per task: several patches share a
            # task here, and a shared path would lay the second patch over the
            # first one's tree.
            hold = Path(tmp) / bundle.name
            hold.mkdir(parents=True)
            t0 = time.time()
            try:
                r = agent_probe.one(tasks[task_name], bundle, hold)
            except Exception as e:  # noqa: BLE001
                r = {"why": f"{type(e).__name__}: {e}"}
            r.update({"task": task_name, "arm": arm, "model": model,
                      "bundle": str(bundle.relative_to(RESULTS)).replace("\\", "/"),
                      "seconds": round(time.time() - t0)})
            report.append(r)
            ms = [m for m in r.get("mutants", []) if m["verdict"] != "not generated"]
            live = sum(m["verdict"] == "SURVIVED" for m in ms)
            said = r.get("why") or f"{live}/{len(ms)} survived revert_killed={r['revert_killed']} tests={len(r['tests_in_patch'])}"
            print(f"{task_name:24s} {arm:8s} {said} ({r['seconds']}s)", flush=True)
            out.write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
