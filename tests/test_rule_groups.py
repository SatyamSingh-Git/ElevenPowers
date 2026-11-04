"""Rule groups: proposing files that carry the same rule, for a person to certify.

Measured before it was built: results/multistage-v3/discover/README.md.
"""
import json
import subprocess

TAX = '''from decimal import Decimal, ROUND_HALF_UP
from .rates import LODGING_RATE


def lodging_tax(cents):
    return int((Decimal(cents) * LODGING_RATE).quantize(Decimal(1), rounding=ROUND_HALF_UP))
'''
QUOTE = '''from decimal import Decimal, ROUND_HALF_UP
from ..rates import LODGING_RATE


def quote_tax(nights):
    return sum(int((Decimal(n) * LODGING_RATE).quantize(Decimal(1), rounding=ROUND_HALF_UP)) for n in nights)
'''
NAMES = '''def greeting(name):
    return "Hello, " + name.title()
'''
FILES = '''import json


def save(path, value):
    with open(path, "w") as stream:
        json.dump(value, stream)
'''
OTHER_FILES = '''import json


def load(path):
    with open(path) as stream:
        return json.load(stream)
'''


def project(root, extra=None):
    files = {'app/money.py': TAX, 'app/services/pricing.py': QUOTE, 'app/names.py': NAMES,
             'app/store.py': FILES, 'app/archive.py': OTHER_FILES, 'app/rates.py': 'LODGING_RATE = 0.1175\n',
             **(extra or {})}
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
    return root


def test_a_rule_kept_in_two_files_is_proposed_first_with_its_reason(tmp_path):
    from core.milestones.propose import propose
    value = propose(project(tmp_path))
    first = value['proposals'][0]
    assert first['files'] == ['app/money.py', 'app/services/pricing.py']
    assert first['functions'] == ['lodging_tax', 'quote_tax']
    # The five rarest; LODGING_RATE is also defined in rates.py, so it is less rare.
    assert {'ROUND_HALF_UP', 'quantize'} <= set(first['shared'])


def test_files_that_share_only_ordinary_words_rank_below_the_rule(tmp_path):
    from core.milestones.propose import propose
    ranked = [p['files'] for p in propose(project(tmp_path))['proposals']]
    assert ranked.index(['app/money.py', 'app/services/pricing.py']) < ranked.index(['app/archive.py', 'app/store.py'])
    assert ['app/names.py', 'app/store.py'] not in ranked


def test_test_files_and_same_file_pairs_are_never_proposed(tmp_path):
    from core.milestones.propose import propose
    copy = {'tests/test_tax.py': TAX.replace('from .rates', 'from app.rates'),
            'app/money_twice.py': TAX + '\n\n' + TAX.replace('lodging_tax', 'lodging_tax_again')}
    for proposal in propose(project(tmp_path, copy))['proposals']:
        assert not any(f.startswith('tests/') for f in proposal['files'])
        assert proposal['files'][0] != proposal['files'][1]


def test_a_pair_already_declared_together_is_not_proposed_again(tmp_path):
    from core.milestones.propose import propose
    root = project(tmp_path)
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [
        {'id': 'lodging-tax', 'description': 'Lodging tax rounds half-up to the cent.',
         'inputs': ['app/money.py', 'app/services/pricing.py'],
         'checks': [{'kind': 'test_suite', 'command': 'python -m pytest -q'}]}]}), encoding='utf-8')
    files = [p['files'] for p in propose(root)['proposals']]
    assert ['app/money.py', 'app/services/pricing.py'] not in files


def test_a_proposal_carries_an_entry_to_certify_with_the_declared_tests(tmp_path):
    from core.config import Config, save
    from core.milestones.propose import propose
    root = project(tmp_path)
    save(root, Config(commands={'tests': 'python -m pytest -q'}))
    entry = propose(root)['proposals'][0]['entry']
    assert entry['inputs'] == ['app/money.py', 'app/services/pricing.py']
    assert entry['checks'] == [{'kind': 'test_suite', 'command': 'python -m pytest -q'}]
    assert entry['description'].startswith('TODO')


def test_without_a_declared_test_command_the_entry_says_a_check_is_needed(tmp_path):
    from core.config import Config, save
    from core.milestones.propose import propose
    root = project(tmp_path)
    save(root, Config(commands={}, auto_detect=False))
    value = propose(root)
    assert value['proposals'][0]['entry']['checks'] == []
    assert any('check' in issue for issue in value['coverage']['issues'])


