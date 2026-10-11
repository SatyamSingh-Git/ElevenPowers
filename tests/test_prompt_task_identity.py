"""Task correlation exists independently of conservative claim inference."""
import json

import pytest

from core.hook import on_prompt
from core.ledger import Ledger
from core.obligations import Claim
from core.parsers import parse


def prompt(root, text):
    assert on_prompt({'prompt': text}, root) == 0
    return Ledger.load(root)


@pytest.mark.parametrize('text', ['Read EXERCISE.md and follow its instructions.',
                                 'what does app.py do?', 'continue'])
def test_first_nonempty_prompt_opens_identity_without_inventing_claim(tmp_path, text):
    ledger = prompt(tmp_path, text)
    assert ledger.task
    assert ledger.request == text
    assert ledger.claims == []


def test_new_read_subject_cannot_inherit_previous_evidence(tmp_path):
    first = prompt(tmp_path, 'fix the boundary bug')
    (tmp_path / 'app.py').write_text('value = 1\n')
    first.add(parse('python -m pytest', '1 passed in 0.01s', 0, tmp_path))
    first.seen = ['app.py']; first.touched = ['app.py']; first.guided = True
    first.save()
    second = prompt(tmp_path, 'Read the deployment instructions.')
    assert second.task and second.task != first.task
    assert not second.claims and not second.evidence
    assert not second.seen and not second.touched and not second.guided


@pytest.mark.parametrize('text', ['continue', 'go on', 'yes do it'])
def test_continuation_preserves_claim_and_identity(tmp_path, text):
    before = prompt(tmp_path, 'fix the boundary bug')
    after = prompt(tmp_path, text)
    assert after.task == before.task and after.claims == [Claim.BUG_FIXED]
    assert after.request == before.request


def test_repeated_claimless_prompt_and_its_continuation_keep_identity(tmp_path):
    before = prompt(tmp_path, 'Read EXERCISE.md and follow its instructions.')
    repeated = prompt(tmp_path, before.request)
    continued = prompt(tmp_path, 'continue')
    assert before.task == repeated.task == continued.task != ''
    assert continued.request == before.request


def test_question_continuation_keeps_classification_after_edit(tmp_path):
    before = prompt(tmp_path, 'what does app.py do?')
    after = prompt(tmp_path, 'continue')
    after.observe_edit('app.py')
    assert after.request == before.request
    assert not after.claims


def test_empty_prompt_does_not_create_state(tmp_path):
    assert on_prompt({'prompt': '  '}, tmp_path) == 0
    assert not (tmp_path / '.elevenpowers').exists()


def test_legacy_claimless_ledger_gets_identity_on_next_prompt(tmp_path):
    Ledger(root=tmp_path, request='Read EXERCISE.md').save()
    after = prompt(tmp_path, 'Read EXERCISE.md')
    assert after.task and not after.claims


def test_legacy_continuation_retains_existing_claim(tmp_path):
    Ledger(root=tmp_path, request='fix the boundary bug', claims=[Claim.BUG_FIXED]).save()
    after = prompt(tmp_path, 'continue')
    assert after.task and after.claims == [Claim.BUG_FIXED]
