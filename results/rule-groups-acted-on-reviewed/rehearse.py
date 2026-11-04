"""Gate 1 of the reviewed acted-on design, at $0: the reviewer's kept pairs load as declarations in
the rules arm only; on the four stages whose pair it kept, the reference edit and the same change
written by a shell command bring a note naming the dependent; on parcelpost 5, whose pair it
dropped, neither does. Usage: rehearse.py <new scratch dir>."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'results' / 'rule-groups-acted-on'))
from core.milestones.definition import load as declarations  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import ARMS, certify, workspace  # noqa: E402
from rehearse import PRIMARY, hook  # noqa: E402

DROPPED = ('parcelpost', 5)


def names(text, dependent):
    # Only rule notes: the import-neighbourhood line can name the dependent too, in both arms
    # (parcelpost's manifest.py is imported by billing.py).
    return any('Declared rule' in line and dependent in line for line in text.splitlines())


def main():
    scratch = Path(sys.argv[1]).resolve()
    accepted = json.loads(Path(__file__).with_name('accepted.json').read_text(encoding='utf-8'))
    rows = []
    for name, n in PRIMARY:
        case = load(ROOT / 'eval' / 'multistage_v3' / name)
        folder = scratch / f'{name}-{n}'
        entries = certify(case, folder / 'certify', accept=accepted[name])
        dependent = case['stages'][n - 1]['quiet'][0]['file']
        quiet = tree(case, n, folder / 'quiet', 'quiet')
        before = tree(case, n - 1, folder / 'before')
        changed = [p.relative_to(quiet).as_posix() for p in quiet.rglob('*.py')
                   if not (before / p.relative_to(quiet)).exists()
                   or (before / p.relative_to(quiet)).read_bytes() != p.read_bytes()]
        briefs, shell = {}, {}
        for arm in ARMS:
            work = workspace(case, n, arm, folder / arm, entries)
            hook(work, 'SessionStart', source='startup')
            hook(work, 'UserPromptSubmit', prompt=case['stages'][n - 1]['request'])
            briefs[arm] = {path: hook(work, 'PreToolUse', tool_name='Edit',
                                      tool_input={'file_path': str(work / path), 'old_string': 'a', 'new_string': 'b'}
                                      ).get('additionalContext', '') for path in changed}
            work = workspace(case, n, arm, folder / f'{arm}-shell', entries)
            hook(work, 'SessionStart', source='startup')
            hook(work, 'UserPromptSubmit', prompt=case['stages'][n - 1]['request'])
            for path in changed:
                (work / path).parent.mkdir(parents=True, exist_ok=True)
                (work / path).write_bytes((quiet / path).read_bytes())
            shell[arm] = hook(work, 'PostToolUse', tool_name='Bash', tool_input={'command': 'python apply_change.py'},
                              tool_response={'stdout': '', 'stderr': '', 'interrupted': False, 'isImage': False,
                                             'noOutputExpected': False}).get('additionalContext', '')
        loaded = declarations(folder / 'rules' / 'work')
        covered = (name, n) != DROPPED
        row = {'stage': f'{name} {n}', 'dependent': dependent, 'declared rules': len(entries),
               'pair kept': any(dependent in e['inputs'] and set(changed) & set(e['inputs']) for e in entries),
               'declarations load': not loaded['issues'] and len(loaded['milestones']) == len(entries),
               'control has none': not (folder / 'control' / 'work' / 'elevenpowers.milestones.json').exists(),
               'edit brief names dependent': [path for path, text in briefs['rules'].items() if names(text, dependent)],
               'shell note names dependent': names(shell['rules'], dependent),
               'rule notes in the shell note': shell['rules'].count('Declared rule'),
               'control briefs carry no rule': not any('Declared rule' in t for t in briefs['control'].values()),
               'control shell silent': 'Declared rule' not in shell['control'],
               'neighbourhood names dependent, either arm':
                   any(dependent in t and not names(t, dependent) for t in briefs['control'].values())}
        named = bool(row['edit brief names dependent']) or row['shell note names dependent']
        row['passes'] = (row['declarations load'] and row['control has none'] and row['control shell silent']
                         and row['control briefs carry no rule']
                         and row['pair kept'] == covered and named == covered
                         and (not covered or (bool(row['edit brief names dependent']) and row['shell note names dependent'])))
        rows.append(row)
        print(json.dumps(row), flush=True)
    Path(__file__).with_name('rehearsal.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    print('gate 1:', 'PASS' if all(r['passes'] for r in rows) else 'FAIL', f"({sum(r['passes'] for r in rows)} of {len(rows)})")


if __name__ == '__main__':
    main()
