"""Gate 1 of the rule-as-mandate design, at $0. Usage: rehearse.py <new scratch dir>.

Through the real plugin hook on household_budget 7: before an Edit of budgets.py, the `described`
arm's brief carries the whole mandate sentence for the summarise rule, and the `rules` arm's brief
carries the proposer's template for it instead."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'results' / 'rule-gate'))
from eval.multistage_cases import load  # noqa: E402
from eval.rule_groups_run import certify, workspace  # noqa: E402
from rehearse import hook  # noqa: E402

HERE = Path(__file__).parent
CASE, STAGE = 'household_budget', 7
RULE = 'rule-summarise-_spent_by_category'
EDITED = 'src/budgetbook/services/budgets.py'


def brief(case, arm, folder, entries):
    work = workspace(case, STAGE, arm, folder, entries)
    hook(work, 'SessionStart', source='startup')
    hook(work, 'UserPromptSubmit', prompt=case['stages'][STAGE - 1]['request'])
    done = hook(work, 'PreToolUse', tool_name='Edit',
                tool_input={'file_path': str(work / EDITED), 'old_string': 'a', 'new_string': 'b'})
    return json.loads(done.stdout)['hookSpecificOutput'].get('additionalContext', '') if done.stdout.strip() else ''


def main():
    scratch = Path(sys.argv[1]).resolve()
    if scratch.exists():
        raise SystemExit('new scratch dir required')
    case = load(ROOT / 'eval' / 'multistage_v3' / CASE)
    accepted = json.loads((ROOT / 'results' / 'rule-gate' / 'accepted.json').read_text(encoding='utf-8'))[CASE]
    mandates = json.loads((HERE / 'descriptions.json').read_text(encoding='utf-8'))[CASE]
    entries = certify(case, scratch / 'certify', accept=accepted)
    described = [{**e, 'description': mandates[e['id']]} for e in entries]
    template = next(e['description'] for e in entries if e['id'] == RULE)
    briefs = {'rules': brief(case, 'rules', scratch / 'rules', entries),
              'described': brief(case, 'described', scratch / 'described', described)}
    checks = {
        'mandates cover exactly the certified rules': set(mandates) == {e['id'] for e in entries},
        'described brief carries the whole mandate': mandates[RULE] in briefs['described'],
        'described brief has no template text': 'keep the same rule' not in briefs['described'],
        'rules brief carries the template': template in briefs['rules'],
        'rules brief has no mandate': 'must stay consistent' not in briefs['rules'],
    }
    result = {'briefs': briefs, 'checks': checks}
    (HERE / 'rehearsal.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=1))
    print('gate 1:', 'PASS' if all(checks.values()) else 'FAIL')


if __name__ == '__main__':
    main()
