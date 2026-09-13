"""Split the pinned corpus into chunks, recorded so later chunks match.

    python -m eval.chunks

A paired sweep over forty-nine tasks costs more than one sitting should, and a
subscription is easier to watch in pieces. The split is not only budgeting.

Each chunk carries both arms and every replicate of the tasks in it, so no task
is ever measured with its arms in different sittings: when an agent broke the
machine partway through pass B, every affected run was in the same arm because
only one arm was in flight, and drift landing on one side of a comparison is
indistinguishable from an effect.

The assignment is stratified by band and seeded, so a chunk boundary cannot
correlate with difficulty and the same four chunks come out every time it is
computed. It is written to disk because a later chunk has to agree with an
earlier one, and "I shuffled it the same way" is not a record.
"""
import json, pathlib, random, sys

CORPUS = pathlib.Path("E:/ep-corpus/paired.json")
OUT = pathlib.Path("E:/ep-corpus/chunks.json")
SEED = 11

def split() -> None:
    rows = json.loads(CORPUS.read_text(encoding="utf-8"))
    def band(n): return "one-liner" if n <= 3 else "small" if n <= 20 else "substantial"

    # Stratified: each chunk gets its share of both bands, so a chunk boundary
    # cannot correlate with difficulty. Shuffled inside each band, seeded, so the
    # assignment is the same every time it is computed.
    shuffler = random.Random(SEED)
    chunks = [[] for _ in range(4)]
    for name in ("substantial", "one-liner"):
        pool = sorted(r["name"] for r in rows if band(r["gold_lines"]) == name)
        shuffler.shuffle(pool)
        for i, task in enumerate(pool):
            chunks[i % 4].append(task)

    OUT.write_text(json.dumps({f"chunk{i+1}": sorted(c) for i, c in enumerate(chunks)},
                              indent=1), encoding="utf-8")
    for i, c in enumerate(chunks):
        subs = sum(1 for t in c if band(next(r for r in rows if r["name"] == t)["gold_lines"]) == "substantial")
        print(f"chunk{i+1}: {len(c):>2} tasks ({subs} substantial, {len(c)-subs} one-liner)")
    print(f"\nwrote {OUT}")


def carve(which: str, out: pathlib.Path) -> int:
    """Write one chunk's tasks as a corpus of their own, for a single sitting."""
    assignment = json.loads(OUT.read_text(encoding="utf-8"))
    if which not in assignment:
        print(f"no {which}; one of {', '.join(assignment)}")
        return 1
    wanted = set(assignment[which])
    rows = [r for r in json.loads(CORPUS.read_text(encoding="utf-8"))
            if r["name"] in wanted]
    missing = wanted - {r["name"] for r in rows}
    if missing:
        # The chunk names a task the corpus no longer has. Running the rest
        # would quietly measure a smaller benchmark under the same name.
        print(f"{which} names {len(missing)} task(s) the corpus does not hold: "
              f"{sorted(missing)[:3]}")
        return 1
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{which}: {len(rows)} task(s) -> {out}")
    return 0


if __name__ == "__main__":
    if "--carve" in sys.argv:
        where = sys.argv.index("--carve") + 1
        target = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "chunk.json"
        sys.exit(carve(sys.argv[where], pathlib.Path(target)))
    split()
