"""The reviewed rerun's report: the acted-on report on this batch, then the design's secondaries, the
rule notes each run received and each stage beside the perfect-certification run.

Usage: analyse.py <batch>. Writes analysis-<batch name>.json next to this file and prints a summary."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'results' / 'rule-groups-acted-on'))
from analyse import build, show  # noqa: E402
from eval.multistage_cases import load  # noqa: E402

PERFECT = ROOT / 'results' / 'rule-groups-acted-on' / 'analysis-rule-groups-acted-on-full-2026-11-04.json'


def notes(rules, briefed):
    """The rule ids `rules_naming` sends for the briefed files: up to three per file, in declaration order."""
    sent = set()
    for path in briefed:
        sent |= {r['id'] for r in [r for r in rules if path in r['inputs'] and len(r['inputs']) > 1][:3]}
    return sent


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    protocol = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))
    report = build(batch)
    for row in report['rows']:
        if row['arm'] != 'rules':
            continue
        rules = protocol['rules'][row['case']]
        dependent = load(ROOT / 'eval' / 'multistage_v3' / row['case'])['stages'][row['stage'] - 1]['quiet'][0]['file']
        sent = notes(rules, row.get('declared_files_briefed') or [])
        row.update(rule_notes=len(sent),
                   dependent_note=any(r['id'] in sent and dependent in r['inputs'] for r in rules))
    rows = [r for r in report['rows'] if r['arm'] == 'rules' and r['comparable']]
    report['delivery'] = {'rule_notes_per_run': sorted(r['rule_notes'] for r in rows),
                          'runs_with_the_dependent_s_note': sum(r['dependent_note'] for r in rows),
                          'lost_with_the_dependent_s_note': sum(r['dependent_lost'] for r in rows if r['dependent_note']),
                          'lost_without_it': sum(r['dependent_lost'] for r in rows if not r['dependent_note']),
                          'runs_without_it': sum(not r['dependent_note'] for r in rows)}
    perfect = json.loads(PERFECT.read_text(encoding='utf-8'))['rows']
    report['beside_perfect'] = []
    for name, stage in protocol['stages']:
        table = {}
        for label, source in (('reviewed', report['rows']), ('perfect', perfect)):
            runs = {arm: [r for r in source if (r['case'], r['stage'], r['arm']) == (name, stage, arm) and r['comparable']]
                    for arm in ('rules', 'control')}
            table[label] = [sum(r['dependent_lost'] for r in runs['rules']), len(runs['rules']),
                            sum(r['dependent_lost'] for r in runs['control']), len(runs['control'])]
        report['beside_perfect'].append({'stage': f'{name} {stage}', **table})
    Path(__file__).with_name(f'analysis-{batch.name}.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    show(batch, report)
    print('delivery', report['delivery'])
    print('beside the perfect run (rules lost, rules n, control lost, control n):')
    for item in report['beside_perfect']:
        print(f"  {item['stage']}: reviewed {item['reviewed']}  perfect {item['perfect']}")


if __name__ == '__main__':
    main()
