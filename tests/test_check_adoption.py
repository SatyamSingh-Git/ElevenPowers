"""Real native prompt producers and executable guidance, without model calls."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
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
    assert 'Owned declared checks (tests, build):' in context
    assert 'Owned check arguments:' in context
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


def test_batch_guidance_has_readable_arguments_and_one_executable_covering_all_properties(tmp_path):
    project(tmp_path)
    text=guidance(tmp_path,batch=True)
    assert len(text)<=2000 and 'Owned check arguments: ' in text
    preview=next(line for line in text.splitlines() if line.startswith('Owned check arguments: '))
    args=json.loads(preview.split(': ',1)[1])
    assert Path(args[1]).name=='ep_check.py' and '--all' in args
    line=next(line for line in text.splitlines() if line.startswith('Owned declared checks (tests, build): '))
    assert invocation_args(line.split(': ',1)[1])==args
    done=subprocess.run(args,capture_output=True,text=True,timeout=30)
    assert done.returncode==0,done.stderr
    assert 'Declared check tests: passed' in done.stdout
    assert 'Declared check build: passed' in done.stdout


def test_filtered_batch_advice_keeps_only_selected_command_instead_of_broadening(tmp_path):
    project(tmp_path)
    command=Ledger.load(tmp_path).config.command_for('build')
    text=guidance(tmp_path,commands=[command],batch=True)
    assert text.startswith('Owned declared check build: ')
    args=invocation_args(text.split(': ',1)[1])
    assert '--all' not in args and args[2]=='build'


def test_long_batch_instruction_is_explicitly_omitted_without_cutting_its_command(tmp_path,monkeypatch):
    import core.hosts.setup as setup
    project(tmp_path)
    monkeypatch.setattr(setup,'invocation',lambda args:'x'*2100)
    text=guidance(tmp_path,batch=True)
    assert len(text)<=2000 and 'instructions not shown' in text
    assert 'tests' in text and 'build' in text and 'x'*100 not in text


def test_prompt_advice_reserves_its_receipt_explanation_inside_the_bound(tmp_path,monkeypatch):
    import core.hosts.setup as setup
    from core.hook import _declared_advice
    project(tmp_path)
    for size in range(1400,2001,25):
        monkeypatch.setattr(setup,'invocation',lambda args,n=size:'x'*n)
        assert len(_declared_advice(tmp_path,'Verify the project'))<=2000
