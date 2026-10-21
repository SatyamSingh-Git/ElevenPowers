"""Choose held-out repositories from a public ranking by a rule fixed before mining.

The ranking is someone else's (most-downloaded PyPI packages), so the choice of
library is not ours. A package is kept when its source is on GitHub, it is pure
Python, its licence is permissive, and it is not one of the libraries this
project was tuned on. Every rejected package keeps its reason.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

PERMISSIVE = {'MIT', 'BSD-2-CLAUSE', 'BSD-3-CLAUSE', 'APACHE-2.0', 'ISC', 'PSF-2.0', 'PYTHON-2.0', '0BSD'}
CLASSIFIERS = ('MIT License', 'BSD License', 'Apache Software License', 'ISC License',
               'Python Software Foundation License')
GITHUB = re.compile(r'https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')
TUNED = {'click', 'attrs', 'jinja2', 'markupsafe', 'itsdangerous'}


def _repo(info):
    for url in (info.get('project_urls') or {}).values():
        match = GITHUB.match(url or '')
        # A Funding link (github.com/sponsors/<user>) has the same shape and names no repository.
        if match and match.group(1) != 'sponsors':
            owner, name = match.group(1), match.group(2).removesuffix('.git')
            return f'https://github.com/{owner}/{name}'
    return ''


def _permissive(info):
    expression = info.get('license_expression')
    if expression:
        # Every AND term must offer at least one permissive OR alternative.
        return all(any(choice.strip(' ()').upper() in PERMISSIVE for choice in re.split(r'\bOR\b', term))
                   for term in re.split(r'\bAND\b', expression))
    licences = [c for c in info.get('classifiers', []) if c.startswith('License ::')]
    if licences:
        # Classifiers cannot express AND; several of them list a dual licence's options.
        return any(c.endswith(CLASSIFIERS) for c in licences)
    return (info.get('license') or '').strip().upper() in PERMISSIVE


def _pure(files):
    return any(f.get('packagetype') == 'bdist_wheel' and f['filename'].endswith(('-py3-none-any.whl', '-py2.py3-none-any.whl'))
               for f in files)


def select(ranking, metadata, *, limit, exclude):
    rows = []
    for rank, row in enumerate(ranking['rows'][:limit], 1):
        project = row['project']
        value = {'project': project, 'rank': rank, 'repo': '', 'verdict': 'rejected'}
        if project.lower() in exclude:
            value['reason'] = 'excluded'
        elif not (found := metadata(project)):
            value['reason'] = 'metadata unavailable'
        elif not (repo := _repo(found['info'])):
            value['reason'] = 'no GitHub source'
        elif not _pure(found['urls']):
            value.update(repo=repo, reason='not pure Python')
        elif not _permissive(found['info']):
            value.update(repo=repo, reason='licence not permissive')
        else:
            value.update(repo=repo, verdict='accepted', reason='kept')
        rows.append(value)
    return rows


def _locked_names():
    names = set()
    for lock in Path(__file__).resolve().parent.glob('corpus*.lock'):
        for line in lock.read_text(encoding='utf8').splitlines():
            match = GITHUB.search(line)
            if match:
                names.add(match.group(2).removesuffix('.git').lower())
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ranking', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=400)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raw = args.ranking.read_bytes()
    hashes = {}

    def fetch(project):
        try:
            with urllib.request.urlopen(f'https://pypi.org/pypi/{project}/json', timeout=30) as response:
                body = response.read()
        except (urllib.error.URLError, TimeoutError):
            return None
        hashes[project] = hashlib.sha256(body).hexdigest()
        return json.loads(body)

    rows = select(json.loads(raw), fetch, limit=args.limit, exclude=TUNED | _locked_names())
    for row in rows:
        row['metadata_sha256'] = hashes.get(row['project'], '')
    value = {'schema': 1, 'ranking_sha256': hashlib.sha256(raw).hexdigest(), 'limit': args.limit,
             'excluded': sorted(TUNED | _locked_names()), 'rows': rows,
             'accepted': sum(r['verdict'] == 'accepted' for r in rows)}
    args.out.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    print(value['accepted'], 'accepted of', len(rows))


if __name__ == '__main__':
    main()
