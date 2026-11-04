"""Does an agent act on a certified rule? One v3 stage per run, two arms that differ only
in elevenpowers.milestones.json.

Borrowed: the v3 runner's workspace, launch, sealing and oracles (`eval.multistage_run`,
`eval.multistage_oracles`). Added: a simulated perfect certification, fixed in advance,
and a one-stage outcome. See docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md.
"""
from pathlib import Path
import subprocess
import sys

from core.config import Config, save
from core.hosts.setup import install
from core.milestones.propose import propose
from core.surface import TEST_NAME
from . import multistage_oracles as oracles
from .heldout_run import _interpreter
from .live import _seed_git
from .multistage_cases import tree
from .multistage_run import PROJECT_SETTINGS, TOOL_ROOT
from .preservation import _write

ARMS = ('control', 'rules')
PROPOSALS = 50


def _sources(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in Path(root).rglob('*.py')
            if not TEST_NAME.search(p.relative_to(root).as_posix())}


def breaking_pairs(case, scratch):
    """Every (file a stage's reference changes, that stage's declared dependent) pair."""
    scratch = Path(scratch)
    pairs = set()
    for n, stage in enumerate(case['stages'], 1):
        for which, quiet in enumerate(stage.get('quiet') or []):
            before = _sources(tree(case, n - 1, scratch / f'{n}-{which}-before'))
            after = _sources(tree(case, n, scratch / f'{n}-{which}-after', 'quiet', which))
            pairs |= {frozenset((path, quiet['file'])) for path in after
                      if before.get(path) != after[path] and path != quiet['file']}
    return pairs


def certify(case, scratch):
    """A perfect reviewer of the top proposals at stage 0: accept exactly the pairs some stage breaks."""
    scratch = Path(scratch)
    start = tree(case, 0, scratch / 'start')
    subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
    wanted = breaking_pairs(case, scratch / 'pairs')
    entries = []
    for proposal in propose(start, limit=PROPOSALS, seconds=120)['proposals']:
        if frozenset(proposal['files']) in wanted:
            entries.append({**proposal['entry'],
                            'description': f"These files keep the same rule (they share {', '.join(proposal['shared'][:3])}).",
                            'checks': [{'kind': 'test_suite', 'command': f"python -m pytest {case['test_dir']} -q"}]})
    return entries


def outcome(case, stage, before, after):
    previous = oracles.groups(case, stage - 1, before)
    current = oracles.groups(case, stage, after)
    lost = oracles.regressions(case, stage, previous, current)
    fails = {name for quiet in case['stages'][stage - 1].get('quiet') or [] for name in quiet.get('fails', [])}
    return {'lost': lost, 'dependent_lost': bool(set(lost) & fails), 'groups': current}


def workspace(case, stage, arm, folder, entries):
    """The reference tree before `stage`, set up as the v3 ElevenPowers arm; `rules` adds the declarations."""
    if arm not in ARMS:
        raise ValueError(f'unknown arm {arm}')
    folder = Path(folder)
    work = tree(case, stage - 1, folder / 'work')
    _write(work / '.claude' / 'settings.json', PROJECT_SETTINGS)
    _interpreter(sys.executable, folder)
    save(work, Config(profile='guide', commands={'tests': f"python -m pytest {case['test_dir']} -q"}))
    install('claude', work, sys.executable, TOOL_ROOT)
    if arm == 'rules':
        _write(work / 'elevenpowers.milestones.json', {'schema': 1, 'milestones': entries})
    _seed_git(work)
    return work
