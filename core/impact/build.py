"""Build a fresh bounded graph; never import or execute target project code."""
import hashlib
import json
import math
import time
from pathlib import Path, PurePosixPath

from ..evidence import scan_sources
from .model import Graph, Node
from .source import extract
from .typescript import extract_typescript
from . import ingest
from .history import collect

FILE_BYTES = 4 * 1024 * 1024


def safe_path(root, rel):
    """Return an in-scope ordinary path, without following repository links."""
    if not isinstance(rel, str) or not rel or '\\' in rel or ':' in rel:
        raise ValueError('expected a repository-relative POSIX path')
    path = PurePosixPath(rel)
    if path.is_absolute() or '..' in path.parts or '.git' in path.parts:
        raise ValueError('unsafe repository-relative path')
    if str(path) != rel:
        raise ValueError('path must be normalized')
    full = root / rel
    if (any((root / str(p)).is_symlink() for p in (path, *path.parents))
            or any((root / str(p) / '.git').exists() for p in path.parents if str(p) != '.')
            or not full.resolve().is_relative_to(root)):
        raise ValueError('linked or out-of-scope input')
    return full


def read_input(root, rel, deadline):
    if time.monotonic() >= deadline:
        raise ValueError('impact deadline reached reading inputs')
    full = safe_path(root, rel)
    if not full.is_file():
        raise ValueError('input is missing or not a file')
    with full.open('rb') as stream:
        data = stream.read(FILE_BYTES + 1)
    if len(data) > FILE_BYTES:
        raise ValueError('per-file 4 MiB limit exceeded')
    return data


def build(root, *, seconds=30, max_files=None, max_bytes=None, observations=None, history=0,
          typescript=None, tsconfig=None):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('project root must be an existing directory')
    if tsconfig is not None:
        safe_path(root, tsconfig)
        if not tsconfig.endswith('.json') or typescript is None:
            raise ValueError('tsconfig must be a relative JSON path with an explicit compiler')
    if not isinstance(seconds, (float, int)) or not math.isfinite(seconds) or not 0 <= seconds <= 300:
        raise ValueError('seconds must be finite and between 0 and 300')
    if type(history) is not int or not 0 <= history <= 200:
        raise ValueError('history must be between 0 and 200 commits')
    for name, value in (('max_files', max_files), ('max_bytes', max_bytes)):
        if value is not None and (type(value) is not int or value <= 0):
            raise ValueError(name + ' must be a positive integer')
    deadline = time.monotonic() + seconds
    graph = Graph(coverage={'complete': False, 'unresolved_calls': 0})
    artifact = None
    if observations is not None:
        artifact_path = Path(observations)
        artifact = artifact_path.as_posix() if not artifact_path.is_absolute() else artifact_path.relative_to(root).as_posix()
        safe_path(root, artifact)
    # Command discovery is irrelevant here and can eagerly read arbitrary large
    # manifests. Read only the scan policy, under the same explicit-input rules.
    policy = {}
    try:
        config = safe_path(root, '.elevenpowers/config.json')
        if config.exists():
            value = json.loads(read_input(root, '.elevenpowers/config.json', deadline))
            if not isinstance(value, dict):
                raise ValueError('scan configuration must be an object')
            policy = value.get('scan', {})
    except (OSError, ValueError, RecursionError):
        graph.issues.append('scan configuration unreadable, invalid or over budget')
    scan = scan_sources(root, limit=max_files, max_bytes=max_bytes, deadline=deadline, policy=policy)
    graph.issues.extend(scan.issues)
    sources, fingerprints = {}, {}
    read_bytes = 0
    allowance = max_bytes if max_bytes is not None else (
        policy.get('max_bytes', 268435456) if isinstance(policy, dict) else 268435456)
    if type(allowance) is not int or allowance <= 0:
        allowance = 268435456
    for path in scan.files:
        if path == artifact:
            continue
        identity = 'file:' + path
        graph.nodes[identity] = Node(identity, 'file', path, path)
        try:
            data = read_input(root, path, deadline)
            read_bytes += len(data)
            if read_bytes > allowance:
                raise ValueError('source read byte limit exceeded')
        except (OSError, ValueError) as exc:
            graph.issues.append(f'{exc}: {path}')
            fingerprints[path] = 'unread'
            continue
        sources[path] = data
        fingerprints[path] = hashlib.sha256(data).hexdigest()
    graph.fingerprint = hashlib.sha256(json.dumps(
        {'files': fingerprints, 'policy': policy, 'file_limit': max_files,
         'byte_limit': max_bytes}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    graph.coverage.update(selected_files=len(graph.nodes), read_files=len(sources),
                          read_bytes=read_bytes, selection_complete=scan.complete,
                          inputs_complete=scan.complete and not graph.issues)
    extract(graph, sources, deadline)
    if typescript is None:
        extract_typescript(graph, sources, deadline)
    else:
        from .compiler import extract_compiler
        extract_compiler(graph, sources, typescript, tsconfig, deadline)
    ingest.declarations(graph, sources, deadline)
    if artifact:
        try:
            data = read_input(root, artifact, deadline)
        except (OSError, ValueError) as exc:
            graph.quarantined.append({'artifact': artifact, 'reason': str(exc)})
            graph.issues.append('observation artifact unreadable or over budget')
        else:
            ingest.observations(graph, data, artifact, deadline)
    if history:
        collect(graph, root, history, deadline)
    graph.coverage['complete'] = not graph.issues
    return graph
