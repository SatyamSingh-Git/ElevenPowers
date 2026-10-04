"""Real grammar controls for qualified repository JS/TS import relationships."""
import json

import pytest

from core import polyglot
from core.impact import build


def put(root, path, source):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(source, encoding='utf-8')


def links(graph):
    return {(e.source, e.target) for e in graph.edges if e.kind == 'imports'}


@pytest.mark.skipif(not polyglot.available(), reason='optional grammar pack absent')
@pytest.mark.parametrize('source,target', [
    ('import {expire} from "./session";', 'session.ts'),
    ('import {expire} from "./session.js";', 'session.ts'),
    ('export {expire} from "./session";', 'session.ts'),
    ('const s = require("./session");', 'session.ts'),
    ('import "./session";', 'session/index.ts'),
])
def test_typescript_relative_barrels_and_js_extension(tmp_path, source, target):
    put(tmp_path, target, 'export function expire() { return 1; }')
    put(tmp_path, 'api.ts', source)
    value = build(tmp_path)
    assert ('file:api.ts', 'file:' + target) in links(value)
    assert value.coverage['parsed_typescript'] == 2


@pytest.mark.skipif(not polyglot.available(), reason='optional grammar pack absent')
def test_declared_workspace_entry_and_subpath(tmp_path):
    put(tmp_path, 'packages/session/package.json', json.dumps(
        {'name': '@app/session', 'main': 'lib/entry.js'}))
    put(tmp_path, 'packages/session/lib/entry.ts', 'export const expire = () => 1;')
    put(tmp_path, 'packages/session/lib/util.ts', 'export const tick = () => 1;')
    put(tmp_path, 'packages/api/index.ts',
        'import {expire} from "@app/session"; import {tick} from "@app/session/lib/util";')
    edges = links(build(tmp_path))
    assert ('file:packages/api/index.ts', 'file:packages/session/lib/entry.ts') in edges
    assert ('file:packages/api/index.ts', 'file:packages/session/lib/util.ts') in edges


@pytest.mark.skipif(not polyglot.available(), reason='optional grammar pack absent')
def test_ambiguous_extensions_do_not_choose_a_target(tmp_path):
    put(tmp_path, 'session.ts', 'export const x=1;')
    put(tmp_path, 'session.js', 'export const x=2;')
    put(tmp_path, 'api.ts', 'import {x} from "./session";')
    value = build(tmp_path)
    assert not links(value)
    assert 'ambiguous' in ' '.join(value.issues)


@pytest.mark.skipif(not polyglot.available(), reason='optional grammar pack absent')
def test_unknown_bare_alias_and_syntax_errors_are_gaps(tmp_path):
    put(tmp_path, 'api.ts', 'import {x} from "@/session";')
    put(tmp_path, 'broken.ts', 'export function broken( {')
    value = build(tmp_path)
    assert 'unresolved' in ' '.join(value.issues)
    assert 'parse' in ' '.join(value.issues)


def test_missing_grammar_and_unsupported_language_visible(tmp_path, monkeypatch):
    put(tmp_path, 'api.ts', 'import {x} from "./session";')
    put(tmp_path, 'session.ts', 'export const x=1;')
    put(tmp_path, 'main.go', 'package main\nfunc main() {}')
    monkeypatch.setattr(polyglot, '_get_parser', None)
    value = build(tmp_path)
    assert not links(value)
    assert 'grammar' in ' '.join(value.issues)
    assert 'unsupported' in ' '.join(value.issues)


@pytest.mark.skipif(not polyglot.available(), reason='optional grammar pack absent')
def test_duplicate_workspace_and_unsafe_relative_import(tmp_path):
    for name in ('a', 'b'):
        put(tmp_path, name + '/package.json', '{"name":"@app/session","main":"index.ts"}')
        put(tmp_path, name + '/index.ts', 'export const x=1;')
    put(tmp_path, 'api.ts', 'import {x} from "@app/session"; import y from "../outside";')
    value = build(tmp_path)
    assert not links(value)
    assert 'ambiguous' in ' '.join(value.issues)
    assert 'unresolved' in ' '.join(value.issues)
