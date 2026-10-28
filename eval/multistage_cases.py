"""Multi-stage v2 cases: one directory each, checked against the design's rules.

A case is a start tree, one reference diff per stage applied in order, a
dependent-missed diff for every cross-cutting stage, hidden group tests and a
cumulative table of documented facts. See
docs/superpowers/specs/2026-10-23-multistage-field-claims-design.md.
"""
import json
from pathlib import Path
import re
import shutil
import tempfile

from .bundle import apply_patch

# v3 cases declare their quiet dependents: ones neither a search for the changed names nor the
# public suite reveals (docs/superpowers/specs/2026-10-28-multistage-v3-harder-cases-design.md).
PROFILES = {
    'v2': {'stages': 6, 'cross_cutting': 4, 'self_contained': 1, 'bugfix': 0, 'quiet': False},
    'v3': {'stages': 8, 'cross_cutting': 5, 'self_contained': 1, 'bugfix': 1, 'quiet': True},
}
KINDS = ('key', 'data', 'copy', 'contract')
# Requests are written as a user writes them; the rule in CLAUDE.md has to do the rest.
FORBIDDEN = ('doc', 'docs', 'documentation', 'reference.md', 'changelog', 'test', 'tests', 'claude.md')
VARIANTS = ('reference', 'dependent-missed', 'quiet', 'docs-forgotten', 'no-op')


def _refuse(case_id, message):
    raise ValueError(f'{case_id}: {message}')


def load(root):
    root = Path(root)
    case = json.loads((root / 'case.json').read_text(encoding='utf-8'))
    name = case['id']
    stages, groups = case['stages'], case['groups']
    if case.get('profile', 'v2') not in PROFILES:
        _refuse(name, f"unknown profile {case['profile']}")
    profile = PROFILES[case.get('profile', 'v2')]
    count = profile['stages']
    if len(stages) != count:
        _refuse(name, f'{len(stages)} stages, not {count}')
    kinds = [stage['kind'] for stage in stages]
    if kinds.count('cross-cutting') < profile['cross_cutting']:
        _refuse(name, f'too few cross-cutting stages in {kinds}')
    if kinds.count('self-contained') < profile['self_contained']:
        _refuse(name, f'too few self-contained stages in {kinds}')
    if sum(bool(stage['bugfix']) for stage in stages) < profile['bugfix']:
        _refuse(name, 'no bug fix stage')
    for n, stage in enumerate(stages, 1):
        for word in FORBIDDEN:
            if re.search(rf'(?<![\w.]){re.escape(word)}(?![\w.])', stage['request'].lower()):
                _refuse(name, f'stage {n} request mentions {word!r}')
    window = {}
    for group in groups:
        if not (root / 'oracle' / 'groups' / f"{group['id']}.py").is_file():
            _refuse(name, f"group {group['id']} has no file")
        if not 0 <= group['since'] <= group['until'] <= count or group['id'] in window:
            _refuse(name, f"group {group['id']} window or identity")
        window[group['id']] = (group['since'], group['until'])
    introduced = [sum(since == n for since, _ in window.values()) for n in range(count + 1)]
    if introduced != [2] * (count + 1):
        _refuse(name, f'groups introduced per stage {introduced}, not two each')

    def earlier(n, failing, what):
        for group in failing:
            since, until = window.get(group, (count + 1, -1))
            if not since < n <= until:
                _refuse(name, f'stage {n} {what} group {group} is not an earlier group still required')

    for n, stage in enumerate(stages, 1):
        if stage['kind'] != 'cross-cutting':
            continue
        if profile['quiet']:
            if not stage.get('quiet'):
                _refuse(name, f'cross-cutting stage {n} has no quiet dependent')
            for entry in stage['quiet']:
                if entry['kind'] not in KINDS:
                    _refuse(name, f"stage {n} quiet dependent kind {entry['kind']!r} is not one of {KINDS}")
                if not (root / 'stages' / str(n) / entry['diff']).is_file():
                    _refuse(name, f"stage {n} quiet dependent diff {entry['diff']} is missing")
                if not entry['fails']:
                    _refuse(name, f'stage {n} quiet dependent has no fails')
                earlier(n, entry['fails'], 'quiet dependent fails')
            continue
        if not (root / 'stages' / str(n) / 'dependent-missed.diff').is_file() or not stage['dependent_missed_fails']:
            _refuse(name, f'cross-cutting stage {n} has no dependent-missed variant')
        earlier(n, stage['dependent_missed_fails'], 'dependent-missed')
    used = {entry['kind'] for stage in stages for entry in stage.get('quiet', [])}
    if profile['quiet'] and len(used) < 2:
        _refuse(name, f'quiet dependents use {len(used)} kinds; at least two kinds are required')
    facts = json.loads((root / 'oracle' / 'facts.json').read_text(encoding='utf-8'))
    if sorted(facts, key=int) != [str(n) for n in range(count + 1)]:
        _refuse(name, f'facts must cover stages 0 to {count}')
    for n in range(1, count + 1):
        if facts[str(n)] == facts[str(n - 1)]:
            _refuse(name, f'stage {n} changes no documented fact')
        if not (root / 'stages' / str(n) / 'reference.diff').is_file():
            _refuse(name, f'stage {n} has no reference diff')
    return {**case, 'profile': case.get('profile', 'v2'), 'root': str(root),
            'facts': {int(n): value for n, value in facts.items()}}


def _apply(root, diff):
    trouble = apply_patch(root, diff.read_bytes().decode('utf-8'))
    if trouble:
        raise ValueError(f'{diff} does not apply: {trouble}')


def tree(case, stage, folder, variant='reference', which=0):
    """The project as the reference left it at `stage`, or one of the broken variants.

    `quiet` leaves behind the stage's quiet dependent number `which`.
    """
    if variant not in VARIANTS:
        raise ValueError(f'unknown variant {variant}')
    root, folder = Path(case['root']), Path(folder)
    if variant == 'no-op':
        return tree(case, stage - 1, folder)
    if variant in ('dependent-missed', 'quiet') and case['stages'][stage - 1]['kind'] != 'cross-cutting':
        raise ValueError(f'stage {stage} is not cross-cutting')
    shutil.copytree(root / 'start', folder)
    for n in range(1, stage + 1):
        _apply(folder, root / 'stages' / str(n) / 'reference.diff')
    if variant == 'dependent-missed':
        _apply(folder, root / 'stages' / str(stage) / 'dependent-missed.diff')
    if variant == 'quiet':
        _apply(folder, root / 'stages' / str(stage) / case['stages'][stage - 1]['quiet'][which]['diff'])
    if variant == 'docs-forgotten':
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
            earlier = tree(case, stage - 1, Path(scratch) / 'earlier') / case['docs']
            target = folder / case['docs']
            if earlier.exists():
                shutil.copyfile(earlier, target)
            else:
                target.unlink(missing_ok=True)
    return folder