def test_sources_it_cannot_read_are_counted_not_skipped_silently(tmp_path):
    from core.milestones.propose import propose
    coverage = propose(project(tmp_path, {'web/tax.js': 'export const tax = (c) => Math.round(c * 0.1175);\n'}))['coverage']
    assert coverage['not_examined'] == 1
    assert any('1 non-Python source files were not examined' == issue for issue in coverage['issues'])


def _words(prefix, count):
    return ', '.join(f'{prefix}{i}' for i in range(count))


def test_two_large_functions_do_not_outrank_a_small_copy_by_size(tmp_path):
    # The large pair shares ten rare words, more than the tax pair; each also has sixty of its own.
    from core.milestones.propose import propose
    large = 'def {name}():\n    return [{shared}, {own}]\n'
    root = project(tmp_path, {
        'app/big_one.py': large.format(name='big_one', shared=_words('both', 10), own=_words('alpha', 60)),
        'app/big_two.py': large.format(name='big_two', shared=_words('both', 10), own=_words('beta', 60))})
    ranked = [p['files'] for p in propose(root)['proposals']]
    assert ranked.index(['app/money.py', 'app/services/pricing.py']) < ranked.index(['app/big_one.py', 'app/big_two.py'])


def test_words_used_everywhere_weigh_less_than_words_two_functions_share(tmp_path):
    # Twelve files share six words used everywhere; counted alike, those pairs would win.
    from core.milestones.propose import propose
    common = {f'app/common_{i}.py': f'def common_{i}():\n    return [{_words("everywhere", 6)}]\n' for i in range(12)}
    ranked = [p['files'] for p in propose(project(tmp_path, common))['proposals']]
    assert ranked[0] == ['app/money.py', 'app/services/pricing.py']


def test_a_large_project_is_scored_within_its_budget(tmp_path):
    # sqlalchemy's 245 files spent the whole 30 s cutting functions out of their files, and nothing was proposed.
    from core.milestones.propose import propose
    # The cost was functions times file length, so a few long files show it best.
    body = ''.join(f'def handler_{n}(event):\n    return event.get("field_{n}") or fallback_{n % 7}\n\n\n'
                   for n in range(1500))
    files = {f'app/module_{m}.py': body.replace('handler_', f'handler_{m}_') for m in range(4)}
    value = propose(project(tmp_path, files), seconds=10)
    assert value['proposals']
    assert not any('time budget' in issue for issue in value['coverage']['issues'])


