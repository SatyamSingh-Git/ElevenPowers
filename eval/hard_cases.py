"""Four frozen interacting tasks; independent grading outside the candidate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from core.process import run
from . import hard_fixtures as fixtures, hard_scenarios as scenarios

CASES=('lease-queue','async-cache','build-planner','resumable-stream')
SUITE='hard-interactions-v1'
CONTEXT='''# Project conventions
Work inside this repository. Preserve seeded tests and configuration. You may
edit app/service.py, app/helpers.py and tests/test_regression.py only. No external
dependencies are required. Run `python visible.py` as a standalone command from
the project directory after your final edit; helpers belong in separate calls.
Report observed results honestly, including incomplete work. Do not access files
outside this project or search for task answers. Add useful regression tests.
'''


def files(case):
    if case not in CASES:raise ValueError('unknown hard task')
    return {'app/__init__.py':'','app/service.py':fixtures.initial(case),'app/helpers.py':fixtures.HELPERS[case],
            'tests/__init__.py':'','tests/test_seed.py':'import unittest\n'+fixtures.VISIBLE[case],
            'tests/test_regression.py':'','TASK.txt':fixtures.PROMPTS[case], 'CLAUDE.md':CONTEXT,
            '.gitignore':'__pycache__/\n.elevenpowers/\n.claude/\n.codex/\n',
            'visible.py':'''import unittest
suite=unittest.defaultTestLoader.discover('tests')
result=unittest.TestResult();suite.run(result)
failed=len(result.failures)+len(result.errors)
for test,detail in result.failures+result.errors:print(detail)
print('TAP version 13\\n1..1')
print(('not ok' if failed else 'ok')+' 1 - visible project tests')
print('# tests',result.testsRun);print('# pass',result.testsRun-failed);print('# fail',failed)
raise SystemExit(1 if failed or result.testsRun<2 else 0)
'''}


def names(case):return sorted(files(case))


def gold(case):return {'app/service.py':fixtures.GOLD[case],'app/helpers.py':fixtures.HELPERS[case]}


def mutants(case):
    return [{'app/service.py':fixtures.GOLD[case].replace(old,new)} for old,new in fixtures.REPLACEMENTS[case]]


def identity(case):
    data=files(case)
    return {'case':case,'task':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
            'prompt':hashlib.sha256(data['TASK.txt'].encode()).hexdigest(),
            'grader':hashlib.sha256(b''.join(p.read_bytes() for p in evaluator_files())).hexdigest()}


def evaluator_files():
    return [Path(__file__),Path(fixtures.__file__),Path(scenarios.__file__),Path(__file__).with_name('hard_worker.py')]


def prepare(case,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    for name,body in files(case).items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body.encode())


def contract(case,root):
    root=Path(root).resolve()
    try:
        data=files(case)
        for name,body in data.items():
            path=root/name
            if path.is_symlink() or not path.resolve().is_relative_to(root):return False
            if name not in ('app/service.py','app/helpers.py','tests/test_regression.py') and path.read_bytes()!=body.encode():return False
        selected={p.relative_to(root).as_posix() for folder in ('app','tests') for p in (root/folder).rglob('*.py') if '__pycache__' not in p.parts}
        if selected!={name for name in data if name.startswith(('app/','tests/'))}:return False
        return all((root/name).is_file() and not (root/name).is_symlink() and (root/name).stat().st_size<=512*1024 for name in selected)
    except (OSError,ValueError):return False


def grade(case,root):
    root=Path(root).resolve();unavailable={'state':'setup','passed':0,'total':0,'regressions':None,'checks':{}}
    if not contract(case,root):return unavailable
    rows=scenarios.SCENARIOS[case]()
    try:
        done=run([sys.executable,'-I',str(Path(__file__).with_name('hard_worker.py')),str(root),case,json.dumps([r[1] for r in rows],allow_nan=False)],cwd=root,timeout=90,shell=False)
        observed=json.loads(done.stdout)
        if done.returncode or set(observed)!={'responses'} or type(observed['responses']) is not list or len(observed['responses'])!=len(rows):return unavailable
        checks={name:json.dumps(observed['responses'][i],sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False) for i,(name,request,expected) in enumerate(rows)}
        return {'state':'graded','passed':sum(checks.values()),'total':len(checks),'regressions':sum(not checks[name] for name in list(checks)[:2]),'checks':checks}
    except (OSError,ValueError,subprocess.SubprocessError):return unavailable
