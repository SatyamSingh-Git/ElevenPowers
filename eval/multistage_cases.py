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

STAGES = 6
CROSS_CUTTING = 4
SELF_CONTAINED = 1
# Requests are written as a user writes them; the rule in CLAUDE.md has to do the rest.
FORBIDDEN = ('doc', 'docs', 'documentation', 'reference.md', 'changelog', 'test', 'tests', 'claude.md')
VARIANTS = ('reference', 'dependent-missed', 'docs-forgotten', 'no-op')


def _refuse(case_id, message):
    raise ValueError(f'{case_id}: {message}')


def load(root):
    root = Path(root)
    case = json.loads((root / 'case.json').read_text(encoding='utf-8'))
    name = case['id']
    stages, groups = case['stages'], case['groups']
    if len(stages) != STAGES:
        _refuse(name, f'{len(stages)} stages, not {STAGES}')
    kinds = [stage['kind'] for stage in stages]
    if kinds.count('cross-cutting') < CROSS_CUTTING or kinds.count('self-contained') < SELF_CONTAINED:
        _refuse(name, f'stage kinds {kinds}')
    for n, stage in enumerate(stages, 1):
        for word in FORBIDDEN:
            if re.search(rf'(?<![\w.]){re.escape(word)}(?![\w.])', stage['request'].lower()):
                _refuse(name, f'stage {n} request mentions {word!r}')
    window = {}
    for group in groups:
        if not (root / 'oracle' / 'groups' / f"{group['id']}.py").is_file():
            _refuse(name, f"group {group['id']} has no file")
        if not 0 <= group['since'] <= group['until'] <= STAGES or group['id'] in window:
            _refuse(name, f"group {group['id']} window or identity")
        window[group['id']] = (group['since'], group['until'])
    introduced = [sum(since == n for since, _ in window.values()) for n in range(STAGES + 1)]
    if introduced != [2] * (STAGES + 1):
        _refuse(name, f'groups introduced per stage {introduced}, not two each')
    for n, stage in enumerate(stages, 1):
        if stage['kind'] != 'cross-cutting':
            continue
        if not (root / 'stages' / str(n) / 'dependent-missed.diff').is_file() or not stage['dependent_missed_fails']:
            _refuse(name, f'cross-cutting stage {n} has no dependent-missed variant')
        for group in stage['dependent_missed_fails']:
            since, until = window.get(group, (STAGES + 1, -1))
            if not since < n <= until:
                _refuse(name, f'stage {n} dependent-missed group {group} is not an earlier group still required')
    facts = json.loads((root / 'oracle' / 'facts.json').read_text(encoding='utf-8'))
    if sorted(facts, key=int) != [str(n) for n in range(STAGES + 1)]:
        _refuse(name, 'facts must cover stages 0 to 6')
    for n in range(1, STAGES + 1):
        if facts[str(n)] == facts[str(n - 1)]:
            _refuse(name, f'stage {n} changes no documented fact')
        if not (root / 'stages' / str(n) / 'reference.diff').is_file():
            _refuse(name, f'stage {n} has no reference diff')
    return {**case, 'root': str(root), 'facts': {int(n): value for n, value in facts.items()}}


def _apply(root, diff):
    trouble = apply_patch(root, diff.read_bytes().decode('utf-8'))
    if trouble:
        raise ValueError(f'{diff} does not apply: {trouble}')


def tree(case, stage, folder, variant='reference'):
    """The project as the reference left it at `stage`, or one of the broken variants."""
    if variant not in VARIANTS:
        raise ValueError(f'unknown variant {variant}')
    root, folder = Path(case['root']), Path(folder)
    if variant == 'no-op':
        return tree(case, stage - 1, folder)
    if variant == 'dependent-missed' and case['stages'][stage - 1]['kind'] != 'cross-cutting':
        raise ValueError(f'stage {stage} is not cross-cutting')
    shutil.copytree(root / 'start', folder)
    for n in range(1, stage + 1):
        _apply(folder, root / 'stages' / str(n) / 'reference.diff')
    if variant == 'dependent-missed':
        _apply(folder, root / 'stages' / str(stage) / 'dependent-missed.diff')
    if variant == 'docs-forgotten':
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
            earlier = tree(case, stage - 1, Path(scratch) / 'earlier') / case['docs']
            target = folder / case['docs']
            if earlier.exists():
                shutil.copyfile(earlier, target)
            else:
                target.unlink(missing_ok=True)
    return folder
