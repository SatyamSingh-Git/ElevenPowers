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
for (const name of request.paths) {
  if (fs.statSync(name).size > 1024 * 1024) throw new Error('Mutation source exceeds producer limit');
  const source = fs.readFileSync(name, 'utf8');
  const result = await instrumenter.instrument([{name, content: source, mutate: true}],
    {excludedMutations: [], ignorers: [], plugins: null});
  const lines = source.split('\n');
  const offset = position => lines.slice(0, position.line).reduce((sum, line) => sum + line.length + 1, 0) + position.column;
  for (const mutant of result.mutants) {
    if (mutant.ignoreReason) continue;
    if (candidates.length >= request.maximum) { more = true; break; }
    const start = offset(mutant.location.start), end = offset(mutant.location.end);
    if (start < 0 || end < start || end > source.length) throw new Error('Invalid mutation range');
    const content = source.slice(0, start) + mutant.replacement + source.slice(end);
    if (content === source) continue;
    candidates.push({id: crypto.createHash('sha256').update(name + '|' + mutant.id).digest('hex').slice(0,24),
      path: name, line: mutant.location.start.line + 1, operator: mutant.mutatorName, content});
  }
  if (more) break;
}
console.log(JSON.stringify({version: metadata.version, candidates, more}));
