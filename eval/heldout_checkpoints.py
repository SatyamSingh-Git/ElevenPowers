"""Did a held-out run pass through a better state than the one it submitted?

PLAN §7's B2.3 asked this of the saved bundles and could not answer it: the
recorder held a candidate only at each proposed stop, and §1.2 predicts the
effect lives at edit granularity. The held-out sweep kept every run's host
transcript, which records each Edit and Write in full, so the tree after every
edit can be rebuilt from the base commit. A replay counts only when its last
state is byte-identical to the patch the run submitted; a run that also changed
files through the shell is reported as not replayable rather than graded from a
guess.

Each earlier state is graded as the sweep graded the final one: the upstream
tests in a fresh tree, then the revert probe when it resolves. Better means
resolved and not VACUOUS where the submitted patch was not, or resolved where it
was not.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import tempfile

from .bundle import apply_patch, export_patch
from .heldout_run import load_task
from .heldout_vacuity import vacuity
from .live import _seed_git, base_tree, grade_patch
from .preservation import _read, _write


def edits(transcript):
    """Successful Edit and Write calls on files inside the run's workspace, in order."""
    work, uses, failed = None, [], set()
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') == 'system' and event.get('subtype') == 'init':
            work = PureWindowsPath(event['cwd'])
        content = event.get('message', {}).get('content') if isinstance(event.get('message'), dict) else None
        for item in content if isinstance(content, list) else []:
            if item.get('type') == 'tool_use' and item.get('name') in ('Edit', 'Write'):
                uses.append(item)
            elif item.get('type') == 'tool_result' and item.get('is_error'):
                failed.add(item.get('tool_use_id'))
    kept = []
    for use in uses:
        target = PureWindowsPath(use['input']['file_path'])
        if use['id'] in failed or work is None or not target.is_relative_to(work):
            continue
        kept.append((target.relative_to(work).as_posix(), use))
    return kept


def change(root, path, step):
    target = Path(root) / path
    data = step['input']
    if step['name'] == 'Write':
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data['content'].encode('utf-8'))
        return
    text = target.read_bytes().decode('utf-8')
    old, new = data['old_string'], data['new_string']
    # The host matches an edit against a CRLF file with LF text and writes CRLF back.
    if old not in text and '\r\n' in text:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    if old not in text:
        raise ValueError(f'{path}: the recorded edit does not match the replayed file')
    target.write_bytes(text.replace(old, new, -1 if data.get('replace_all') else 1).encode('utf-8'))


def _rank(state):
    outcome, vacuous = state
    return 0 if outcome != 'resolved' else 1 if vacuous else 2


def better(states, final):
    return max(map(_rank, states), default=0) > _rank(final)


def replay(task, transcript, folder):
    """The distinct patches the workspace held after each edit, the submitted one last."""
    base_tree(task, folder)
    _seed_git(folder)
    patches = []
    for path, step in edits(transcript):
        change(folder, path, step)
        patch = export_patch(folder)
        if not patches or patch != patches[-1]:
            patches.append(patch)
    return patches


def touched(patch):
    return set(re.findall(r'^diff --git a/\S+ b/(\S+)$', patch, re.M))


def same_files(one, other, paths):
    def body(root, path):
        target = Path(root) / path
        return target.read_bytes().replace(b'\r\n', b'\n') if target.exists() else None
    return all(body(one, path) == body(other, path) for path in paths)


def match(task, replayed, patches, submitted, folder):
    """'exact', 'line endings', or None when the replay is not the run that was graded.

    A `git stash` and `stash pop` under core.autocrlf rewrites whole files with
    CRLF, so a run can submit the replayed content with different line endings.
    """
    if not patches:
        return None
    if patches[-1] == submitted:
        return 'exact'
    base_tree(task, folder)
    _seed_git(folder)
    if apply_patch(folder, submitted):
        return None
    return 'line endings' if same_files(replayed, folder, touched(patches[-1]) | touched(submitted)) else None


def grade(task, patch, scratch):
    scratch.mkdir(parents=True, exist_ok=True)
    graded = grade_patch(task, patch, scratch / 'court')
    if not graded.resolved:
        return graded.outcome, None
    base_tree(task, scratch / 'base')
    value = vacuity(scratch / 'base', patch, python=task.source['python'], env=task.source.get('env') or {},
                    test_dir=task.source['test_dir'], work=scratch / 'vacuity')
    return graded.outcome, value['vacuous']


def measure(sweep, corpus, out):
    data = corpus.read_bytes()
    if hashlib.sha256(data).hexdigest() != _read(sweep / 'protocol.json')['corpus_sha256']:
        raise ValueError(f'{corpus} is not the corpus {sweep} was sealed with')
    corpus = json.loads(data)
    journal = json.loads(out.read_bytes()) if out.exists() else {}
    for result in sorted((sweep / 'runs').glob('*/result.json')):
        record = _read(result)
        if record['state'] != 'graded' or record['slot'] in journal:
            continue
        task = load_task(corpus, record['task'])
        transcript = (result.parent / 'native.jsonl').read_text(encoding='utf-8')
        submitted = (result.parent / 'patch.diff').read_bytes().decode('utf-8')
        entry = {'arm': record['arm'], 'final': [record['outcome'], record['vacuous']], 'states': []}
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
            replayed = Path(scratch) / 'replay'
            try:
                patches = replay(task, transcript, replayed)
            except (ValueError, OSError) as error:
                patches, entry['reason'] = [], str(error)
            entry['faithful'] = match(task, replayed, patches, submitted, Path(scratch) / 'submitted')
            if entry['faithful']:
                for n, patch in enumerate(patches[:-1]):
                    entry['states'].append(list(grade(task, patch, Path(scratch) / f'state-{n}')))
        journal[record['slot']] = entry
        _write(out, journal)
        print(record['slot'], entry['faithful'], entry['states'], entry['final'], flush=True)
    return journal


def summary(journal):
    lines = []
    for arm in ('ordinary', 'assisted'):
        runs = [e for e in journal.values() if e['arm'] == arm]
        faithful = [e for e in runs if e['faithful']]
        earlier = [e for e in faithful if e['states']]
        found = [e for e in earlier if better(e['states'], tuple(e['final']))]
        moved = Counter(f"{_rank(max(e['states'], key=_rank))}->{_rank(tuple(e['final']))}" for e in found)
        fixed_first = sum(1 for e in earlier if _rank(tuple(e['final'])) == 2 and any(_rank(s) == 1 for s in e['states']))
        endings = sum(1 for e in faithful if e['faithful'] == 'line endings')
        lines.append(f'{arm}: {len(runs)} graded runs, {len(faithful)} replayed ({endings} up to line endings), '
                     f'{len(earlier)} with an '
                     f'earlier distinct state; a better earlier state in {len(found)} '
                     f'(best earlier -> submitted, 0 failing, 1 resolved VACUOUS, 2 resolved and pinned: '
                     f'{dict(moved)}); {fixed_first} pinned runs passed through a resolved VACUOUS state first')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sweep', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='journal; an existing one is resumed')
    args = parser.parse_args()
    print(summary(measure(args.sweep, args.corpus, args.out)))


if __name__ == '__main__':
    main()
