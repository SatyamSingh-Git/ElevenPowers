"""Explicit disposable actual dependency checks; no model or installation."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

from core.config import Config, save
from core.inputs.bindings import bind
from core.ledger import Ledger
from core.patchproof.execution import verify
from core.patchproof.planning import plan
from core.patchproof.github import build
from core.patchproof.github_output import publish
from core.hosts.provenance import fingerprint
from core.process import run
from eval.github_presentation import _git, _snapshot


def case(directory,language):
    root = directory/(language+'-project'); root.mkdir()
    installed = directory/(language+'-installed'); installed.mkdir()
    _git(root,'init','-q')
    _git(root,'config','user.name','Input exercise')
    _git(root,'config','user.email','input-exercise@example.invalid')
    _git(root,'config','core.autocrlf','false')
    Ledger(root=root).save()
    target = installed/('parser.py' if language=='python' else 'parser.cjs')
    good = b'value=2\n' if language=='python' else b'module.exports={value:2};\n'
    bad = b'value=9\n' if language=='python' else b'module.exports={value:9};\n'
    target.write_bytes(good)
    if language == 'python':
        (root/'check.py').write_text('from pathlib import Path\nimport runpy\n'
            "p=Path('.elevenpowers/count.txt')\n"
            "p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
            f'assert runpy.run_path({str(target)!r})["value"]==2\n'
            'print("verified actual dependency behavior")\n',encoding='utf-8')
        args = [sys.executable,'-B','check.py']
    else:
        node = shutil.which('node')
        if not node:
            raise ValueError('actual Node producer unavailable')
        (root/'check.cjs').write_text("const fs=require('node:fs'),assert=require('node:assert/strict');\n"
            "const p='.elevenpowers/count.txt';\n"
            "fs.writeFileSync(p,String(fs.existsSync(p)?Number(fs.readFileSync(p))+1:1));\n"
            f'assert.equal(require({json.dumps(str(target))}).value,2);\n'
            'console.log("verified actual dependency behavior");\n',encoding='utf-8')
        args = [node,'check.cjs']
    (root/'elevenpowers.inputs.json').write_text(json.dumps({'schema':1,'witnesses':[
        {'id':'dependencies','root':'deps','paths':[target.name]}]}),encoding='utf-8')
    bind(root,'deps',installed)
    (root/'service.py').write_bytes(b'value=1\n')
    _git(root,'add','.'); _git(root,'commit','-qm','base')
    base = _git(root,'rev-parse','HEAD')
    (root/'service.py').write_bytes(b'value=2\n')
    _git(root,'add','.'); _git(root,'commit','-qm','change')
    head = _git(root,'rev-parse','HEAD')
    command = subprocess.list2cmdline(args) if os.name=='nt' else shlex.join(args)
    save(root,Config(auto_detect=False,commands={'tests':command}))
    counts = []
    count = lambda:int((root/'.elevenpowers/count.txt').read_text())
    first = verify(root,base,head,seconds=120,command_seconds=15); counts.append(count())
    unchanged = verify(root,base,head,seconds=120,command_seconds=15); counts.append(count())
    source = {p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
    environment = dict(os.environ)
    target.write_bytes(bad)
    independent = run(args,cwd=root,shell=False,timeout=15); counts.append(count())
    if source != {p.name:p.read_bytes() for p in root.iterdir() if p.is_file()} or environment != dict(os.environ):
        raise ValueError('controller changed project source or environment values')
    if _git(root,'rev-parse','HEAD') != head:
        raise ValueError('controller changed project head')
    planned = plan(root,base,head,seconds=120)
    drift = verify(root,base,head,seconds=120,command_seconds=15); counts.append(count())
    target.unlink()
    missing = verify(root,base,head,seconds=120,command_seconds=15); counts.append(count())
    before = _snapshot(root)
    presented = build(root,base,head,repository='example/project')
    publish(presented,directory/(language+'-evidence'),project=root)
    if _snapshot(root) != before:
        raise ValueError('readonly evidence export changed the project')
    result = {'language':language,'initial':first['state'],'unchanged':unchanged['checks'][0]['status'],
              'independent_bad_exit':independent.returncode,'drift_action':planned['checks'][0]['action'],
              'drift':drift['state'],'missing':missing['state'],'counts':counts,'readonly':True}
    if (result['initial'] != 'passed' or result['unchanged'] != 'reused' or independent.returncode == 0
            or result['drift_action'] != 'run' or result['drift'] != 'failed'
            or result['missing'] != 'incomplete' or counts != [1,1,2,3,3]):
        raise ValueError('actual dependency outcomes do not satisfy the independent protocol')
    return result


def exercise(directory):
    directory = Path(directory).absolute()
    if directory.resolve() != directory or directory.is_symlink():
        raise ValueError('linked exercise directory is unsupported')
    directory.mkdir()
    started = time.monotonic()
    cases = [case(directory,language) for language in ('python','javascript')]
    result = {'schema':1,'kind':'external_input_acceptance','cases':cases,'readonly':True,
              'runtime_fingerprint':fingerprint(),'elapsed_seconds':round(time.monotonic()-started,3),
              'limits':['Authored capability controls; not population coding benefit, complete environment identity or installed-host acceptance.']}
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(exercise(args.output),ensure_ascii=True))


if __name__ == '__main__':
    main()
