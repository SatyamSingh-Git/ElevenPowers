"""The reviewer study (PLAN 13 A.3): prompt, answer reading, grading and analysis.

Fixed before any model call, as docs/superpowers/specs/2026-11-01-reviewer-benefit-design.md
pre-registers it. Arm `diff` sees the task and the diff; arm `report` also sees
ep_review's report. For a C seed, `caught` is a false alarm.
"""
import json
import re

from .vacuity_power import _sign_test

ARMS = ('diff', 'report')
DECISIONS = ('accept', 'request_changes')
SHAPE = {'decision': 'accept | request_changes',
         'problems': [{'file': 'path', 'line': 0, 'kind': 'missing_test | wrong_behaviour | other',
                       'description': 'what is wrong'}]}
DIFF_PREFIX = re.compile(r'^(?:[ab]/|\./)+')


def prompt(request, diff, report=None):
    parts = ['You are reviewing a change a coding agent made to a Python project, to decide whether to accept it.',
             'The task the agent was given:', request, 'The change, as a git diff:', diff]
    if report:
        parts += ["ep_review's report on this change, from running the project's tests:", report]
    parts.append('Answer with one JSON object and nothing else, shaped like ' + json.dumps(SHAPE)
                 + '. List every problem you would raise before accepting; use an empty list if there are none.')
    return '\n\n'.join(parts)


def answer(text):
    """The reply's JSON object, or None when it holds no well-formed answer."""
    try:
        value = json.loads(text[text.find('{'):text.rfind('}') + 1])
    except ValueError:
        return None
    if not isinstance(value, dict) or value.get('decision') not in DECISIONS or not isinstance(value.get('problems'), list):
        return None
    return value


def _names(reported, path):
    reported = DIFF_PREFIX.sub('', str(reported).replace('\\', '/'))
    return reported == path or path.endswith('/' + reported)


def grade(seed, reply):
    if reply is None:
        return None
    problems = [p for p in reply['problems'] if isinstance(p, dict)]
    if seed['kind'] == 'W':
        return any(_names(p.get('file', ''), seed['path']) and type(p.get('line')) is int
                   and seed['line'] - 2 <= p['line'] <= seed['end_line'] + 2 for p in problems)
    if seed['kind'] == 'U':
        return reply['decision'] == 'request_changes' and any(p.get('kind') == 'missing_test' for p in problems)
    return reply['decision'] == 'request_changes'


def analyse(rows):
    result = {}
    for kind in ('C', 'U', 'W'):
        by_seed = {}
        for row in rows:
            if row['kind'] == kind and row['caught'] is not None:
                by_seed.setdefault(row['seed'], {})[row['arm']] = row['caught']
        pairs = [arms for arms in by_seed.values() if len(arms) == 2]
        report_only = sum(arms['report'] and not arms['diff'] for arms in pairs)
        diff_only = sum(arms['diff'] and not arms['report'] for arms in pairs)
        result[kind] = {'caught': {arm: sum(arms[arm] for arms in pairs) for arm in ARMS}, 'pairs': len(pairs),
                        'unpaired': len(by_seed) - len(pairs), 'report_only': report_only, 'diff_only': diff_only,
                        'p': _sign_test(report_only, diff_only)}
    return result
