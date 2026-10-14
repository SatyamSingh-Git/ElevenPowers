"""Inspect saved execution associations; inspection never launches checks."""
import subprocess

from .execution_state import read, _source_witness, qualify_external
from ..inputs.collection import capture


LIMITS = [
    'Unsigned local execution records require trust in the producer and state directory.',
    'Before/after input reads are not atomic and cannot detect intervening reverted changes.',
    'Environment values are hashed, not exported; only explicitly approved selected local bytes are witnessed. Other dependencies and external services remain unobserved.',
    'A passing declared command and current inputs do not certify correctness or universal safety.',
]


def inspect(root, patch, receipts, deadline, bound, *, base=None, head=None):
    result = {'schema': 1, 'state': 'absent', 'checks': [], 'issues': [],
              'evicted': 0, 'limits': LIMITS}
    try:
        saved = read(root)
        result['evicted'] = saved['evicted']
        if not saved['attempts']:
            return result
        source, _ = _source_witness(root, patch, deadline, base=base, head=head)
        external_observation = capture(root, deadline)
        if external_observation['state'] != 'not_configured':
            final, _ = _source_witness(root, patch, deadline, base=base, head=head)
            if final != source:
                raise ValueError('source changed during external inspection')
        if read(root) != saved:
            raise ValueError('saved execution state changed during inspection')
        latest = {}
        for item in saved['attempts']:
            latest[item['command_digest']] = item
        for item in latest.values():
            why = []
            command = ''
            if 'external_inputs_scope' in item['witness']:
                from ..config import load
                command=load(root).commands.get(item['properties'][0],'')
            try:
                current=qualify_external(source,external_observation,command)
            except ValueError:
                current=source
                why.append('required external input observation is incomplete')
            keys = set(item['receipt_keys'])
            matches = [r for r in receipts if r['receipt_key'] in keys]
            external = current.get('external_inputs_fingerprint')
            external_matching = (external is not None and
                item['witness'].get('external_inputs_fingerprint') == external and
                (item.get('after') or {}).get('external_inputs_fingerprint') == external)
            if external is not None and not external_matching:
                why.append('declared external inputs changed or have no matching saved observation')
            if not bound or item['witness'] != current or item.get('after') != current:
                why.append('patch, source, configuration, policy, producer, environment or external-input association changed/unavailable')
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
                'external_inputs_fingerprint': item['witness'].get('external_inputs_fingerprint'),
                'external_inputs_association': ('not_configured' if external is None and
                                               'external_inputs_fingerprint' not in item['witness'] and not why else
                                               'bound' if external_matching and not why else 'unavailable'),
                'budgets': item.get('budgets', {})})
        result['state'] = 'available' if all(c['association'] == 'bound' for c in result['checks']) else 'incomplete'
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, subprocess.SubprocessError) as error:
        result['state'] = 'incomplete'
        result['issues'].append(type(error).__name__ + ': saved execution association unavailable')
    return result
