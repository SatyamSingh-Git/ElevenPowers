"""Sample held-out tasks from accepted repositories by the frozen rule.

Repositories are taken in the public ranking's order. Within one, commits after
the cutoff are taken in sha256(seed, repository, sha) order and validated until
`cap` are kept or none remain; sampling stops at `want`. Every rejected
candidate and every unusable repository is retained with its reason.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from .heldout_env import build
from .mine import GIT, candidates, validate


def order(items, seed):
    return sorted(items, key=lambda item: hashlib.sha256(f'{seed}\0{item[0]}\0{item[1]}'.encode()).hexdigest())


def sample(repositories, candidates_for, check, *, seed, want, cap, progress=None):
    kept, rejections = [], []
    for repo in repositories:
        if len(kept) >= want:
            break
        shas = candidates_for(repo)
        if shas is None:
            rejections.append({'repo': repo, 'sha': '', 'reason': 'repository unusable'})
            if progress:
                progress(kept, rejections)
            continue
        taken = 0
        for _, sha in order([(repo, sha) for sha in shas], seed):
            if taken >= cap or len(kept) >= want:
                break
            instance, reason = check(repo, sha)
            if instance is None:
                rejections.append({'repo': repo, 'sha': sha, 'reason': reason})
                continue
            kept.append(instance)
            taken += 1
        if progress:
            progress(kept, rejections)
    return kept, rejections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repos', type=Path, required=True, help='results/heldout/repos.json')
    parser.add_argument('--work', type=Path, required=True, help='clones and environments, outside any Git ancestor')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--since', default='2026-06-01')
    parser.add_argument('--seed', default='heldout-2026-10-20')
    parser.add_argument('--want', type=int, default=40)
    parser.add_argument('--cap', type=int, default=4)
    parser.add_argument('--limit', type=int, default=400, help='commits scanned per repository')
    args = parser.parse_args()
    rows = [r for r in json.loads(args.repos.read_text(encoding='utf8'))['rows'] if r['verdict'] == 'accepted']
    environments, repos = {}, {}

    def candidates_for(url):
        name = url.rstrip('/').split('/')[-1]
        clone = args.work / 'repos' / name
        if not clone.exists():
            done = subprocess.run([*GIT, 'clone', '-q', '--filter=blob:none', url, str(clone)], capture_output=True, timeout=900)
            if done.returncode:
                return None
        environment = build(clone, args.work / 'venvs' / name)
        environments[url] = {k: environment.get(k) for k in ('state', 'reason', 'import_names', 'source_dir',
                                                              'test_dir', 'pythonpath', 'distribution', 'plan')}
        if environment['state'] != 'ready':
            return None
        environment['clone'] = clone
        repos[url] = environment
        return [sha for sha, _ in candidates(clone, args.limit, environment['source_dir'], environment['test_dir'],
                                             since=args.since)]

    def check(url, sha):
        environment = repos[url]
        tests = dict(candidates(environment['clone'], args.limit, environment['source_dir'], environment['test_dir'],
                                since=args.since))[sha]
        with tempfile.TemporaryDirectory() as work:
            instance, reason = validate(environment['clone'], sha, tests, {'PYTHONPATH': environment['pythonpath']},
                                        Path(work), python=environment['python'],
                                        suite_dir=environment['test_dir'].rstrip('/'))
        if instance is None:
            return None, reason
        return {**vars(instance), 'python': environment['python'], 'import_names': environment['import_names'],
                'pythonpath': environment['pythonpath'], 'url': url}, reason

    def write(kept, rejections):
        value = {'schema': 1, 'since': args.since, 'seed': args.seed, 'want': args.want, 'cap': args.cap,
                 'tasks': kept, 'rejections': rejections, 'environments': environments}
        args.out.write_text(json.dumps(value, indent=2, default=str) + '\n', encoding='utf8')

    kept, rejections = sample([r['repo'] for r in rows], candidates_for, check,
                              seed=args.seed, want=args.want, cap=args.cap, progress=write)
    write(kept, rejections)
    print(len(kept), 'tasks;', len(rejections), 'rejections;', len(environments), 'repositories tried')


if __name__ == '__main__':
    main()
