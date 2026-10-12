"""Bounded witness of ignore inputs used by the existing Git source enumerator."""
import hashlib
import json
import os
from pathlib import Path
import time

from ..process import run
from .identity import GitRead


class PolicyError(ValueError):
    """Fixed, public diagnostic; never embeds a producer body or external path."""


def fingerprint(root, deadline):
    """Hash effective config and applicable rule files, never export their bodies."""
    git = GitRead(root, deadline)
    # Source enumeration inherits global/system configuration. Witness that same
    # environment; these commands inspect metadata only, with no source/helpers.
    git.env = dict(os.environ)
    git.env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0',
                   GIT_NO_LAZY_FETCH='1', GIT_ALLOW_PROTOCOL='')
    def read(*args, optional=False, status=False):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('repository policy inspection deadline reached')
        done = run([*git.command, *args], cwd=root, env=git.env,
                   timeout=remaining, shell=False, text=False)
        if done.stderr or (done.returncode and not (optional and done.returncode == 1)):
            raise PolicyError('Git repository policy inspection unavailable')
        return done.returncode if status else done.stdout

    values = {'configuration': hashlib.sha256(read('config', '--show-origin', '--null', '--list')).hexdigest()}
    total = 0
    def add(path):
        nonlocal total
        if time.monotonic() >= deadline:
            raise TimeoutError('repository policy file deadline reached')
        path = path.absolute()
        if path.is_symlink() or path.resolve() != path:
            raise PolicyError('linked repository policy input is unsupported')
        if not path.exists():
            values[str(path)] = None
            return
        if not path.is_file():
            raise PolicyError('repository policy input is not an ordinary file')
        with path.open('rb') as stream:
            data = stream.read(1024 * 1024 + 1)
        total += len(data)
        if len(data) > 1024 * 1024 or total > 8 * 1024 * 1024:
            raise PolicyError('repository policy byte budget exceeded')
        values[str(path)] = hashlib.sha256(data).hexdigest()

    add(Path(os.fsdecode(read('rev-parse', '--path-format=absolute', '--git-path', 'info/exclude').strip())))
    configured = read('config', '--null', '--path', '--get',
                      'core.excludesfile', optional=True).removesuffix(b'\0')
    if configured:
        path = Path(os.fsdecode(configured))
        add(path if path.is_absolute() else root / path)
    else:
        home = Path(os.environ.get('HOME') or Path.home())
        xdg = Path(os.environ.get('XDG_CONFIG_HOME') or home / '.config')
        add(xdg / 'git/ignore')

    # Git itself identifies wholly ignored directories. Their nested rules cannot
    # re-include children while that parent is ignored; do not traverse generated
    # trees. Ignored .gitignore *files* in active directories still participate.
    ignored = read('ls-files', '--others', '--ignored', '--exclude-standard', '--directory', '-z')
    directories = {os.fsdecode(p).rstrip('/') for p in ignored.split(b'\0') if p.endswith(b'/')}
    # --directory can also collapse a directory containing only ignored files;
    # that is not proof the parent itself is ignored. Ask Git before pruning.
    omitted = {rel for rel in sorted(directories) if read('check-ignore', '--no-index',
               '--quiet', '--', rel + '/', optional=True, status=True) == 0}
    visited = 0
    def failed(error):
        raise OSError('repository policy directory unreadable') from error
    for base, folders, names in os.walk(root, followlinks=False, onerror=failed):
        visited += 1
        if visited > 20000 or time.monotonic() >= deadline:
            raise PolicyError('repository policy directory/time budget exceeded')
        directory = Path(base)
        add(directory / '.gitignore')
        keep = []
        for name in sorted(folders):
            full = directory / name
            rel = full.relative_to(root).as_posix()
            if name in ('.git', '.elevenpowers') or rel in omitted or (full / '.git').exists():
                continue
            if full.is_symlink() or full.resolve() != full.absolute():
                raise PolicyError('linked repository policy directory is unsupported')
            keep.append(name)
        folders[:] = keep
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
