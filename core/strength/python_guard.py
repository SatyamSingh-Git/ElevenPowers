"""Installed as private sitecustomize during trusted test execution only.

Detect known Python import redirection to the original project, including .pth
and PEP 660 finder mappings. This is an isolation diagnostic, not a security
sandbox. Python processes that disable startup customization are unsupported.
"""
import os
from pathlib import Path
import sys

_original = Path(os.environ['EP_STRENGTH_GUARD_ORIGINAL']).resolve()
_prefix = Path(sys.prefix).resolve()
_marker = os.environ['EP_STRENGTH_GUARD_MARKER']


def _inside_original(value):
    if not isinstance(value, (str, bytes, os.PathLike)):
        return False
    try:
        path = Path(os.fsdecode(value)).resolve()
        return path.is_relative_to(_original) and not (
            _prefix != _original and _prefix.is_relative_to(_original) and path.is_relative_to(_prefix))
    except (OSError, ValueError):
        return False


def _deny():
    with open(_marker, 'w', encoding='utf-8') as stream:
        stream.write('Python import/read path points to the original workspace; isolation is incomplete')
    raise PermissionError('original workspace cannot be read during isolated test-strength execution')


def _audit(event, arguments):
    if event == 'open' and arguments and _inside_original(arguments[0]):
        _deny()


sys.addaudithook(_audit)
_bad = any(_inside_original(path) for path in sys.path)
_bad |= any(_inside_original(getattr(module, '__file__', None)) for module in list(sys.modules.values()))
for finder in sys.meta_path:
    module = sys.modules.get(getattr(finder, '__module__', ''))
    mapping = getattr(module, 'MAPPING', {})
    if isinstance(mapping, dict):
        _bad |= any(_inside_original(path) for path in mapping.values())
if _bad:
    try:
        _deny()
    finally:
        raise SystemExit(78)
