"""Presentation output stays literal, bounded and separate from inspected source."""
import hashlib
import json

import pytest

from core.config import Config, save
from tests.test_patchproof_report import project, seed
from tests.test_patchproof_github import snapshot


@pytest.fixture
def presentation(project):
    from core.patchproof.github import build
    root, base, head = project
    seed(root, declaration='tests')
    save(root, Config(auto_detect=False, commands={'tests': 'python -m pytest', 'typecheck': 'missing'}))
    return root, build(root, base, head, repository='example/project')


def test_summary_preserves_gaps_and_full_patch_identity(presentation):
    from core.patchproof.github_output import markdown
    root, value = presentation
    text = markdown(value)
    assert 'informational' in text.lower() and 'not patch safety' in text
    assert value['subject']['base'] in text and value['subject']['head'] in text
    assert 'typecheck' in text and 'absent' in text
    assert 'current' in text and 'UNVERIFIED' in text
    assert 'Unobserved patch paths' in text and 'Unsupported properties' in text


def test_command_text_cannot_create_markdown_or_expose_known_credentials(project):
    from core.patchproof.github import build
    from core.patchproof.github_output import markdown
    root, base, head = project
    seed(root)
    save(root, Config(auto_detect=False, commands={'tests': '![](https://evil.test/image) | <script> @someone\n::error:: ghp_ABCDEFGHIJKLM1234567890'}))
    value = build(root, base, head, repository='example/project')
    text = markdown(value)
    assert '<script>' not in text and '![](' not in text and '@someone' not in text
    assert 'ABCDEFGHIJKLM1234567890' not in text and 'REDACTED' in text


def test_new_external_output_keeps_project_bytes_and_bundle_hash(presentation, tmp_path_factory):
    from core.patchproof.github_output import publish
    from core.patchproof.github import canonical
    root, value = presentation
    before = snapshot(root)
    destination = tmp_path_factory.mktemp('output-parent') / 'new'
    paths = publish(value, destination, project=root)
    assert snapshot(root) == before
    saved = json.loads(paths['evidence'].read_text())
    assert saved['bundle_sha256'] == hashlib.sha256(canonical(saved['bundle'])).hexdigest()
    assert paths['summary'].read_text().startswith('# ElevenPowers')
    with pytest.raises((ValueError, FileExistsError)):
        publish(value, destination, project=root)


def test_output_inside_project_is_refused_before_writing(presentation):
    from core.patchproof.github_output import publish
    root, value = presentation
    before = snapshot(root)
    with pytest.raises(ValueError):
        publish(value, root / 'artifact', project=root)
    assert snapshot(root) == before


def test_linked_output_parent_is_refused(presentation, tmp_path_factory):
    from core.patchproof.github_output import publish
    root, value = presentation
    parent = tmp_path_factory.mktemp('links')
    target = parent / 'target'
    target.mkdir()
    link = parent / 'link'
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip('directory symlink unavailable')
    with pytest.raises(ValueError):
        publish(value, link / 'new', project=root)
    assert not (target / 'new').exists()


def test_summary_omissions_are_visible_and_artifact_is_complete(presentation, tmp_path_factory):
    from core.patchproof.github_output import publish, MAX_SUMMARY_BYTES
    from core.patchproof.github import canonical
    root, value = presentation
    check = value['bundle']['checks'][0]
    value['bundle']['checks'] = [{**check, 'property': f'property-{i}', 'command': '界' * 700}
                               for i in range(180)]
    value['bundle']['coverage']['unobserved_patch_paths'] = ['service.py']
    value['bundle_sha256'] = hashlib.sha256(canonical(value['bundle'])).hexdigest()
    paths = publish(value, tmp_path_factory.mktemp('omissions') / 'new', project=root)
    assert paths['summary'].stat().st_size <= MAX_SUMMARY_BYTES
    assert '116 rows omitted' in paths['summary'].read_text()
    assert 'truncated' in paths['summary'].read_text()
    assert 'Unobserved patch paths: 1' in paths['summary'].read_text()
    assert len(json.loads(paths['evidence'].read_text())['bundle']['checks']) == 180


def test_hash_or_byte_limit_failure_creates_no_output(presentation, tmp_path_factory, monkeypatch):
    from core.patchproof import github_output
    root, value = presentation
    destination = tmp_path_factory.mktemp('refuse') / 'new'
    value['bundle_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        github_output.publish(value, destination, project=root)
    assert not destination.exists()
    from core.patchproof.github import canonical
    value['bundle_sha256'] = hashlib.sha256(canonical(value['bundle'])).hexdigest()
    monkeypatch.setattr(github_output, 'MAX_ARTIFACT_BYTES', 100)
    with pytest.raises(ValueError):
        github_output.publish(value, destination, project=root)
    assert not destination.exists()


def test_known_credential_command_keys_are_scrubbed_in_all_public_exports(project):
    from core.export import build as report
    from core.patchproof.github import build
    from core.config import load
    root, base, head = project
    secret = 'ghp_' + 'Abc123XYZ' * 4
    seed(root)
    save(root, Config(auto_detect=False, commands={secret: 'unused'}))
    before = snapshot(root)
    assert secret not in json.dumps(report(root))
    assert secret not in json.dumps(build(root, base, head, repository='example/project'))
    assert secret in load(root).commands
    assert snapshot(root) == before


def test_public_key_redaction_collision_is_controlled_and_private_config_retained(project):
    from core.export import build as report
    from core.config import load
    root, _, _ = project
    keys = ['ghp_' + 'Abc123XYZ' * 4, 'ghp_' + 'Def456UVW' * 4]
    seed(root)
    save(root, Config(auto_detect=False, commands={keys[0]: 'one', keys[1]: 'two'}))
    with pytest.raises(ValueError, match='collision'):
        report(root)
    assert list(load(root).commands) == keys
