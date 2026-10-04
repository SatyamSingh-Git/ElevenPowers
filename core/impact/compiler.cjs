/* Microsoft TypeScript 5.7.3 compiler API (Apache-2.0). No target JS execution.
 * The host exposes only snapshot bytes; not the project's physical filesystem.
 * A user-supplied compiler module is trusted executable code, not a sandbox.
 */
'use strict';
const fs = require('fs');
const path = require('path').posix;
const ts = require(process.argv[2]);
if (ts.version !== '5.7.3') throw new Error('qualified compiler version is 5.7.3');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const prefix = '/impact-input';
const sources = new Map(Object.entries(input.sources).map(([p, v]) => [prefix + '/' + p, v]));
const issues = new Set();
function issue(message) { if (issues.size >= 999) { issues.add('compiler issue limit reached'); return; } issues.add(message.slice(0, 600)); }
const workspace = new Map();
for (const [p, data] of sources) {
  if (!p.endsWith('/package.json')) continue;
  try {
    const pkg = JSON.parse(data);
    if (typeof pkg.name === 'string' && /^(@[a-zA-Z0-9._-]+\/)?[a-zA-Z0-9._-]+$/.test(pkg.name)) {
      if (workspace.has(pkg.name)) { workspace.set(pkg.name, null); issue('ambiguous workspace package: ' + pkg.name); }
      else workspace.set(pkg.name, path.dirname(p));
    }
  } catch (_) { issue('compiler package.json parse failed: ' + p.slice(prefix.length + 1)); }
}
function canonical(p) {
  p = path.normalize(p.replace(/\\/g, '/'));
  const marker = prefix + '/node_modules/';
  if (p.startsWith(marker)) {
    const rel = p.slice(marker.length), parts = rel.split('/');
    const name = parts[0].startsWith('@') ? parts.slice(0, 2).join('/') : parts[0];
    const directory = workspace.get(name);
    if (directory) return directory + rel.slice(name.length);
  }
  return p;
}
const fileExists = p => sources.has(canonical(p));
const readFile = p => sources.get(canonical(p));
const directoryExists = p => {
  p = canonical(p);
  if (p === prefix + '/node_modules' && workspace.size) return true;
  if (p.startsWith(prefix + '/node_modules/@')) return true;
  return [...sources.keys()].some(k => k.startsWith(p + '/'));
};
const config = input.config || (fileExists(prefix + '/tsconfig.json') ? 'tsconfig.json' : null);
let options = {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.NodeNext,
  moduleResolution: ts.ModuleResolutionKind.NodeNext, allowJs: true, noEmit: true, noLib: true};
