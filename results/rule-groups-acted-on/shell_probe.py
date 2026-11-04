"""Does the rule note emitted after a Bash write reach the model on the real host? Both arms, one turn each."""
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, r'E:\ElevenPowers')
from core.process import run  # noqa: E402
from eval.heldout_run import _tool_calls  # noqa: E402
from eval.live import _sandboxed  # noqa: E402
from eval.multistage_cases import load  # noqa: E402
from eval.rule_groups_run import certify, command, workspace  # noqa: E402

MODEL = 'claude-sonnet-5-5'
TOUCH = r'''from pathlib import Path
p = Path("src/payroll/rules/overtime.py")
p.write_text(p.read_text() + "\n# probe\n")
'''
PROMPT = ('Run `python touch_overtime.py` exactly once with the Bash tool, and use no other tool. '
          'Then reply with the exact text of any message you received after that command that begins with '
          '"Declared rule", or reply NONE if there was no such message.')

scratch = Path(sys.argv[1])
case = load(Path(r'E:\ElevenPowers\eval\multistage_v3\payroll_lite'))
entries = certify(case, scratch / 'certify')
rule_ids = [e['id'] for e in entries if 'src/payroll/rules/overtime.py' in e['inputs']]
print('rules naming overtime.py:', rule_ids)
total = 0.0
for arm in ('rules', 'control'):
    folder = scratch / arm
    work = workspace(case, 2, arm, folder, entries)
    (work / 'touch_overtime.py').write_text(TOUCH, encoding='utf-8')
    done = run(command('claude', work, PROMPT, str(uuid.uuid4()), 1, MODEL), cwd=work, timeout=300, shell=False,
               env={**_sandboxed(folder), 'ANTHROPIC_DEFAULT_HAIKU_MODEL': MODEL})
    (folder / 'native.jsonl').write_text(done.stdout, encoding='utf-8')
    calls, result = _tool_calls(done.stdout)
    ledger = work / '.elevenpowers' / 'ledger.json'
    briefed = json.loads(ledger.read_text(encoding='utf-8')).get('briefed', []) if ledger.exists() else []
    reply = (result or {}).get('result', '')
    total += float((result or {}).get('total_cost_usd') or 0)
    print(json.dumps({'arm': arm, 'exit': done.returncode, 'tools': [c.get('name') for c in calls],
                      'briefed': briefed, 'quotes_rule_id': any(i in reply for i in rule_ids),
                      'reply': reply[:600], 'cost': (result or {}).get('total_cost_usd')}, indent=1))
print('total cost', round(total, 4))
