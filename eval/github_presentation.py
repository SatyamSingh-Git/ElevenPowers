"""Disposable actual-command acceptance; no model, install or hidden verification."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from core.config import Config, save
from core.ledger import Ledger
from core.parsers import parse
from core.process import run
from core.patchproof.github import build


def _git(root, *args):
    done = run(['git', '-c', 'safe.directory='+str(root), '-c', 'core.hooksPath='+os.devnull,
                *args], cwd=root, timeout=10, shell=False)
    if done.returncode:
        raise ValueError('disposable Git setup failed')
    return done.stdout.strip()


def _snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


def _case(root, mode, repository, external_inputs=False):
    root.mkdir()
    _git(root, 'init', '-q')
    _git(root, 'config', 'user.email', 'exercise@example.invalid')
    _git(root, 'config', 'user.name', 'Evidence exercise')
    _git(root, 'config', 'core.autocrlf', 'false')
    Ledger(root=root).save()
    dependency_check = ''
    if external_inputs:
        from core.inputs.bindings import bind
        dependency = root.parent/(mode+'-dependency')
        dependency.mkdir()
        target = dependency/'settings.json'
        target.write_bytes(b'{"value":2}\n')
        (root/'elevenpowers.inputs.json').write_text(json.dumps({'schema':1,'witnesses':[
            {'id':'runtime-data','root':'deps','paths':['settings.json']}]}),encoding='utf-8')
        bind(root,'deps',dependency)
        dependency_check = f'assert __import__("json").loads(Path({str(target)!r}).read_text())["value"] == 2\n'
    (root/'service.py').write_text('value=1\n', encoding='utf-8')
    (root/'check.py').write_text(
        "from pathlib import Path\nimport service,time\n"
        "p=Path('.elevenpowers/count.txt')\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
        +( "time.sleep(60)\n" if mode == 'incomplete' else '')
        +dependency_check
        +"assert service.value == 2, 'independent expected value'\n"
        +"print('TAP version 13\\nok 1 - expected value\\n1..1\\n# pass 1\\n# fail 0')\n",
        encoding='utf-8')
    _git(root, 'add', '.')
    _git(root, 'commit', '-qm', 'base')
    base = _git(root, 'rev-parse', 'HEAD')
    (root/'service.py').write_text('value=3\n' if mode == 'failed' else 'value=2\n', encoding='utf-8')
    _git(root, 'add', '.')
    _git(root, 'commit', '-qm', 'patch')
    head = _git(root, 'rev-parse', 'HEAD')
    command = f'"{sys.executable}" -B check.py'
    save(root, Config(auto_detect=False, commands={'tests': command, 'typecheck': 'declared-check-not-run'}))
    try:
        done = run(command, cwd=root, timeout=2 if mode == 'incomplete' else 10)
        text, status = done.stdout+done.stderr, done.returncode
    except subprocess.TimeoutExpired as error:
        text, status = (error.stdout or '')+(error.stderr or ''), None
    if mode == 'passing' and status != 0 or mode == 'failed' and status == 0 or mode == 'incomplete' and status is not None:
        raise ValueError('independent producer control did not establish its expected outcome')
    ledger = Ledger.load(root)
    ledger.add(parse(command, text, status, root))
    ledger.save()
    before = _snapshot(root)
    value = build(root, base, head, repository=repository)
    if _snapshot(root) != before:
        raise ValueError('presentation mutated the exercise project')
    return {'root': str(root), 'base': base, 'head': head, 'value': value,
            'state': value['bundle']['checks'][0]['state'],
            'count': int((root/'.elevenpowers/count.txt').read_text())}


def prepare(directory, *, repository='example/project', external_inputs=False):
    directory = Path(directory).absolute()
    if directory.resolve() != directory or directory.is_symlink():
        raise ValueError('linked exercise directory')
    directory.mkdir()
    cases = [_case(directory/mode, mode, repository, external_inputs) for mode in ('passing', 'failed', 'incomplete')]
    states = [c['state'] for c in cases]
    if states != ['current', 'failed', 'incomplete']:
        raise ValueError('presentation lost actual producer states')
    return {'states': states, 'readonly': True, 'counts': [c['count'] for c in cases],
            'passing': cases[0]['value'], 'project': cases[0]['root'],
            'base': cases[0]['base'], 'head': cases[0]['head']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repository', default='example/project')
    parser.add_argument('--actions-output', type=Path)
    parser.add_argument('--external-inputs',action='store_true')
    args = parser.parse_args()
    result = prepare(args.output, repository=args.repository,external_inputs=args.external_inputs)
    print(json.dumps({k: v for k, v in result.items() if k != 'passing'}, ensure_ascii=True))
    if args.actions_output:
        # Only controlled fixture paths and Git hashes; no captured output enters
        # the runner file. Delimiters protect unusual temp-directory filenames.
        from plugin.bin.ep_github import outputs, append
        append(args.actions_output, outputs({k: result[k] for k in ('project', 'base', 'head')}))


if __name__ == '__main__':
    main()
