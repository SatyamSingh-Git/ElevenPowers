"""Actual CLI and Actions file transport, without project verification."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.test_patchproof_report import project, seed
from tests.test_patchproof_github import event, snapshot

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_github.py'


def invoke(root, *args, env=None):
    return subprocess.run([sys.executable, str(CLI), '--project', str(root), '--repository', 'example/project',
                           *map(str, args)], capture_output=True, text=True, timeout=120, env=env)


def test_local_cli_writes_external_files_without_runner_or_project_mutation(project, tmp_path_factory):
    root, base, head = project
    seed(root)
    before = snapshot(root)
    output = tmp_path_factory.mktemp('cli-output') / 'new'
    done = invoke(root, '--base', base, '--head', head, '--output-dir', output)
    assert done.returncode == 0, done.stderr
    assert snapshot(root) == before
    metadata = json.loads(done.stdout)
    assert Path(metadata['evidence']).is_file()
    assert json.loads((output/'evidence.json').read_text())['subject']['head'] == head
    assert invoke(root, '--base', base, '--head', head, '--output-dir', output).returncode != 0


def test_actions_files_receive_summary_and_fixed_output_keys(project, tmp_path_factory):
    root, base, head = project
    seed(root)
    parent = tmp_path_factory.mktemp('runner')
    summary, outputs = parent/'summary.md', parent/'outputs.txt'
    summary.touch(); outputs.touch()
    context = parent/'event.json'
    context.write_text(json.dumps(event(base, head)))
    env = {**os.environ, 'GITHUB_STEP_SUMMARY': str(summary), 'GITHUB_OUTPUT': str(outputs)}
    before = snapshot(root)
    done = invoke(root, '--base', base, '--head', head, '--event', context, '--actions', env=env)
    assert done.returncode == 0, done.stderr
    assert snapshot(root) == before
    assert head in summary.read_text() and 'not patch safety' in summary.read_text()
    assert 'directory<<' in outputs.read_text() and 'artifact_name<<' in outputs.read_text()
    assert not done.stdout.startswith('::')


def test_bad_pr_or_runner_target_refuses_before_output(project, tmp_path_factory):
    root, base, head = project
    seed(root)
    parent = tmp_path_factory.mktemp('refusal')
    context = parent/'event.json'
    context.write_text(json.dumps(event(base, 'a'*40)))
    output = parent/'new'
    refused = invoke(root, '--base', base, '--head', head, '--event', context, '--output-dir', output)
    assert refused.returncode != 0 and 'selected patch does not match PR base and head' in refused.stderr
    assert not output.exists()
    before = snapshot(root)
    env = {**os.environ, 'GITHUB_STEP_SUMMARY': str(root/'service.py'), 'GITHUB_OUTPUT': str(parent/'outputs')}
    assert invoke(root, '--actions', '--output-dir', output, env=env).returncode != 0
    assert snapshot(root) == before and not output.exists()


@pytest.mark.parametrize('url', [
    'http://github.com/example/project/actions/runs/42/artifacts/99',
    'https://github.com/elsewhere/project/actions/runs/42/artifacts/99',
    'https://github.com/example/project/actions/runs/43/artifacts/99',
    'https://github.com@example.test/example/project/actions/runs/42/artifacts/99',
    'https://github.com/example/project/actions/runs/42/artifacts/99?token=secret',
    'https://github.com/example/project/actions/runs/42/artifacts/99\n::error::bad'])
def test_wrong_artifact_link_is_refused(url):
    from core.patchproof.github_context import artifact_link
    with pytest.raises(ValueError):
        artifact_link('example/project', '42', url)


def test_uploader_link_matches_exact_repository_run_and_artifact(project, tmp_path_factory):
    from core.patchproof.github_context import artifact_link
    url = 'https://github.com/example/project/actions/runs/42/artifacts/99'
    assert artifact_link('example/project', '42', url).endswith('('+url+')')
    root, _, _ = project
    parent = tmp_path_factory.mktemp('link-runner')
    summary = parent/'summary.md'
    env = {**os.environ, 'GITHUB_STEP_SUMMARY': str(summary)}
    done = invoke(root, '--actions', '--link-artifact', url, '--run-id', '42', env=env)
    assert done.returncode == 0, done.stderr
    assert url in summary.read_text() and 'login' in summary.read_text()
