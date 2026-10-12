"""Read-only GitHub evidence presentation; successful export is informational."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.patchproof.github import build
from core.patchproof.github_context import read_event, artifact_link
from core.patchproof.github_output import publish
from core.redact import scrub

MAX_RUNNER_BYTES = 1024 * 1024


def runner_files(project, *, link=False):
    paths = {}
    names = ['GITHUB_STEP_SUMMARY'] if link else ['GITHUB_STEP_SUMMARY', 'GITHUB_OUTPUT']
    for name in names:
        raw = os.environ.get(name)
        if not raw:
            raise ValueError('required Actions runner file is unavailable')
        path = Path(raw).absolute()
        if path.resolve() != path or path.is_symlink() or not path.parent.is_dir():
            raise ValueError('linked or unavailable Actions runner file')
        if path == project or path.is_relative_to(project):
            raise ValueError('Actions runner file must be outside inspected project')
        if path.exists() and (not path.is_file() or path.stat().st_size > MAX_RUNNER_BYTES):
            raise ValueError('Actions runner file is not a bounded regular file')
        paths[name] = path
    if len(set(paths.values())) != len(paths):
        raise ValueError('Actions runner files must be distinct')
    return paths


def append(path, text):
    data = text.encode('utf-8')
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        state = os.fstat(descriptor)
        if not stat.S_ISREG(state.st_mode) or state.st_size+len(data) > MAX_RUNNER_BYTES:
            raise ValueError('Actions runner file byte/type limit exceeded')
        with os.fdopen(descriptor, 'ab', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(descriptor)
    finally:
        os.close(descriptor)


def outputs(paths):
    text = ''
    for key, value in paths.items():
        delimiter = 'ep_'+uuid.uuid4().hex
        text += f'{key}<<{delimiter}\n{value}\n{delimiter}\n'
    return text


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--repository', required=True)
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--event', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--impact', action='store_true')
    parser.add_argument('--actions', action='store_true')
    parser.add_argument('--link-artifact')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if args.link_artifact and (args.event or args.output_dir or args.impact):
        parser.error('artifact link mode does not collect or publish a new bundle')
    try:
        project = args.project.resolve(strict=True)
        targets = runner_files(project, link=bool(args.link_artifact)) if args.actions else {}
        if args.link_artifact:
            text = artifact_link(args.repository, args.run_id, args.link_artifact)
            text += '\n\nGitHub login and artifact retention apply. Upload is not independent attestation.\n'
            if args.actions:
                append(targets['GITHUB_STEP_SUMMARY'], text)
                print('Evidence download link attached (informational).')
            else:
                print(text, end='')
            return 0
        before = read_event(args.event) if args.event else None
        value = build(project, args.base, args.head, repository=args.repository,
                      event=before, timeout=args.timeout, impact=args.impact)
        if args.event and read_event(args.event) != before:
            raise ValueError('event file changed during evidence collection')
        paths = publish(value, args.output_dir, project=project)
        metadata = {key: str(value) for key, value in paths.items()}
        metadata.update(bundle_sha256=value['bundle_sha256'],
                        patch_id=value['subject']['patch_id'] or 'unavailable')
        if args.actions:
            append(targets['GITHUB_STEP_SUMMARY'], paths['summary'].read_text(encoding='utf-8'))
            append(targets['GITHUB_OUTPUT'], outputs(metadata))
        # JSON keeps filename newlines and workflow-like text off line starts.
        print(json.dumps(metadata, ensure_ascii=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as error:
        reason = scrub(str(error)).replace('\r', ' ').replace('\n', ' ')[:256]
        parser.exit(2, 'GitHub evidence unavailable: '+type(error).__name__+': '+reason+'\n')


if __name__ == '__main__':
    sys.exit(main())
