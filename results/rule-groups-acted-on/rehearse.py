"""Gate 1 of the acted-on design, at $0: on each primary stage, the certification holds the
stage's pair, the declarations load, only the rules arm carries them, the reference edit
replayed through the real hooks brings a brief naming the dependent, and the grader scores
the reference as kept and the quiet variant as lost. Usage: rehearse.py <new scratch dir>."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.definition import load as declarations  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import certify, outcome, workspace  # noqa: E402

PRIMARY = [('household_budget', 7), ('recipe_box', 4), ('library_loans', 1), ('payroll_lite', 2), ('parcelpost', 5)]
HOOK = ROOT / 'plugin' / 'bin' / 'ep_hook.py'


def hook(work, event, **extra):
    payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
    done = subprocess.run([sys.executable, str(HOOK), event], input=json.dumps(payload), text=True, cwd=work,
                          capture_output=True, env={**os.environ, 'CLAUDE_PROJECT_DIR': str(work)})
    return json.loads(done.stdout).get('hookSpecificOutput', {}) if done.stdout.strip() else {}


def main():
    scratch = Path(sys.argv[1]).resolve()
    rows = []
    for name, n in PRIMARY:
        case = load(ROOT / 'eval' / 'multistage_v3' / name)
        folder = scratch / f'{name}-{n}'
        entries = certify(case, folder / 'certify')
        dependent = case['stages'][n - 1]['quiet'][0]['file']
        control = workspace(case, n, 'control', folder / 'control', entries)
        rules = workspace(case, n, 'rules', folder / 'rules', entries)
        reference = tree(case, n, folder / 'reference')
        quiet = tree(case, n, folder / 'quiet', 'quiet')
        changed = [p.relative_to(quiet).as_posix() for p in quiet.rglob('*.py')
                   if (rules / p.relative_to(quiet)).exists() is False
                   or (rules / p.relative_to(quiet)).read_bytes() != p.read_bytes()]
        hook(rules, 'SessionStart', source='startup')
        hook(rules, 'UserPromptSubmit', prompt=case['stages'][n - 1]['request'])
        named = [path for path in changed if dependent in hook(
            rules, 'PreToolUse', tool_name='Edit',
            tool_input={'file_path': str(rules / path), 'old_string': 'a', 'new_string': 'b'}).get('additionalContext', '')]
        row = {'stage': f'{name} {n}', 'dependent': dependent, 'declared rules': len(entries),
               'pair certified': any(dependent in e['inputs'] for e in entries),
               'declarations load': not declarations(rules)['issues'] and len(declarations(rules)['milestones']) == len(entries),
               'control has none': not (control / 'elevenpowers.milestones.json').exists(),
               'brief names dependent before': named,
               'reference kept': not outcome(case, n, control, reference)['dependent_lost'],
               'quiet graded lost': outcome(case, n, control, quiet)['dependent_lost']}
        row['passes'] = all([row['pair certified'], row['declarations load'], row['control has none'],
                             bool(named), row['reference kept'], row['quiet graded lost']])
        rows.append(row)
        print(json.dumps(row))
    (Path(__file__).with_name('rehearsal.json')).write_text(json.dumps(rows, indent=1), encoding='utf-8')
    print('gate 1:', 'PASS' if all(r['passes'] for r in rows) else 'FAIL', f"({sum(r['passes'] for r in rows)} of {len(rows)})")


if __name__ == '__main__':
    main()
