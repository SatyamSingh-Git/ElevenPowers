"""Sample held-out tasks from accepted repositories by the frozen rule.

Repositories are taken in the public ranking's order, each once however many
packages it publishes. Within one, commits between the cutoffs are taken in
sha256(seed, repository, sha) order and validated until `cap` are kept or none
remain; sampling stops at `want`. Every rejected candidate and every unusable
repository is retained with its reason.

The journal is rewritten atomically after each repository and a rerun resumes
from it. A repository that contributed no task is deleted once done, and the
run stops before the next repository when free space falls below the floor:
on 2026-10-20 a run filled the disk and its journal was truncated to nothing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

from .heldout_env import build
from .mine import GIT, candidates, validate
from .preservation import _write


class LowDisk(Exception):
    pass


def order(items, seed):
    return sorted(items, key=lambda item: hashlib.sha256(f'{seed}\0{item[0]}\0{item[1]}'.encode()).hexdigest())


def sample(repositories, candidates_for, check, *, seed, want, cap, progress=None, resume=None, room=None):
    resume = resume or {}
    kept, rejections = list(resume.get('tasks', [])), list(resume.get('rejections', []))
    processed = list(resume.get('processed', []))
    for repo in repositories:
        if len(kept) >= want:
            break
        if repo in processed:
            continue
        if room and not room():
            raise LowDisk(f'free space below the floor before {repo}')
        _take(repo, candidates_for, check, seed=seed, want=want, cap=cap, kept=kept, rejections=rejections, room=room)
        processed.append(repo)
        if progress:
            progress(kept, rejections, processed)
    return kept, rejections


def _take(repo, candidates_for, check, *, seed, want, cap, kept, rejections, room=None):
    def reject(sha, reason):
        # A clone, install or suite that failed for want of disk says nothing about the repository.
        if room and not room():
            raise LowDisk(f'free space fell below the floor while preparing {repo}')
        rejections.append({'repo': repo, 'sha': sha, 'reason': reason})

    try:
        shas = candidates_for(repo)
    except subprocess.TimeoutExpired:
        reject('', 'repository preparation timed out')
        return
    if shas is None:
        reject('', 'repository unusable')
        return
    taken = 0
    for _, sha in order([(repo, sha) for sha in shas], seed):
        if taken >= cap or len(kept) >= want:
            break
        try:
            instance, reason = check(repo, sha)
        except subprocess.TimeoutExpired:
            # The full suite is run for every candidate; one that cannot finish once never will.
            reject(sha, 'suite exceeded the mining timeout; repository skipped')
            return
        if instance is None:
            reject(sha, reason)
            continue
        kept.append(instance)
        taken += 1


def resumed(path, rule):
    """The journal to continue from, or None; a journal from other rule values is refused."""
    if not path.exists():
        return None
    journal = json.loads(path.read_text(encoding='utf8'))
    if any(journal.get(key) != value for key, value in rule.items()):
        raise ValueError(f'{path} was written under different rule values; refusing to splice two samples')
    return journal


def _name(url):
    return url.rstrip('/').split('/')[-1]


def _writable(function, path, _):
    # Git writes its object files read-only, and Windows will not delete them as they are.
    os.chmod(path, stat.S_IWRITE)
    function(path)


def prune(work, processed, kept):
    keep = {_name(task['url']) for task in kept}
    removed = []
    for name in dict.fromkeys(_name(url) for url in processed):
        paths = [Path(work) / kind / name for kind in ('repos', 'venvs')]
        if name in keep or not any(path.exists() for path in paths):
            continue
        try:
            for path in paths:
                if path.exists():
                    shutil.rmtree(path, onexc=_writable)
        except OSError as error:
            # A file a just-exited test process still holds; every journal retries.
            print(f'prune deferred for {name}: {error}', file=sys.stderr)
            continue
        removed.append(name)
    return removed


def clone(url, into):
    partial = into.with_name(into.name + '.partial')
    if partial.exists():
        shutil.rmtree(partial, onexc=_writable)
    into.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run([*GIT, 'clone', '-q', '--filter=blob:none', url, str(partial)], capture_output=True, timeout=900)
    if done.returncode:
        if partial.exists():
            shutil.rmtree(partial, onexc=_writable)
        return False
    partial.rename(into)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repos', type=Path, required=True, help='results/heldout/repos.json')
    parser.add_argument('--work', type=Path, required=True, help='clones and environments, outside any Git ancestor')
    parser.add_argument('--out', type=Path, required=True, help='the journal; an existing one is resumed')
    parser.add_argument('--since', default='2026-06-01')
    parser.add_argument('--until', default='2026-10-20T00:00:00+00:00')
    parser.add_argument('--seed', default='heldout-2026-10-20')
    parser.add_argument('--want', type=int, default=40)
    parser.add_argument('--cap', type=int, default=4)
    parser.add_argument('--limit', type=int, default=400, help='commits scanned per repository')
    parser.add_argument('--min-free-gb', type=float, default=2)
    args = parser.parse_args()
    rule = {'seed': args.seed, 'since': args.since, 'until': args.until, 'want': args.want, 'cap': args.cap,
            'limit': args.limit}
    rows = [r for r in json.loads(args.repos.read_text(encoding='utf8'))['rows'] if r['verdict'] == 'accepted']
    journal = resumed(args.out, rule)
    environments = dict(journal['environments']) if journal else {}
    repos = {}

    def candidates_for(url):
        name = _name(url)
        checkout = args.work / 'repos' / name
        if not checkout.exists() and not clone(url, checkout):
            return None
        environment = build(checkout, args.work / 'venvs' / name)
        head = subprocess.run([*GIT, '-C', str(checkout), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        environments[url] = {k: environment.get(k) for k in ('state', 'reason', 'import_names', 'source_dir',
                                                              'test_dir', 'pythonpath', 'distribution', 'plan')}
        environments[url]['head'] = head.stdout.strip()
        if environment['state'] != 'ready':
            return None
        environment['clone'] = checkout
        repos[url] = environment
        return [sha for sha, _ in candidates(checkout, args.limit, environment['source_dir'], environment['test_dir'],
                                             since=args.since, until=args.until)]

    def check(url, sha):
        environment = repos[url]
        tests = dict(candidates(environment['clone'], args.limit, environment['source_dir'], environment['test_dir'],
                                since=args.since, until=args.until))[sha]
        # As in eval.mine: Windows holds handles a moment after pytest exits, and a
        # strict cleanup ended the 2026-10-22 run on a temporary file.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as work:
            instance, reason = validate(environment['clone'], sha, tests, {'PYTHONPATH': environment['pythonpath']},
                                        Path(work), python=environment['python'],
                                        suite_dir=environment['test_dir'].rstrip('/'))
        if instance is None:
            return None, reason
        return {**vars(instance), 'python': environment['python'], 'import_names': environment['import_names'],
                'pythonpath': environment['pythonpath'], 'url': url}, reason

    state = {'tasks': [], 'rejections': [], 'processed': []}

    def write(kept, rejections, processed):
        state.update(tasks=kept, rejections=rejections, processed=processed)
        _write(args.out, {'schema': 2, **rule, **state, 'environments': environments})
        prune(args.work, processed, kept)

    def room():
        return shutil.disk_usage(args.work).free >= args.min_free_gb * 2 ** 30

    args.work.mkdir(parents=True, exist_ok=True)
    try:
        kept, rejections = sample(list(dict.fromkeys(r['repo'] for r in rows)), candidates_for, check,
                                  seed=args.seed, want=args.want, cap=args.cap, progress=write, resume=journal,
                                  room=room)
    except LowDisk as error:
        if journal and not state['processed']:
            state.update(tasks=journal['tasks'], rejections=journal['rejections'], processed=journal['processed'])
        _write(args.out, {'schema': 2, **rule, **state, 'environments': environments, 'stopped': str(error)})
        print('stopped:', error, '- free space and rerun the same command to resume')
        sys.exit(1)
    print(len(kept), 'tasks;', len(rejections), 'rejections;', len(environments), 'repositories tried')


if __name__ == '__main__':
    main()
