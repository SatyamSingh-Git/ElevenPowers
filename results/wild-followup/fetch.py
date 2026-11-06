"""Fetch each PR's changed files through the GitHub CLI, once, into files.jsonl.

Resumable: PRs already in files.jsonl are skipped. A refusal for the rate limit
waits for the reset and retries; any other failure is stored as the PR's error,
so it is counted as a drop rather than lost.
"""
import csv
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "files.jsonl"
API_CAP = 3000
WORKERS = 4


def files_of(repo, number):
    while True:
        done = subprocess.run(["gh", "api", f"repos/{repo}/pulls/{number}/files", "--paginate",
                               "--jq", ".[] | {filename, status, additions, deletions}"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if done.returncode == 0:
            return [json.loads(line) for line in done.stdout.splitlines() if line.strip()], ""
        said = (done.stdout + done.stderr).strip()
        if "rate limit" in said.lower() or "HTTP 429" in said:
            reset = subprocess.run(["gh", "api", "rate_limit", "--jq", ".resources.core.reset"],
                                   capture_output=True, text=True).stdout.strip()
            time.sleep(max(int(reset or 0) - time.time(), 0) + 5 if reset.isdigit() else 60)
            continue
        return None, said[-300:]


def main():
    # Only a fetched list counts as done, so a re-run retries refusals such as
    # GitHub's "not available due to heavy server load". The last record wins.
    done = set()
    if OUT.exists():
        done = {r["pr_id"] for r in map(json.loads, OUT.read_text(encoding="utf-8").splitlines())
                if r["files"] is not None}
    rows = [r for r in csv.DictReader(open(HERE / "prs.csv", encoding="utf-8")) if r["pr_id"] not in done]
    lock = threading.Lock()

    def fetch(row):
        files, error = files_of(row["repo"], row["number"])
        return {"pr_id": row["pr_id"], "files": files, "error": error,
                "capped": files is not None and len(files) >= API_CAP}

    with open(OUT, "a", encoding="utf-8") as out, ThreadPoolExecutor(WORKERS) as pool:
        for i, record in enumerate(pool.map(fetch, rows), 1):
            with lock:
                out.write(json.dumps(record) + "\n")
                out.flush()
            if i % 200 == 0:
                print(f"{i}/{len(rows)}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
