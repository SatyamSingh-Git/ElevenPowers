// StrykerJS supplies operators and replacement ranges. This optional worker
// limits selected candidates; shared Python execution owns all test attempts.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';

const engine = process.argv[2];
const metadata = JSON.parse(fs.readFileSync(path.join(engine, 'package.json'), 'utf8'));
if (metadata.name !== '@stryker-mutator/instrumenter' || metadata.version !== '9.5.1') {
  throw new Error('Supported Stryker instrumenter version is 9.5.1');
}
const {Instrumenter} = await import(pathToFileURL(path.join(engine, 'dist/src/index.js')).href);
const logger = {debug(){}, info(){}, warn(){}, error(){}, isDebugEnabled(){return false;}};
const instrumenter = new Instrumenter(logger);
const request = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const candidates = [];
let more = false;
const groups = new Map();
const sources = new Map();
let eligible = 0;
const parserOptions = {excludedMutations: [], ignorers: [], plugins: null};
const {createParser} = await import(pathToFileURL(path.join(engine, 'dist/src/parsers/index.js')).href);
const parse = createParser(parserOptions);
const overlaps = (start, end, range) => start <= range[1] && end >= range[0];
function targetsFrom(ast, changed) {
  const functions = [];
  const functionTypes = new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression',
    'ObjectMethod','ClassMethod','ClassPrivateMethod']);
  function walk(node, parent) {
    if (!node || typeof node !== 'object') return;
    if (functionTypes.has(node.type) && node.loc) {
      const start = Math.min(node.loc.start.line, ...(node.decorators ?? []).map(d => d.loc.start.line));
      const end = Math.max(start, node.loc.end.line - (node.loc.end.column === 0 ? 1 : 0));
      const context = node.id?.name ?? node.key?.name ?? parent?.id?.name ?? 'anonymous';
      functions.push([start,end,context]);
    }
    for (const [key,value] of Object.entries(node)) {
      if (['loc','extra','tokens','comments'].includes(key)) continue;
      if (Array.isArray(value)) value.forEach(child => walk(child,node));
      else if (value && typeof value === 'object' && value.type) walk(value,node);
    }
  }
  walk(ast.root);
  const targets = [];
  for (const range of changed) {
    const enclosing = functions.filter(f => f[0] <= range[0] && f[1] >= range[1]);
    enclosing.sort((a,b) => (a[1]-a[0])-(b[1]-b[0]));
    const chosen = enclosing.length
      ? [enclosing[0], ...functions.filter(f => range[0] <= f[0] && f[1] <= range[1])]
      : functions.filter(f => overlaps(f[0],f[1],range));
    targets.push(...chosen);
    let cursor = range[0];
    for (const [start,end] of [...chosen].sort((a,b) => a[0]-b[0])) {
      if (cursor < start) targets.push([cursor,Math.min(start-1,range[1]),'module']);
      cursor = Math.max(cursor,end+1);
    }
    if (cursor <= range[1]) targets.push([cursor,range[1],'module']);
  }
  return [...new Map(targets.map(t => [JSON.stringify(t),t])).values()];
}
for (const name of request.paths) {
  if (fs.statSync(name).size > 1024 * 1024) throw new Error('Mutation source exceeds producer limit');
  const source = fs.readFileSync(name, 'utf8');
  sources.set(name, source);
  const changed = request.regions?.[name];
  if (changed && !changed.length) continue;
  if (changed?.some(range => range[1] > source.split(/\r?\n/).length)) throw new Error('Changed ranges exceed copied source');
  const targets = changed ? targetsFrom(await parse(source,name),changed) : null;
  const result = await instrumenter.instrument([{name, content: source, mutate: true}],
    parserOptions);
  const lines = source.split('\n');
  const offset = position => lines.slice(0, position.line).reduce((sum, line) => sum + line.length + 1, 0) + position.column;
  for (const mutant of result.mutants) {
    if (mutant.ignoreReason) continue;
    if (!changed && candidates.length >= request.maximum) { more = true; break; }
    const line = mutant.location.start.line + 1;
    const endLine = Math.max(line, mutant.location.end.line + 1 - (mutant.location.end.column === 0 ? 1 : 0));
    const choices = targets?.filter(t => t[0] <= line && endLine <= t[1]).sort((a,b) => (a[1]-a[0])-(b[1]-b[0]));
    if (changed && !choices.length) continue;
    const start = offset(mutant.location.start), end = offset(mutant.location.end);
    if (start < 0 || end < start || end > source.length) throw new Error('Invalid mutation range');
    if (source.slice(start, end) === mutant.replacement) continue;
    const item = {id: crypto.createHash('sha256').update(name + '|' + mutant.id).digest('hex').slice(0,24),
      path: name, line, operator: mutant.mutatorName};
    if (changed) {
      const target = choices[0];
      Object.assign(item,{end_line:endLine,context:target[2],
        relevance:changed.some(r => overlaps(line,endLine,r)) ? 'changed_lines' : 'changed_function'});
      const key = JSON.stringify([name,target]);
      if (!groups.has(key)) groups.set(key,[]);
      groups.get(key).push({item, start, end, replacement: mutant.replacement});
      if (++eligible > 100000) throw new Error('Eligible mutation enumeration limit exceeded');
    } else candidates.push({...item, content: source.slice(0, start) + mutant.replacement + source.slice(end)});
  }
  if (more) break;
}
if (request.regions !== null && request.regions !== undefined) {
  const files = new Map();
  for (const key of [...groups.keys()].sort()) {
    const name = JSON.parse(key)[0];
    if (!files.has(name)) files.set(name,[]);
    files.get(name).push(key);
    groups.get(key).sort((a,b) => (a.item.relevance !== 'changed_lines') - (b.item.relevance !== 'changed_lines'));
  }
  const turns = [...files.keys()];
  while (turns.length && candidates.length < request.maximum) {
    const name = turns.shift(), key = files.get(name).shift();
    const {item, start, end, replacement} = groups.get(key).shift();
    const source = sources.get(name);
    candidates.push({...item, content: source.slice(0,start) + replacement + source.slice(end)});
    if (groups.get(key).length) files.get(name).push(key);
    if (files.get(name).length) turns.push(name);
  }
  more = turns.length > 0;
}
console.log(JSON.stringify({version: metadata.version, candidates, more}));
