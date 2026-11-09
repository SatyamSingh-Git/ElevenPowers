"""Gate 1 of the rule-gate design, at $0. Usage: rehearse.py <new scratch dir>.

1. Writes accepted.json: the blind reviewer's kept pairs for every case.
2. Picks the harm stages: every v3 stage but household_budget 7 whose reference
   solution changes a reviewed rule in some of its files and not the others, so
   the gate sends a correct agent back. At most 8, most findings first, then by name.
3. Through the real plugin hook on household_budget 7: the left-behind variant
   is sent back naming month_end.py in `gate` and not in `note`; the reference
   is sent back in `gate` only for the rule whose other file a correct run leaves.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import GATED, certify, workspace  # noqa: E402

HERE = Path(__file__).parent
HOOK = ROOT / 'plugin' / 'bin' / 'ep_hook.py'
PRIMARY = ('household_budget', 7)
HARM_STAGES = 8
TOLD = 'Declared rules left behind:'


def hook(work, event, **extra):
    payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
    return subprocess.run([sys.executable, str(HOOK), event], input=json.dumps(payload), text=True, cwd=work,
                          capture_output=True, env={**os.environ, 'CLAUDE_PROJECT_DIR': str(work)})


def changed(before, after):
    return sorted(p.relative_to(after).as_posix() for p in after.rglob('*.py')
                  if not (before / p.relative_to(after)).exists()
                  or (before / p.relative_to(after)).read_bytes() != p.read_bytes())


def left_behind(entries, paths):
    return [e['id'] for e in entries
            if set(e['inputs']) & set(paths) and set(e['inputs']) - set(paths)]


def stop(case, n, arm, folder, entries, variant):
    work = workspace(case, n, arm, folder, entries)
    hook(work, 'SessionStart', source='startup')
    hook(work, 'UserPromptSubmit', prompt=case['stages'][n - 1]['request'])
    before = tree(case, n - 1, folder.parent / f'{folder.name}-before')
    for path in changed(before, variant):
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_bytes((variant / path).read_bytes())
    hook(work, 'PostToolUse', tool_name='Bash', tool_input={'command': 'python apply_change.py'},
         tool_response={'stdout': '', 'stderr': '', 'interrupted': False, 'isImage': False,
                        'noOutputExpected': False})
    done = hook(work, 'Stop', stop_hook_active=False, last_assistant_message='Done; the tests pass.')
    told = done.stderr.split(TOLD, 1)[1] if TOLD in done.stderr else ''
    return {'exit': done.returncode, 'rules told': [line.strip() for line in told.splitlines()
                                                    if line.strip().startswith('declared rule')]}


def main():
    scratch = Path(sys.argv[1]).resolve()
    if scratch.exists():
        raise SystemExit('new scratch dir required')
    reviewed = json.loads((ROOT / 'results' / 'rule-groups-reviewed' / 'reviewed.json').read_text(encoding='utf-8'))
    accepted = {row['case']: row['kept'] for row in reviewed}
    (HERE / 'accepted.json').write_text(json.dumps(accepted, indent=1, sort_keys=True) + '\n', encoding='utf-8')

    findings, rules = [], {}
    for name in sorted(accepted):
        case = load(ROOT / 'eval' / 'multistage_v3' / name)
        rules[name] = certify(case, scratch / name / 'certify', accept=accepted[name])
        for n in range(1, len(case['stages']) + 1):
            before = tree(case, n - 1, scratch / name / f'{n}-before')
            after = tree(case, n, scratch / name / f'{n}-after')
            said = left_behind(rules[name], changed(before, after))
            if said and (name, n) != PRIMARY:
                findings.append({'case': name, 'stage': n, 'rules left behind by the reference': said})
    findings.sort(key=lambda f: (-len(f['rules left behind by the reference']), f['case'], f['stage']))
    harm = findings[:HARM_STAGES]

    name, n = PRIMARY
    case = load(ROOT / 'eval' / 'multistage_v3' / name)
    folder = scratch / 'primary'
    dependent = case['stages'][n - 1]['quiet'][0]['file']
    variants = {'left behind': tree(case, n, folder / 'quiet', 'quiet'), 'reference': tree(case, n, folder / 'ref')}
    primary = {f'{arm}, {label}': stop(case, n, arm, folder / f'{arm}-{label.replace(" ", "-")}', rules[name], variant)
               for arm in GATED for label, variant in variants.items()}
    names = lambda key: any(dependent in said for said in primary[key]['rules told'])  # noqa: E731
    checks = {
        'gate sends the left-behind variant back naming the dependent':
            primary['gate, left behind']['exit'] == 2 and names('gate, left behind'),
        'note never sends a rule back': not primary['note, left behind']['rules told']
                                        and not primary['note, reference']['rules told'],
        'gate sends the reference back, but not for the dependent':
            primary['gate, reference']['exit'] == 2 and bool(primary['gate, reference']['rules told'])
            and not names('gate, reference'),
        'harm stages found': bool(harm),
    }
    result = {'dependent': dependent, 'primary': primary, 'checks': checks,
              'harm stages': harm, 'all reference findings': findings}
    (HERE / 'rehearsal.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=1))
    print('gate 1:', 'PASS' if all(checks.values()) else 'FAIL')


if __name__ == '__main__':
    main()
