"""Join the follow-up-fix labels to each PR's repository and number.

Needs pyarrow, which the project does not depend on; run it from a separate
environment. Its output, prs.csv, is committed so the rest needs neither.

    python build.py <rq1_survival_frame.csv> <AIDev pull_request.parquet>
"""
import csv
import sys
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).parent


def main(frame_path, parquet_path):
    frame = {int(r["pr_id"]): r for r in csv.DictReader(open(frame_path, encoding="utf-8"))
             if r["cohort"] == "Agent"}
    table = pq.read_table(parquet_path, columns=["id", "number", "agent", "repo_url"]).to_pylist()
    found = {}
    for row in table:
        if row["id"] in frame:
            found[row["id"]] = row
    with open(HERE / "prs.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["pr_id", "repo", "number", "agent", "ver_event", "ver_time"])
        for pr_id, row in sorted(found.items()):
            repo = row["repo_url"].removeprefix("https://api.github.com/repos/")
            label = frame[pr_id]
            writer.writerow([pr_id, repo, row["number"], row["agent"], label["ver_event"], label["ver_time"]])
    print(f"agent PRs in the frame: {len(frame)}; found: {len(found)}; dropped: {len(frame) - len(found)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
