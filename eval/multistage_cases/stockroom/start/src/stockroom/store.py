"""The JSON data file: one document holding items, locations, stock and movements.

The document is used directly as the in-memory model. Callers change it through
`Inventory` and write it back with `save`.
"""
import json
import os
from pathlib import Path

from .models import StockError

SCHEMA_VERSION = 1
DEFAULT_FILE = 'stockroom.json'
FILE_ENV = 'STOCKROOM_FILE'
SECTIONS = ('items', 'locations', 'stock', 'movements')


def default_path(environ=None):
    environ = os.environ if environ is None else environ
    return Path(environ.get(FILE_ENV) or DEFAULT_FILE)


def new_document():
    return {'version': SCHEMA_VERSION, 'items': {}, 'locations': {}, 'stock': {}, 'movements': []}


def load(path):
    """The document stored at `path`, or an empty one when the file does not exist yet."""
    path = Path(path)
    if not path.exists():
        return new_document()
    try:
        doc = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise StockError(f'data file is not valid JSON: {path} (line {exc.lineno})') from None
    version = doc.get('version') if isinstance(doc, dict) else None
    if version != SCHEMA_VERSION:
        raise StockError(f'unsupported data file version: {version}')
    missing = [name for name in SECTIONS if name not in doc]
    if missing:
        raise StockError(f"data file is missing {', '.join(missing)}: {path}")
    return doc


def save(path, doc):
    """Write the document so that a crash mid-write leaves the old file in place."""
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)
