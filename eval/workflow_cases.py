"""Frozen metadata for two authored, cross-language four-stage systems."""
from copy import deepcopy
from . import workflow_queue as queue, workflow_orders as orders


NAMES=('workflow-queue-py','workflow-orders-js')


def case(name):
    if name not in NAMES: raise ValueError('unknown four-stage case')
    python=name==NAMES[0]; asset=queue if python else orders
    service='service.py' if python else 'service.cjs'
    utility='formatting.py' if python else 'formatting.cjs'
    files={service:asset.BASE, utility:'def render(value):\n    return str(value)\n' if python else
           'exports.render=value=>String(value);\n', 'CONTRACT.md':'# Public staged contracts\n\n'+
           '\n\n'.join(f'{i}. {request}' for i,request in enumerate(asset.REQUESTS,1))}
    files.update({'tests/test_core.py':asset.PUBLIC,'tests/test_formatting.py':
        'import unittest\nfrom formatting import render\nclass Formatting(unittest.TestCase):\n    def test_render(self):\n        self.assertEqual(render(42),"42")\n'} if python else
        {'test/core.test.cjs':asset.PUBLIC,'test/formatting.test.cjs':
         "const test=require('node:test'),assert=require('node:assert/strict');\nconst {render}=require('../formatting.cjs');\ntest('formatting',()=>assert.equal(render(42),'42'));\n"})
    command='python -m unittest discover -s tests -v' if python else 'node --test --test-reporter=tap'
    replacements=[('now < row["until"]','now <= row["until"]'),
                  ('result.serial = value["serial"]','result.serial = 0'),
                  ('self.__dict__.update(clone.__dict__)\n        return result','return result'),
                  ('if identity in clone.seen:','if False:')] if python else [
                  ('now>=r.until','now>r.until'),
                  ("BigInt(this.prices[r.sku]||'0')*BigInt(qty)","BigInt(Number(this.prices[r.sku]||'0')*qty)"),
                  ('result.rows=v.rows','result.rows={}'),
                  ('Object.assign(this,clone);','this.stock=clone.stock;this.prices=clone.prices;this.rows=clone.rows;')]
    faults=[]
    for before,after in replacements:
        if before not in asset.REFERENCE: raise ValueError('fault no longer changes reference')
        faults.append(asset.REFERENCE.replace(before,after))
    return deepcopy({'id':name,'language':'python' if python else 'javascript','files':files,
        'production':[service,utility],'public_command':command,
        'new_test_paths':['tests/test_agent_*.py'] if python else ['test/agent-*.test.cjs'],
        'milestones':[{'id':'established-core','description':'Retain established core behavior.',
                       'inputs':[service], 'checks':[{'kind':'test_suite','command':command}]},
                      {'id':'formatting','description':'Retain independent formatting.',
                       'inputs':[utility], 'checks':[{'kind':'test_suite','command':command}]}],
        'requests':asset.REQUESTS,'gold':[asset.REFERENCE]*4,'fault':faults,
        'fault_groups':['lease_expiry','restart_fencing','batch_atomicity','replay_identity'] if python else
                       ['hold_expiry','exact_refunds','restart_identity','batch_replay']})
