"""Does a Cursor rule reach the model in a real Claude Code session? One turn per arm, a few cents.

`rule`: the project carries `.cursor/rules/overtime.mdc` scoped to the file the agent edits, with a
marker phrase no other source contains. `control`: the same project without it. The agent makes one
Edit and quotes any project rule it received. Usage: probe.py <new scratch dir>"""
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.process import run  # noqa: E402
from eval.heldout_run import _tool_calls  # noqa: E402
from eval.live import _sandboxed  # noqa: E402
from eval.multistage_cases import load  # noqa: E402
from eval.rule_groups_run import command, workspace  # noqa: E402

MODEL = 'claude-sonnet-5-5'
TARGET = 'src/payroll/rules/overtime.py'
MARKER = 'PROBE-4417'
RULE = (f'---\nglobs: {TARGET}\nalwaysApply: false\n---\n'
        f'{MARKER}: overtime multipliers are read from settings, never written as literals.\n')
PROMPT = (f'Use the Edit tool exactly once to append the line `# probe` to the end of {TARGET}. Use no other '
          'tool except Read. Then reply with the exact text of any message you received that begins with '
          '"Project rule", or reply NONE if there was no such message.')


def main():
    scratch = Path(sys.argv[1]).resolve()
    if scratch.exists():
        raise SystemExit('new scratch dir required')
    case = load(ROOT / 'eval' / 'multistage_v3' / 'payroll_lite')
    rows, total = [], 0.0
    for arm in ('rule', 'control'):
        folder = scratch / arm
        work = workspace(case, 2, 'control', folder, [])
        if arm == 'rule':
            (work / '.cursor' / 'rules').mkdir(parents=True)
            (work / '.cursor' / 'rules' / 'overtime.mdc').write_text(RULE, encoding='utf-8')
        done = run(command('claude', work, PROMPT, str(uuid.uuid4()), 1, MODEL), cwd=work, timeout=300,
                   shell=False, env={**_sandboxed(folder), 'ANTHROPIC_DEFAULT_HAIKU_MODEL': MODEL})
        (folder / 'native.jsonl').write_text(done.stdout, encoding='utf-8')
        calls, result = _tool_calls(done.stdout)
        reply = (result or {}).get('result', '')
        total += float((result or {}).get('total_cost_usd') or 0)
        rows.append({'arm': arm, 'exit': done.returncode, 'tools': [c.get('name') for c in calls],
                     'quotes_marker': MARKER in reply, 'reply': reply[:600],
                     'read_the_rule_file': any('.cursor' in json.dumps(c.get('input', {})) for c in calls),
                     'cost': (result or {}).get('total_cost_usd')})
    checks = {'rule arm quotes the marker it could only get from the hook':
                  rows[0]['quotes_marker'] and not rows[0]['read_the_rule_file'],
              'control arm received no project rule': not rows[1]['quotes_marker'] and 'NONE' in rows[1]['reply']}
    result = {'rows': rows, 'checks': checks, 'total_cost': round(total, 4)}
    Path(__file__).with_name('probe.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=1))
    print('probe:', 'PASS' if all(checks.values()) else 'FAIL')


if __name__ == '__main__':
    main()
