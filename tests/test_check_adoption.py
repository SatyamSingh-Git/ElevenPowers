"""Real native prompt producers and executable guidance, without model calls."""
from contextlib import redirect_stdout
import io
import json
import sys

import pytest

from core.checks import guidance
from core.config import Config, save
from core.hook import dispatch
from core.hosts.readiness import ingress
from core.hosts.setup import invocation_args
from core.ledger import Ledger


def project(root, profile='guide'):
    (root/'source.py').write_text('value=1\n')
    save(root, Config(profile=profile, auto_detect=False, commands={
        'tests': f'"{sys.executable}" -c "print(\'1 passed\')"',
        'build': f'"{sys.executable}" -c "print(\'built\')"'}))


def prompt(root, text):
    stream=io.StringIO()
    with redirect_stdout(stream), ingress('host'):
        dispatch('UserPromptSubmit', {'cwd':str(root), 'session_id':'no-model-producer', 'prompt':text})
    return stream.getvalue()


def test_encoded_guidance_identifies_properties_before_executable_text(tmp_path):
    project(tmp_path)
    lines=guidance(tmp_path).splitlines()
    assert lines[0].startswith('Owned declared check tests: ')
    assert lines[1].startswith('Owned declared check build: ')
    for selected,line in zip(('tests','build'),lines):
        args=invocation_args(line.split(': ',1)[1])
        assert args[2]==selected and args[-1]==str(tmp_path.resolve())
    assert len(guidance(tmp_path))<=2000
    assert not Ledger.load(tmp_path).evidence


@pytest.mark.parametrize('scenario',[
    'This is a new task. Verify the changed dependency without editing files.',
    'New task: recheck retained evidence; do not edit anything.',
    'Separate task: validate the project checks without changing source.'
])
def test_new_no_edit_verification_task_gets_owned_instructions_without_a_claim(tmp_path,scenario):
    project(tmp_path)
    prompt(tmp_path,'Inspect the repository')
    old=Ledger.load(tmp_path).task
    text=prompt(tmp_path,scenario)
    ledger=Ledger.load(tmp_path)
    assert ledger.task!=old and ledger.claims==[]
    assert text, 'The no-edit verification prompt emitted no owned instructions'
    value=json.loads(text)
    context=value['hookSpecificOutput']['additionalContext']
    assert 'Owned declared check tests:' in context
    assert 'Owned declared check build:' in context
    assert 'outer' in context.lower() and 'receipt' in context.lower()
    assert not ledger.evidence
    assert not (tmp_path/'.elevenpowers/verification.json').exists()
    assert prompt(tmp_path,scenario)==''
    assert prompt(tmp_path,'continue')==''
    assert Ledger.load(tmp_path).task==ledger.task


@pytest.mark.parametrize('profile,scenario',[
    ('off','This is a new task. Verify without edits.'),
    ('guide','New task: read the README.')
])
def test_passive_and_unrelated_requests_do_not_emit_or_execute_instructions(tmp_path,profile,scenario):
    project(tmp_path,profile)
    text=prompt(tmp_path,scenario)
    assert 'Owned declared check' not in text
    if profile=='off':
        assert text==''
    assert not Ledger.load(tmp_path).evidence
    assert not (tmp_path/'.elevenpowers/verification.json').exists()
