"""Optional real TypeScript compiler controls; source is never executed."""
import json
import os
from pathlib import Path

import pytest

from core.impact import build, analyze
from core.impact.compiler import validate


def engine():
    root=Path(__file__).parents[1]
    candidates=[os.environ.get('EP_TYPESCRIPT_ENGINE',''),
        root/'.venv/impact-acceptance/tools/node_modules/typescript/lib/typescript.js',
        root/'.venv/strength-js/node_modules/typescript/lib/typescript.js']
    return next((Path(p) for p in candidates if p and Path(p).is_file()),None)


ENGINE=engine()
pytestmark=pytest.mark.skipif(ENGINE is None,reason='optional TypeScript compiler absent')


def put(root,path,value):
    file=root/path
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(value) if isinstance(value,dict) else value,encoding='utf-8')


def test_compiler_resolves_config_alias_and_imported_call(tmp_path):
    put(tmp_path,'tsconfig.json',{'compilerOptions':{'baseUrl':'.','paths':{'@/*':['src/*']}}})
    put(tmp_path,'src/session.ts','export function expire() { return 1; }')
    put(tmp_path,'src/api.ts','import {expire as check} from "@/session"; export const login=()=>check();')
    value=build(tmp_path,typescript=ENGINE)
    assert any(e.source=='file:src/api.ts' and e.target=='file:src/session.ts' and e.kind=='imports' for e in value.edges)
    assert any(e.source=='file:src/api.ts' and e.target=='symbol:src/session.ts#expire' and e.kind=='calls' for e in value.edges)
    assert value.coverage['typescript_compiler']['version']=='5.7.3'


def test_package_exports_and_barrel_alias_resolve_to_real_declaration(tmp_path):
    put(tmp_path,'package.json',{'type':'module'})
    put(tmp_path,'packages/session/package.json',{'name':'@app/session','type':'module',
        'exports':{'.':'./src/index.ts'}})
    put(tmp_path,'packages/session/src/session.ts','export function expire() { return 1; }')
    put(tmp_path,'packages/session/src/index.ts','export {expire as check} from "./session.js";')
    put(tmp_path,'api.ts','import {check} from "@app/session"; check();')
    value=build(tmp_path,typescript=ENGINE)
    assert any(e.target=='symbol:packages/session/src/session.ts#expire' and e.kind=='calls' for e in value.edges)


def test_namespace_method_and_specific_symbol_query(tmp_path):
    put(tmp_path,'session.ts','export class Session { static expire() { return 1; } static other() { return 2; } }')
    put(tmp_path,'api.ts','import * as s from "./session"; s.Session.expire();')
    put(tmp_path,'test_api.ts','import "./api";')
    put(tmp_path,'unrelated.ts','export function expire() { return 0; }')
    value=build(tmp_path,typescript=ENGINE)
    report=analyze(value,['symbol:session.ts#Session.expire'])
    assert 'test_api.ts' in {n['path'] for n in report['tests']}
    assert 'unrelated.ts' not in {n['path'] for n in report['affected']}


def test_type_only_and_shadowed_bindings_do_not_invent_calls(tmp_path):
    put(tmp_path,'session.ts','export function expire() { return 1; }')
    put(tmp_path,'api.ts','import {expire} from "./session"; function run(expire:()=>number) { return expire(); }')
    value=build(tmp_path,typescript=ENGINE)
    assert not any(e.kind=='calls' and e.source=='file:api.ts' for e in value.edges)


def test_export_reassignment_is_not_a_stable_callable(tmp_path):
    put(tmp_path,'session.ts','export function expire() { return 1; } expire=()=>2;')
    put(tmp_path,'api.ts','import {expire} from "./session"; expire();')
    value=build(tmp_path,typescript=ENGINE)
    assert not any(e.kind=='calls' and e.source=='file:api.ts' for e in value.edges)
    assert 'rebound' in ' '.join(value.issues)


def test_project_source_and_executable_configs_are_not_run(tmp_path):
    put(tmp_path,'api.ts','throw new Error("do not run"); export const x=1;')
    put(tmp_path,'tsconfig.js','require("fs").writeFileSync("unexpected", "bad");')
    value=build(tmp_path,typescript=ENGINE)
    assert 'file:api.ts' in value.nodes
    assert not (tmp_path/'unexpected').exists()


def test_missing_engine_and_zero_budget_are_explicit(tmp_path):
    put(tmp_path,'api.ts','export const x=1;')
    assert 'compiler' in ' '.join(build(tmp_path,typescript=tmp_path/'missing.js').issues)
    value=build(tmp_path,typescript=ENGINE,seconds=0)
    assert not value.coverage['complete']


def test_invalid_config_outside_scope_is_not_read(tmp_path):
    put(tmp_path,'api.ts','export const x=1;')
    with pytest.raises(ValueError):
        build(tmp_path,typescript=ENGINE,tsconfig='../outside.json')


def test_instance_dispatch_is_qualified_not_an_implementation_prediction(tmp_path):
    put(tmp_path,'session.ts','export class Session { expire() { return 1; } }')
    put(tmp_path,'api.ts','import {Session} from "./session"; export function run(s:Session) { return s.expire(); }')
    value=build(tmp_path,typescript=ENGINE)
    assert not any(e.kind=='calls' and e.source=='file:api.ts' for e in value.edges)
    assert 'dispatch' in ' '.join(value.issues)


def test_config_extends_cannot_read_physical_outside_snapshot(tmp_path):
    put(tmp_path,'secret.json',{'compilerOptions':{'baseUrl':'.','paths':{'hidden':['src/session']}}})
    put(tmp_path,'.gitignore','secret.json\n')
    put(tmp_path,'tsconfig.json',{'extends':'./secret.json'})
    put(tmp_path,'src/session.ts','export function expire() { return 1; }')
    put(tmp_path,'api.ts','import {expire} from "hidden"; expire();')
    value=build(tmp_path,typescript=ENGINE)
    assert not any(e.kind=='calls' for e in value.edges)
    assert 'config' in ' '.join(value.issues)


def test_external_and_duplicate_workspace_packages_are_explicit(tmp_path):
    put(tmp_path,'a/package.json',{'name':'same','main':'index.ts'})
    put(tmp_path,'a/index.ts','export function x() {}')
    put(tmp_path,'b/package.json',{'name':'same','main':'index.ts'})
    put(tmp_path,'b/index.ts','export function x() {}')
    put(tmp_path,'api.ts','import {x} from "same"; import {y} from "external"; x(); y();')
    value=build(tmp_path,typescript=ENGINE)
    assert not any(e.kind=='calls' for e in value.edges)
    assert 'ambiguous workspace' in ' '.join(value.issues)
    assert 'external' in ' '.join(value.issues)


@pytest.mark.parametrize('payload',[
    {'schema':True,'version':'5.7.3','nodes':[],'edges':[],'issues':[]},
    {'schema':1,'version':'7.1','nodes':[],'edges':[],'issues':[]},
    {'schema':1,'version':'5.7.3','nodes':[],'edges':[{'source':'file:a.ts','target':'file:outside.ts','kind':'imports','path':'a.ts','line':1}],'issues':[]},
])
def test_compiler_result_is_validated_before_graph_mutation(payload):
    with pytest.raises(ValueError):
        validate(payload,{'a.ts':b'export const a=1;'})
