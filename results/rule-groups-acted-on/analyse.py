"""The full run's report: the pre-registered primary outcome and secondaries, then what is exploratory.

Usage: analyse.py <batch>. Writes analysis-<batch name>.json next to this file and prints a summary."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load  # noqa: E402
from eval.rule_groups_run import ARMS, collect  # noqa: E402

EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}


def tool_names(folder):
    names = []
    path = folder / 'native.jsonl'
    for line in (path.read_text(encoding='utf-8').splitlines() if path.exists() else []):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get('type') == 'assistant':
            names += [item.get('name') for item in event.get('message', {}).get('content', [])
                      if isinstance(item, dict) and item.get('type') == 'tool_use']
    return names


def build(batch):
    value = collect(batch)
    cases = {}
    for row in value['rows']:
        case = cases.setdefault(row['case'], load(ROOT / 'eval' / 'multistage_v3' / row['case']))
        stage = case['stages'][row['stage'] - 1]
        fails = {name for quiet in stage.get('quiet') or [] for name in quiet.get('fails', [])}
        own = [g['id'] for g in case['groups'] if g['since'] == row['stage']]
        record = json.loads((batch / row['slot'] / 'result.json').read_text(encoding='utf-8')) \
            if (batch / row['slot'] / 'result.json').exists() else {}
        groups = record.get('outcome', {}).get('groups', {})
        names = tool_names(batch / row['slot'])
        row.update(other_lost=sorted(set(row.get('lost') or []) - fails),
                   request_done=bool(own) and all(groups.get(g) == 'passed' for g in own) if groups else None,
                   edit_tool_calls=sum(n in EDIT_TOOLS for n in names), bash_calls=names.count('Bash'))

    def arm_rows(arm):
        return [r for r in value['rows'] if r['arm'] == arm and r['comparable']]

    report = {'states': {}, 'tables': value['tables'], 'p_one_sided': value['p_one_sided'], 'arms': {}}
    for row in value['rows']:
        report['states'][row['state']] = report['states'].get(row['state'], 0) + 1
    for arm in ARMS:
        rows = arm_rows(arm)
        report['arms'][arm] = {
            'comparable': len(rows),
            'dependent_lost': sum(r['dependent_lost'] for r in rows),
            'other_groups_lost_runs': sum(bool(r['other_lost']) for r in rows),
            'cost': round(sum(r.get('cost') or 0 for r in value['rows'] if r['arm'] == arm), 2),
            'mean_seconds': round(sum(r['seconds'] for r in rows) / len(rows), 1) if rows else None,
            'briefed_runs': sum(bool(r.get('declared_files_briefed')) for r in rows),
            'exploratory_request_done': sum(bool(r['request_done']) for r in rows),
            'exploratory_runs_with_no_edit_tool': sum(r['edit_tool_calls'] == 0 for r in rows)}
    report['rows'] = value['rows']
    return report


def show(batch, report):
    print('states', report['states'])
    print('per stage (rules lost, rules n, control lost, control n):')
    for (name, stage), table in zip(json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))['stages'],
                                    report['tables']):
        print(f'  {name} {stage}: {table}')
    print('pre-registered one-sided exact stratified p:', report['p_one_sided'])
    for arm, summary in report['arms'].items():
        print(arm, summary)


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    report = build(batch)
    Path(__file__).with_name(f'analysis-{batch.name}.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    show(batch, report)


if __name__ == '__main__':
    main()