if (config) {
  const location = prefix + '/' + config;
  const read = ts.readConfigFile(location, readFile);
  if (read.error) issue('compiler config unreadable: ' + config);
  else {
    const parsed = ts.parseJsonConfigFileContent(read.config,
      {useCaseSensitiveFileNames: true, fileExists, readFile,
        readDirectory: () => [...sources.keys()].filter(p => /\.(tsx?|mts|cts|jsx?|mjs|cjs)$/.test(p))},
      path.dirname(location), {}, location);
    for (const error of parsed.errors) issue('compiler config: ' + ts.flattenDiagnosticMessageText(error.messageText, ' '));
    options = {...options, ...parsed.options, noEmit: true, noLib: true};
    if (parsed.projectReferences?.length) issue('compiler project references are not separate programs');
  }
}
// All selected sources are roots; tsconfig supplies resolution, not scan scope.
const roots = [...sources.keys()].filter(p => /\.(tsx?|mts|cts|jsx?|mjs|cjs)$/.test(p));
const host = {
  fileExists, readFile, directoryExists, getDirectories: () => [],
  realpath: canonical, getCurrentDirectory: () => prefix,
  getCanonicalFileName: p => p, useCaseSensitiveFileNames: () => true,
  getNewLine: () => '\n', getDefaultLibFileName: () => prefix + '/__absent_lib.d.ts',
  writeFile: () => { throw new Error('emit is disabled'); },
  getSourceFile(p, target) {
    p = canonical(p); const data = readFile(p);
    return data === undefined ? undefined : ts.createSourceFile(p, data, target, true);
  },
  resolveModuleNames(names, containing) {
    return names.map(name => {
      const resolved = ts.resolveModuleName(name, containing, options, host).resolvedModule;
      return resolved ? {...resolved, resolvedFileName: canonical(resolved.resolvedFileName)} : undefined;
    });
  }
};
const program = ts.createProgram(roots, options, host);
const checker = program.getTypeChecker();
const files = program.getSourceFiles().filter(sf => sources.has(sf.fileName));
const nodes = new Map(), declarations = new Map(), symbols = new Map(), rebound = new Set();
const edges = [], edgeKeys = new Set();
let unresolved = 0;
function rel(sf) { return sf.fileName.slice(prefix.length + 1); }
function line(n, sf) { return sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1; }
function walk(node, visit) { visit(node); ts.forEachChild(node, n => walk(n, visit)); }
function symbolAt(node) {
  let s = checker.getSymbolAtLocation(node);
  if (s && s.flags & ts.SymbolFlags.Alias) s = checker.getAliasedSymbol(s);
  return s;
}
function qualified(node, sf) {
  if (!node.name || !ts.isIdentifier(node.name)) return '';
  const parts = [node.name.text];
  for (let p = node.parent; p && p !== sf; p = p.parent) {
    if ((ts.isClassDeclaration(p) || ts.isModuleDeclaration(p) || ts.isFunctionDeclaration(p)) && p.name) parts.unshift(p.name.getText(sf));
    else if (ts.isFunctionLike(p)) return ''; // Anonymous/instance dispatch not qualified.
  }
  return parts.join('.');
}
for (const sf of files) {
  for (const error of sf.parseDiagnostics) issue('compiler parse failed: ' + rel(sf) + ':' + (error.start || 0));
  walk(sf, node => {
    const callable = (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) && node.body
      || ts.isVariableDeclaration(node) && node.initializer && (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer));
    if (!callable && !ts.isClassDeclaration(node)) return;
    const name = qualified(node, sf);
    if (!name) return;
    const id = 'symbol:' + rel(sf) + '#' + name;
    if (nodes.has(id)) { declarations.delete(nodes.get(id)._decl); rebound.add(symbolAt(node.name)); issue('ambiguous or rebound compiler symbol: ' + id); return; }
    if (nodes.size >= 20000) throw new Error('compiler symbol limit 20000 exceeded');
    nodes.set(id, {id, kind: 'symbol', label: name, path: rel(sf), line: line(node, sf), _decl: node});
    declarations.set(node, id);
    const s = symbolAt(node.name); if (s) symbols.set(s, id);
    if (ts.isVariableDeclaration(node)) declarations.set(node.initializer, id);
  });
}
for (const sf of files) walk(sf, n => {
  const assignment = ts.isBinaryExpression(n) && n.operatorToken.kind >= ts.SyntaxKind.FirstAssignment && n.operatorToken.kind <= ts.SyntaxKind.LastAssignment;
  const update = (ts.isPrefixUnaryExpression(n) || ts.isPostfixUnaryExpression(n)) && [ts.SyntaxKind.PlusPlusToken, ts.SyntaxKind.MinusMinusToken].includes(n.operator);
  if (assignment || update) {
    const s = symbolAt(assignment ? n.left : n.operand);
    if (s) { rebound.add(s); if (symbols.has(s)) issue('rebound compiler callable: ' + symbols.get(s)); }
  }
});
function add(source, target, kind, p, n, sf) {
  const edge = {source, target, kind, path: p, line: line(n, sf)};
  const key = JSON.stringify(edge);
  if (!edgeKeys.has(key)) { if (edges.length >= 50000) throw new Error('compiler edge limit 50000 exceeded'); edgeKeys.add(key); edges.push(edge); }
}
for (const sf of files) walk(sf, n => {
  const p = rel(sf);
  let spec;
  if ((ts.isImportDeclaration(n) || ts.isExportDeclaration(n)) && n.moduleSpecifier && ts.isStringLiteral(n.moduleSpecifier)) spec = n.moduleSpecifier.text;
  if (ts.isCallExpression(n) && n.arguments.length === 1 && ts.isStringLiteral(n.arguments[0])
      && (n.expression.kind === ts.SyntaxKind.ImportKeyword || ts.isIdentifier(n.expression) && n.expression.text === 'require' && !symbolAt(n.expression))) spec = n.arguments[0].text;
  if (spec) {
    const resolved = host.resolveModuleNames([spec], sf.fileName)[0];
    if (resolved && sources.has(resolved.resolvedFileName)) add('file:' + p, 'file:' + rel({fileName: resolved.resolvedFileName}), 'imports', p, n, sf);
    else issue('compiler import outside selected resolution: ' + p + ':' + line(n, sf) + ' ' + spec);
  }
  if (ts.isCallExpression(n)) {
    const s = symbolAt(n.expression);
    const signature = checker.getResolvedSignature(n);
    const decl = signature?.declaration;
    if (decl && ts.isMethodDeclaration(decl) && !decl.modifiers?.some(m => m.kind === ts.SyntaxKind.StaticKeyword)) {
      issue('compiler instance dispatch is not a concrete call: ' + p + ':' + line(n, sf)); return;
    }
    // Signature declarations are reusable types. Only the callee's established
    // binding may identify a selected implementation; callback parameters and
    // copied/reassigned aliases cannot inherit it from their signature.
    const id = s && symbols.get(s);
    const implementation = id && nodes.get(id)?._decl;
    if (ts.isPropertyAccessExpression(n.expression)) {
      let receiver = n.expression.expression;
      while (ts.isPropertyAccessExpression(receiver)) receiver = receiver.expression;
      const receiverSymbol = symbolAt(receiver);
      const namespaceImport = ts.isIdentifier(receiver) && checker.getSymbolAtLocation(receiver)?.declarations?.some(d => ts.isNamespaceImport(d));
      const classOrNamespace = receiverSymbol?.declarations?.some(d => (ts.isClassDeclaration(d) || ts.isModuleDeclaration(d)) && sources.has(d.getSourceFile().fileName));
      if (!receiverSymbol || rebound.has(receiverSymbol) || !namespaceImport && !classOrNamespace) {
        unresolved++; return;
      }
    }
    // An interface, parameter, overload without known implementation, or union
    // signature does not establish a concrete implementation call.
    if (s && rebound.has(s)) {
      issue('rebound or unsupported compiler call binding: ' + p + ':' + line(n, sf)); return;
    }
    if (id && implementation && nodes.get(id).path !== p && (implementation.body || ts.isVariableDeclaration(implementation))) add('file:' + p, id, 'calls', p, n, sf);
    else if (!id) unresolved++;
  }
});
if (unresolved) issue('compiler calls without a concrete selected implementation: ' + unresolved);
const exported = [...nodes.values()].map(({_decl, ...n}) => n);
process.stdout.write(JSON.stringify({schema: 1, version: ts.version, nodes: exported, edges,
  issues: [...issues], files: files.length, config, unresolved_calls: unresolved}));
