"""Quiet dependents from real history: per project, the newest commits modifying 2 to 5 non-test Python
files, and in each the modified files that mention none of the names the rest of the commit changes.
No coverage is computed here. Run: python build.py <folder holding the four clones>"""
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from core.surface import TEST_NAME  # noqa: E402
from eval.multistage_quiet import changed_names, named  # noqa: E402

PROJECTS = {'click': '2247b35ea1c47c727d7a06e51fa280e12a863ff6',
            'attrs': '9d9f94a043de7fc4012459853a4ed597a5577855',
            'rich': '9d8f9a372cc5916fd4781fec207ced7ddac2f08f',
            'pytest': '08017d9ada4c72a7b6a78f7873c238070e24c982'}
WANTED, EXAMINED, SAMPLE = 40, 3000, 30


def git(repo, *args, binary=False):
    done = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True)
    return done.stdout if binary else done.stdout.decode('utf-8', errors='replace')


def source(path):
    return path.endswith('.py') and not TEST_NAME.search(path)


def commits(repo, head):
    """(sha, parent, modified non-test Python files) for every non-merge commit, newest first."""
    out = []
    for block in git(repo, 'log', '--no-merges', '--no-renames', '--name-status', '--format=%x01%H %P', head).split('\x01')[1:]:
        lines = block.strip().splitlines()
        shas = lines[0].split()
        modified = sorted(line.split('\t', 1)[1] for line in lines[1:]
                          if line.startswith('M\t') and source(line.split('\t', 1)[1]))
        out.append((shas[0], shas[1] if len(shas) > 1 else None, modified))
    return out


def quiet(repo, sha, parent, modified, scratch):
    diff = git(repo, 'diff', '--no-renames', parent, sha)
    before = Path(tempfile.mkdtemp(dir=scratch))
    for path in [p for p in git(repo, 'diff', '--no-renames', '--name-only', '--diff-filter=MD', parent, sha).splitlines()
                 if p.endswith('.py')]:
        (before / path).parent.mkdir(parents=True, exist_ok=True)
        (before / path).write_bytes(git(repo, 'show', f'{parent}:{path}', binary=True))
    return [d for d in modified if not named(changed_names(diff, before, d), before / d)]


def main():
    clones = Path(sys.argv[1]).resolve()
    scratch = Path(tempfile.mkdtemp(prefix='ep-history-'))
    cases, qualifying = [], {}
    for project, head in PROJECTS.items():
        repo = clones / project
        found, seen = 0, 0
        qualifying[project] = []
        for sha, parent, modified in commits(repo, head):
            if found >= WANTED or seen >= EXAMINED:
                break
            seen += 1
            if parent is None or not 2 <= len(modified) <= 5:
                continue
            qualifying[project].append({'commit': sha, 'modified': modified})
            for dependent in quiet(repo, sha, parent, modified, scratch):
                cases.append({'project': project, 'commit': sha, 'parent': parent, 'dependent': dependent,
                              'edit': [p for p in modified if p != dependent]})
                found += 1
        # The control needs the next older qualifying commit, past the last one sampled.
        for sha, parent, modified in commits(repo, head)[seen:]:
            if parent is not None and 2 <= len(modified) <= 5:
                qualifying[project].append({'commit': sha, 'modified': modified})
                break
        print(project, f'{seen} commits examined, {len(qualifying[project]) - 1} qualifying,',
              f'{found} quiet dependents in {len({c["commit"] for c in cases if c["project"] == project})} commits',
              flush=True)
    order = {project: [q['commit'] for q in rows] for project, rows in qualifying.items()}
    for case in cases:
        rows = qualifying[case['project']]
        after = rows[order[case['project']].index(case['commit']) + 1]
        case['control'] = [p for p in after['modified'] if p != case['dependent']]
        case['control_commit'] = after['commit']
    (HERE / 'benchmark.json').write_text(json.dumps(cases, indent=1), encoding='utf-8')
    drawn = random.Random(0).sample(range(len(cases)), SAMPLE)
    (HERE / 'sample.json').write_text(json.dumps(
        [{'id': i, **{k: cases[i][k] for k in ('project', 'commit', 'dependent', 'edit')}, 'sort': None}
         for i in sorted(drawn)], indent=1), encoding='utf-8')
    print(len(cases), 'quiet dependents in total')
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == '__main__':
    main()
