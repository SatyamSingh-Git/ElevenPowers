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


def test_the_limit_bounds_the_list(tmp_path):
    from core.milestones.propose import propose
    assert len(propose(project(tmp_path), limit=1)['proposals']) == 1


def _cli(*args):
    import sys
    from pathlib import Path
    launcher = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_milestones.py'
    return subprocess.run([sys.executable, str(launcher), *args], capture_output=True, text=True, encoding='utf-8')


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
