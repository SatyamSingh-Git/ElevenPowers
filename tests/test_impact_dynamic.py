"""Literal import dependencies retain actual binding and source qualification."""
import pytest

from core.impact import build, analyze


def put(root, path, source):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding='utf-8')


@pytest.mark.parametrize('source', [
    'import importlib\ndef runner(): return importlib.import_module("pkg.api")\n',
    'import importlib as loader\ndef runner(): return loader.import_module(name="pkg.api")\n',
    'from importlib import import_module as load\ndef runner(): return load(".api", "pkg")\n',
    'import importlib.util\ndef runner(): return importlib.import_module(".api", package="pkg")\n',
])
def test_literal_imports_use_unique_selected_targets_and_enclosing_witness(tmp_path, source):
    put(tmp_path, 'pkg/api.py', 'def expire(): return 1\n')
    put(tmp_path, 'tests/test_api.py', source)
    value = build(tmp_path)
    edges = [e for e in value.edges if e.kind == 'dynamic_import']
    assert any(e.source == 'file:tests/test_api.py' and e.target == 'file:pkg/api.py' for e in edges)
    assert any(e.source == 'symbol:tests/test_api.py#runner' for e in edges)
    assert all(e.origin == 'static' and e.line == 2 and e.identity == 'importlib.import_module' for e in edges)
    assert 'tests/test_api.py' in {n['path'] for n in analyze(value, ['pkg/api.py'])['tests']}


@pytest.mark.parametrize('source', [
    'import importlib\ndef runner(importlib): return importlib.import_module("pkg.api")\n',
    'import importlib\nimportlib.import_module = lambda _: None\nimportlib.import_module("pkg.api")\n',
    'import importlib\nsetattr(importlib,"import_module",lambda _:None)\nimportlib.import_module("pkg.api")\n',
    'from importlib import import_module as load\nload=lambda _:None\nload("pkg.api")\n',
    'import importlib as load\nimport other as load\nload.import_module("pkg.api")\n',
])
def test_shadowed_or_rebound_import_tools_cannot_invent_literal_edges(tmp_path, source):
    put(tmp_path, 'pkg/api.py', 'x=1\n')
    put(tmp_path, 'test_api.py', source)
    value = build(tmp_path)
    assert not [e for e in value.edges if e.kind == 'dynamic_import']
    assert any('dynamic import' in issue for issue in value.issues)


@pytest.mark.parametrize('source', [
    'from importlib import import_module as load\ndef configure(ignore=(load:=lambda _:None)): pass\n'
    'def test_api(): assert load("pkg.api") is None\n',
    'import importlib\ndef configure(ignore=setattr(importlib,"import_module",lambda _:None)): pass\n'
    'def test_api(): assert importlib.import_module("pkg.api") is None\n',
    'import importlib\nimportlib.__dict__["import_module"]=lambda _:None\n'
    'def test_api(): assert importlib.import_module("pkg.api") is None\n',
])
def test_enclosing_defaults_and_attribute_containers_invalidate_literal_tools(tmp_path, source):
    put(tmp_path, 'pkg/api.py', 'raise AssertionError("must not import")\n')
    put(tmp_path, 'test_api.py', source)
    graph=build(tmp_path)
    assert not [e for e in graph.edges if e.kind=='dynamic_import']
    assert not analyze(graph, ['pkg/api.py'])['test_selection']['focused']
    assert any('dynamic import' in issue for issue in graph.issues)


def test_ordinary_default_preserves_the_qualified_import(tmp_path):
    put(tmp_path, 'pkg/api.py', 'x=1\n')
    put(tmp_path, 'test_api.py', 'from importlib import import_module as load\n'
        'def configure(ignore=1): pass\ndef test_api(): assert load("pkg.api")\n')
    assert analyze(build(tmp_path), ['pkg/api.py'])['test_selection']['focused']


@pytest.mark.parametrize('call', [
    'importlib.import_module(name)', 'importlib.import_module("pkg."+name)',
    'importlib.import_module(".api")', 'importlib.import_module("pkg.api", **options)',
    'importlib.import_module("pkg.api", name="other")',
])
def test_unknown_names_or_arguments_remain_explicit_gaps(tmp_path, call):
    put(tmp_path, 'pkg/api.py', 'x=1\n')
    put(tmp_path, 'test_api.py', 'import importlib\n'+call+'\n')
    value = build(tmp_path)
    assert not [e for e in value.edges if e.kind == 'dynamic_import']
    assert any('dynamic import' in issue for issue in value.issues)


def test_local_importlib_module_does_not_masquerade_as_standard_import_tool(tmp_path):
    put(tmp_path, 'importlib.py', 'def import_module(name): return None\n')
    put(tmp_path, 'pkg/api.py', 'raise RuntimeError("source must never run")\n')
    put(tmp_path, 'test_api.py', 'import importlib\nimportlib.import_module("pkg.api")\n')
    value = build(tmp_path)
    assert not [e for e in value.edges if e.kind == 'dynamic_import']
    assert any('dynamic import' in issue for issue in value.issues)


def test_ambiguous_module_roots_are_not_guessed(tmp_path):
    put(tmp_path, 'pkg/api.py', 'x=1\n')
    put(tmp_path, 'src/pkg/api.py', 'x=2\n')
    put(tmp_path, 'test_api.py', 'import importlib\nimportlib.import_module("pkg.api")\n')
    value = build(tmp_path)
    assert not [e for e in value.edges if e.kind == 'dynamic_import']
    assert any('ambiguous dynamic import' in issue for issue in value.issues)


def test_local_call_owner_keeps_symbol_queries_connected_to_import_fallbacks(tmp_path):
    put(tmp_path, 'api.py', 'def read(): return 1\ndef run(): return read()\n')
    put(tmp_path, 'test_api.py', 'import api\ndef test_run(): assert api.run() == 1\n')
    value = build(tmp_path)
    assert any(e.source == 'symbol:api.py#run' and e.target == 'symbol:api.py#read'
               and e.kind == 'calls' for e in value.edges)
    assert any(e.source == 'file:api.py' and e.target == 'symbol:api.py#run'
               and e.kind == 'defines' for e in value.edges)
    assert 'test_api.py' in {n['path'] for n in analyze(value, ['symbol:api.py#read'])['tests']}


def test_rebound_and_locally_shadowed_function_names_do_not_create_local_calls(tmp_path):
    put(tmp_path, 'api.py', 'def read(): return 1\ndef run(read): return read()\n')
    value = build(tmp_path)
    assert not any(e.target == 'symbol:api.py#read' and e.kind == 'calls' for e in value.edges)
    put(tmp_path, 'api.py', 'def read(): return 1\nread=lambda:2\ndef run(): return read()\n')
    value = build(tmp_path)
    assert not any(e.target == 'symbol:api.py#read' for e in value.edges)


def test_enclosing_function_retains_its_concrete_imported_module_dependency(tmp_path):
    put(tmp_path, 'api.py', 'class Service: pass\n')
    put(tmp_path, 'conftest.py', 'from api import Service\ndef service(): return Service()\n')
    value = build(tmp_path)
    assert any(e.source == 'symbol:conftest.py#service' and e.target == 'file:api.py'
               and e.kind == 'uses' for e in value.edges)
