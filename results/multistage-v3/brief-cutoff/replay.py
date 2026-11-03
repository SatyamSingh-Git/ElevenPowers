"""Open problem 3 ($0): would ordering a brief's importers put the hidden dependent in the first four?

The import brief lists at most four importers, alphabetically, then "+N more".
In 5 of the 31 v3 losses the broken dependent imported an edited file but sat
behind that cutoff. Two orderings are replayed on the kept snapshots:

- `uses`: importers that name a function or class the edit touched come first.
  Borrowed: find-references, cut down to a token match.
- `tokens`: importers ranked by the rare tokens they share with the edited
  functions (the convention spike's score, restricted to importers).

Both only reorder names the brief already has, so neither adds a warning. The
risk is the other way: a reordering can push out a dependent the alphabetical
brief showed, so every v3 stage is replayed, not only the losses.
"""
import ast
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'convention-spike'))
from rank import BATCHES, ROOT, V3, changed, scored, sources, tokens  # noqa: E402
from core.atlas import source_model  # noqa: E402

SHOWN = 4


def touched_names(source, lines):
    """Top-level functions and classes, and methods, whose span holds a changed line."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and any(n.lineno <= l <= n.end_lineno for l in lines)}


def orders(before_tree, after_tree, edited, control):
    """For each edited file: its importers in the brief's order and in each candidate order.

    `control` is another stage's (before, after, edited): its token weights order the same
    importers, so an importer that comes first for any edit shows up as central, not pointed at.
    """
    model = source_model(before_tree)
    before, after = sources(before_tree), sources(after_tree)
    weight = {path: score for score, path in scored(before_tree, after_tree, edited)[0]}
    other = {path: score for score, path in scored(*control)[0]}
    out = {}
    for path in edited:
        if path not in model or path not in before:
            continue
        into = sorted(p for p, m in model.items() if path in m.imports)
        if not into:
            continue
        old, new = changed(before[path], after.get(path, ''))
        names = touched_names(before[path], old) | touched_names(after.get(path, ''), new)
        uses = {p: bool(names & set(tokens(before.get(p, '')))) for p in into}
        out[path] = {'alphabetical': into,
                     'uses': sorted(into, key=lambda p: (not uses[p], p)),
                     'tokens': sorted(into, key=lambda p: (-weight.get(p, 0), p)),
                     'control': sorted(into, key=lambda p: (-other.get(p, 0), p)),
                     'names': sorted(names)}
    return out


def main():
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    losses = {(l['slot'], l['stage']) for l in
              json.loads((V3 / 'diagnosis-elevenpowers-losses.json').read_text(encoding='utf-8'))}
    rows = []
    for row in analysis['rows']:
        case = json.loads((ROOT / 'eval' / 'multistage_v3' / row['case'] / 'case.json').read_text(encoding='utf-8'))
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot'] / 'snapshots'
        for n, stage in enumerate(case['stages'], 1):
            quiet = stage.get('quiet') or []
            quiet = quiet if isinstance(quiet, list) else [quiet]
            if not quiet or not (folder / str(n)).exists():
                continue
            before, after = folder / str(n - 1), folder / str(n)
            old, new = sources(before), sources(after)
            edited = [p for p in new if old.get(p) != new[p]]
            dependents = sorted({q['file'] for q in quiet} - set(edited))
            if not dependents:
                continue
            m = n + 1 if (folder / str(n + 1)).exists() else n - 1
            o_old, o_new = sources(folder / str(m - 1)), sources(folder / str(m))
            control = (folder / str(m - 1), folder / str(m), [p for p in o_new if o_old.get(p) != o_new[p]])
            briefs = orders(before, after, edited, control)
            for dependent in dependents:
                reachable = [b for b in briefs.values() if dependent in b['alphabetical']]
                if not reachable:
                    continue
                rows.append({'slot': row['slot'], 'stage': n, 'dependent': dependent,
                             'loss': (row['slot'], n) in losses, 'importers': max(len(b['alphabetical']) for b in reachable),
                             **{k: min(b[k].index(dependent) + 1 for b in reachable)
                                for k in ('alphabetical', 'uses', 'tokens', 'control')}})
    HERE.joinpath('replay.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    print(len(rows), 'unedited dependents that import an edited file;',
          sum(r['loss'] for r in rows), 'in ElevenPowers losses')
    for subset, label in ((rows, 'all'), ([r for r in rows if r['loss']], 'losses')):
        print(label, {k: f"{sum(r[k] <= SHOWN for r in subset)} of {len(subset)} shown"
                      for k in ('alphabetical', 'uses', 'tokens', 'control')})
    for k in ('uses', 'tokens', 'control'):
        print(k, 'newly shown', sum(r[k] <= SHOWN < r['alphabetical'] for r in rows),
              '| pushed out', sum(r['alphabetical'] <= SHOWN < r[k] for r in rows))


if __name__ == '__main__':
    main()
