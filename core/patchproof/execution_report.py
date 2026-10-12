"""Inspect saved execution associations; inspection never launches checks."""
import subprocess

from .execution_state import read, witness


LIMITS = [
    'Unsigned local execution records require trust in the producer and state directory.',
    'Before/after input reads are not atomic and cannot detect intervening reverted changes.',
    'Environment values are hashed, not exported; installed dependency bytes and external services are unobserved.',
    'A passing declared command and current inputs do not certify correctness or universal safety.',
]


def inspect(root, patch, receipts, deadline, bound):
    result = {'schema': 1, 'state': 'absent', 'checks': [], 'issues': [],
              'evicted': 0, 'limits': LIMITS}
    try:
        saved = read(root)
        result['evicted'] = saved['evicted']
        if not saved['attempts']:
            return result
        current, _ = witness(root, patch, deadline)
        latest = {}
        for item in saved['attempts']:
            latest[item['command_digest']] = item
        for item in latest.values():
            matches = [r for r in receipts if r['receipt_key'] in item['receipt_keys']]
            why = []
            if not bound or item['witness'] != current or item.get('after') != current:
                why.append('patch, source, configuration, policy, producer or environment association changed/unavailable')
            if item['status'] not in {'passed', 'failed'}:
                why.append('execution did not retain a complete qualified result')
            if not matches or len(matches) != len(item['receipt_keys']):
                why.append('associated receipts are absent from current evidence')
            if any((r['association'] != 'bound' and not patch['empty'])
                   or r['execution'] != 'complete' or r['freshness'] != 'fresh'
                   or r['coverage_issues'] for r in matches):
                why.append('receipt input association or completed execution is unavailable')
            # Every property must still name this exact latest aggregate receipt.
            for prop in item['properties']:
                from ..parsers import DECLARED_KINDS
                all_matches = [r for r in receipts if r['declaration'] == prop
                               and r['kind'] == DECLARED_KINDS[prop].value]
                final = max(reversed(all_matches), key=lambda r: r['recorded_at']) if all_matches else None
                if not final or final['receipt_key'] not in item['receipt_keys']:
                    why.append('a later aggregate receipt superseded this execution')
            result['checks'].append({
                'command_digest': item['command_digest'], 'properties': item['properties'],
                'status': item['status'], 'association': 'unavailable' if why else 'bound',
                'association_issues': list(dict.fromkeys(why)), 'receipt_keys': item['receipt_keys'],
                'executed_at_patch_head': current['head'] if not why else 'unknown',
                'producer_fingerprint': item['witness'].get('producer_fingerprint', ''),
                'environment_fingerprint': item['witness'].get('environment_fingerprint', ''),
                'budgets': item.get('budgets', {})})
        result['state'] = 'available' if all(c['association'] == 'bound' for c in result['checks']) else 'incomplete'
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, subprocess.SubprocessError) as error:
        result['state'] = 'incomplete'
        result['issues'].append(type(error).__name__ + ': saved execution association unavailable')
    return result
