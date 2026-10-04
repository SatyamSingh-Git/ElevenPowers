"""Opt-in bounded co-change sample; never a causal dependency extractor."""
import re
import subprocess
import time

from .. import process

OUTPUT_BYTES = 2 * 1024 * 1024


def collect(graph, root, count, deadline):
    consumed = 0

    def git(*args):
        nonlocal consumed
        remaining = min(10, deadline - time.monotonic())
        if remaining <= 0:
            raise ValueError('history deadline reached')
        result = process.run(['git', '--no-pager', '-c', f'safe.directory={root.as_posix()}',
                              '-c', 'core.fsmonitor=false', *args], cwd=root,
                             timeout=remaining, shell=False)
        consumed += len(result.stdout.encode('utf-8')) + len(result.stderr.encode('utf-8'))
        if consumed > OUTPUT_BYTES:
            raise ValueError('history accepted-output limit 2 MiB exceeded')
        if result.returncode:
            raise ValueError('history Git read unavailable')
        return result.stdout

    try:
        commits = git('rev-list', f'--max-count={count + 1}', 'HEAD', '--', '.').splitlines()
        if len(commits) > count:
            graph.issues.append(f'history truncated to {count} recent commits')
        for commit in commits[:count]:
            if not re.fullmatch(r'[a-f0-9]{40,64}', commit):
                raise ValueError('history commit identity invalid')
            # Relative names match the selected project scope, including a subdir.
            paths = git('diff-tree', '--root', '--no-commit-id', '--name-only', '-z',
                        '--relative', '-r', commit, '--', '.').split('\0')
            selected = sorted({'file:' + p for p in paths if 'file:' + p in graph.nodes})
            if len(selected) > 40:
                graph.issues.append(f'history commit {commit[:12]} exceeds 40 selected files; omitted')
                continue
            for i, source in enumerate(selected):
                for target in selected[i + 1:]:
                    if len(graph.associations) >= 10000:
                        raise ValueError('history association limit 10000 reached')
                    graph.associations.append({'source': source, 'target': target, 'commit': commit})
        graph.coverage['history_commits'] = min(len(commits), count)
    except (OSError, ValueError, subprocess.SubprocessError):
        graph.issues.append('history incomplete: Git unavailable, deadline or output/association limit reached')
    graph.coverage['history_output_bytes'] = consumed