def test_each_function_is_cut_out_exactly_as_ast_cuts_it(monkeypatch):
    # The text itself, not its tokens: a cut one character long can still yield the same tokens.
    import ast
    from core.milestones import propose
    source = ('# café\r\nclass Meter:\r\n    def read(self):  # été\r\n        return "é" + UNIT  # x\r\n'
              '\r\n    async def poll(self): return await tick()\r\n\x0c\ndef outer(x):\r    def inner(y):\r'
              '        return y * RATE\r    return inner(x)\nlabel = "ü"; one = lambda: 0\ndef last(): return "▄"  # y')
    tree = ast.parse(source)
    expected = [(node.name, ast.get_source_segment(source, node)) for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert len(expected) == 5
    monkeypatch.setattr(propose, '_tokens', lambda text: text)
    assert propose._functions(source) == expected


def test_the_same_project_gets_the_same_proposals_in_every_process(tmp_path):
    # sqlalchemy's tied dialect methods came back in a different order from run to run: float sums
    # followed set order, which follows each process's hash seed.
    import os
    import random
    import sys
    from pathlib import Path
    # Thirty rules, each copied into two files, all weighted alike: their pairs tie exactly, so
    # they belong in file order. Word n is also used by n + 1 other functions, so words weigh differently,
    # and those come first (app/common_*), so a pair's words are summed in another function's set order.
    groups = {g: [f'g{g}_word_{n}' for n in range(12)] for g in range(30)}
    copies = {}
    for g, words in groups.items():
        for copy in range(2):
            order = random.Random(g * 2 + copy).sample(words, len(words))
            copies[f'app/dialect_{g}_{copy}.py'] = f'def setup_{g}_{copy}(connection):\n    return [{", ".join(order)}]\n'
    spread = {f'app/common_{k}.py': 'def use_{}():\n    return [{}]\n'.format(
        k, ', '.join(w for words in groups.values() for n, w in enumerate(words) if n >= k)) for k in range(12)}
    root = project(tmp_path, {**copies, **spread})
    launcher = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_milestones.py'
    orders = set()
    for seed in range(6):
        done = subprocess.run([sys.executable, str(launcher), '--propose', '--json', '--project', str(root)],
                              capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONHASHSEED': str(seed)})
        orders.add(tuple(tuple(p['files']) for p in json.loads(done.stdout)['proposals']
                         if p['functions'][0].startswith('setup_')
                         and p['functions'][0].rsplit('_', 1)[0] == p['functions'][1].rsplit('_', 1)[0]))
    assert len(orders) == 1
    tied = orders.pop()
    assert len(tied) == 30 and list(tied) == sorted(tied)


def test_the_limit_bounds_the_list(tmp_path):
    from core.milestones.propose import propose
    assert len(propose(project(tmp_path), limit=1)['proposals']) == 1


def _cli(*args):
    import sys
    from pathlib import Path
    launcher = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_milestones.py'
    return subprocess.run([sys.executable, str(launcher), *args], capture_output=True, text=True, encoding='utf-8')


def test_the_command_prints_words_its_console_cannot_encode(tmp_path):
    # rich's block characters crashed it on a Windows pipe (cp1252); force that console everywhere.
    import os
    import sys
    from pathlib import Path
    bars = "def {name}(width):\n    return '▄▀' * width + BAR_EDGE\n"
    root = project(tmp_path, {'app/bars.py': bars.format(name='bar_top'), 'app/meter.py': bars.format(name='meter_top')})
    launcher = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_milestones.py'
    for form in (['--json'], []):
        done = subprocess.run([sys.executable, str(launcher), '--propose', '--project', str(root), *form],
                              capture_output=True, env={**os.environ, 'PYTHONIOENCODING': 'cp1252'})
        assert done.returncode == 0, done.stderr.decode('utf-8', 'replace')
        assert '▄▀' in done.stdout.decode('utf-8')


def test_the_command_lists_proposals_with_reasons_and_entries_to_certify(tmp_path):
    root = project(tmp_path)
    done = _cli('--propose', '--project', str(root))
    assert done.returncode == 0, done.stderr
    assert 'app/money.py' in done.stdout and 'app/services/pricing.py' in done.stdout
    assert 'ROUND_HALF_UP' in done.stdout
    assert '"inputs": [' in done.stdout
    assert 'elevenpowers.milestones.json' in done.stdout
    assert not (root / 'elevenpowers.milestones.json').exists()


def test_the_command_speaks_json_and_honours_the_limit(tmp_path):
    done = _cli('--propose', '--limit', '1', '--json', '--project', str(project(tmp_path)))
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    assert [p['files'] for p in value['proposals']] == [['app/money.py', 'app/services/pricing.py']]


def test_a_token_held_by_too_many_functions_is_skipped_and_said(tmp_path, monkeypatch):
    from core.milestones import propose as module
    monkeypatch.setattr(module, 'MAX_HOLDERS', 1)
    value = module.propose(project(tmp_path))
    assert value['proposals'] == []
    assert any('skipped' in issue for issue in value['coverage']['issues'])


# --- grounding: only what a person declared reaches the agent ----------------

RULE = {'id': 'lodging-tax', 'description': 'Lodging tax rounds half-up to the cent, per charge.',
        'inputs': ['app/money.py', 'app/services/pricing.py'],
        'checks': [{'kind': 'test_suite', 'command': 'python -m pytest -q'}]}
ALONE = {'id': 'greeting', 'description': 'Greetings are title case.', 'inputs': ['app/names.py'],
         'checks': [{'kind': 'test_suite', 'command': 'python -m pytest -q'}]}


def _hook(event, payload):
    import sys
    from pathlib import Path
    return subprocess.run([sys.executable, '-m', 'core.hook', event], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1])


def _brief(root, path):
    done = _hook('PreToolUse', {'cwd': str(root), 'tool_name': 'Edit', 'tool_input': {'file_path': str(root / path)}})
    return json.loads(done.stdout)['hookSpecificOutput'].get('additionalContext', '') if done.stdout.strip() else ''


def declared(tmp_path):
    root = project(tmp_path)
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [RULE, ALONE]}),
                                                       encoding='utf-8')
    for args in (['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'fix the lodging tax rounding'})
    return root


def test_before_an_edit_a_declared_rule_names_the_other_file_that_keeps_it(tmp_path):
    brief = _brief(declared(tmp_path), 'app/money.py')
    assert 'lodging-tax' in brief and 'rounds half-up to the cent' in brief, brief
    assert 'app/services/pricing.py' in brief, brief


def test_the_rule_is_said_once_per_file_not_on_every_edit(tmp_path):
    root = declared(tmp_path)
    _brief(root, 'app/money.py')
    _hook('PostToolUse', {'cwd': str(root), 'tool_name': 'Edit', 'tool_input': {'file_path': str(root / 'app/money.py')}})
    assert 'lodging-tax' not in _brief(root, 'app/money.py')


def _shell(root, command='python edit.py'):
    done = _hook('PostToolUse', {'cwd': str(root), 'tool_name': 'Bash', 'tool_input': {'command': command},
                                 'tool_response': {'stdout': '', 'stderr': '', 'exit_code': 0}})
    return json.loads(done.stdout)['hookSpecificOutput'].get('additionalContext', '') if done.stdout.strip() else ''


def test_an_agent_that_edits_through_the_shell_is_told_too(tmp_path):
    # Seen in the acted-on pilot: agents wrote files with Python in Bash, and no Edit brief ever fired.
    root = declared(tmp_path)
    money = root / 'app/money.py'
    money.write_text(money.read_text(encoding='utf-8').replace('ROUND_HALF_UP)', 'ROUND_HALF_EVEN)'), encoding='utf-8')
    note = _shell(root)
    assert 'lodging-tax' in note and 'app/services/pricing.py' in note, note
    assert 'lodging-tax' not in _shell(root), 'said once per file, not after every command'


def test_a_shell_command_that_touches_no_declared_file_says_nothing(tmp_path):
    root = declared(tmp_path)
    (root / 'app/store.py').write_text('# changed\n', encoding='utf-8')
    assert 'Declared rule' not in _shell(root)


def test_a_shell_change_outside_any_rule_keeps_the_file_s_own_brief_for_its_first_edit(tmp_path):
    root = declared(tmp_path)
    (root / 'app/rates.py').write_text('LODGING_RATE = 0.12\n', encoding='utf-8')
    _shell(root)
    assert 'imported by app/money.py' in _brief(root, 'app/rates.py')


def test_a_declared_file_changed_before_the_task_opened_is_not_put_on_the_agent(tmp_path):
    root = declared(tmp_path)
    (root / 'app/money.py').write_text('# the developer, mid-change\n', encoding='utf-8')
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'add a store opening hours page'})
    assert 'lodging-tax' not in _shell(root)


def test_a_file_already_briefed_before_an_edit_is_not_told_again_after_the_shell(tmp_path):
    root = declared(tmp_path)
    assert 'lodging-tax' in _brief(root, 'app/money.py')
    (root / 'app/money.py').write_text('# changed\n', encoding='utf-8')
    assert 'lodging-tax' not in _shell(root)


def test_files_in_no_shared_rule_get_no_rule_note(tmp_path):
    root = declared(tmp_path)
    assert 'Declared rule' not in _brief(root, 'app/names.py')
    assert 'Declared rule' not in _brief(root, 'app/store.py')



# --- at completion: the person is told which declared rule was changed only partly ---

def _report(root, touched):
    from core.ledger import Ledger
    from core.obligations import Claim, Risk
    from core.report import end_report
    base = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()
    return end_report(Ledger(root=root, claims=[Claim.BUG_FIXED], risk=Risk.LOW, base=base, touched=touched))


def test_the_end_report_names_a_declared_rule_changed_in_one_file_only(tmp_path):
    text = _report(declared(tmp_path), ['app/money.py'])
    assert 'lodging-tax' in text and 'changed app/money.py, not app/services/pricing.py' in text, text


def test_the_end_report_is_quiet_when_a_rule_changed_everywhere_or_nowhere(tmp_path):
    root = declared(tmp_path)
    assert 'lodging-tax' not in _report(root, ['app/money.py', 'app/services/pricing.py'])
    assert 'lodging-tax' not in _report(root, ['app/names.py'])



def test_every_proposed_entry_has_its_own_id_so_several_can_be_certified(tmp_path):
    # Two different pairs of `total` functions would both be called rule-total-total.
    from core.milestones.propose import propose
    total = 'def total(lines):\n    return sum(line.amount_cents for line in lines) // VAT_DIVISOR\n'
    root = project(tmp_path, {'app/a.py': total, 'app/b.py': total, 'app/c.py': total})
    ids = [p['entry']['id'] for p in propose(root)['proposals']]
    assert len(ids) == len(set(ids)), ids


def test_a_proposed_id_never_repeats_one_already_declared(tmp_path):
    from core.milestones.propose import propose
    root = project(tmp_path)
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [dict(
        RULE, id='rule-lodging_tax-quote_tax', inputs=['app/money.py'])]}), encoding='utf-8')
    first = propose(root)['proposals'][0]
    assert first['files'] == ['app/money.py', 'app/services/pricing.py']
    assert first['entry']['id'] != 'rule-lodging_tax-quote_tax'
