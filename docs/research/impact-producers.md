# Actual ImpactGraph producers

Sources and installed producer outputs checked on 2026-10-04. These optional
tools do not run on installation or on an ordinary default impact query.

Microsoft TypeScript is Apache-2.0. The adapter borrows its Program, CompilerHost,
module resolver and type checker APIs; it adds a selected virtual filesystem,
contained execution and typed graph validation. Actual 5.7.3 output established
AST declaration names and lines before implementation. The official
[compiler API guide](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API)
warns that version 7 has a different API; the adapter currently qualifies only
5.7.3. The [module reference](https://www.typescriptlang.org/docs/handbook/modules/reference.html)
documents paths, Node resolution and package exports. This is not a standalone
type check or a prediction of runtime dispatch.

Coverage.py is Apache-2.0. Actual 7.10.7 JSON had format 3, `show_contexts: true`,
native Windows filename separators and line-number keys containing explicit
static context labels. The official [context documentation](https://coverage.readthedocs.io/en/7.10.7/contexts.html)
distinguishes global, static and dynamic attribution. An actual single-file
Jinja run with static context `jinja-nodes` passed one test, then exported contexts.
It revealed execution of `nodes.py` through the pytest environment fixture.
The mapping to that test file is an unsigned operator assertion, not assertion
coverage or production-path mining.

Node is MIT. Actual Node 22.17.1 `NODE_V8_COVERAGE` output supplied file URLs,
function records, UTF-16 range offsets, execution counts and block-coverage flags.
The [Node CLI documentation](https://nodejs.org/api/cli.html#node_v8_coveragedir)
describes V8 output and optional source-map data. The converter supports native
JS on Node 22.x; the CI producer test uses the actual installed patch version.
The local run executed a separate one-test CommonJS fixture. It is adapter
acceptance, not an upstream Zod behavior or performance measurement.
Source-mapped TypeScript remains unsupported, rather than treating generated
offsets as original source. Neither converter reads arbitrary project code as a
producer or authenticates unsigned reports.

The benchmark uses pytest JUnit and Jest 29.7.0 JSON with ts-jest 29.1.5 and
TypeScript 5.7.3. Producer counts are checked against individual test outcomes;
errors, empty runs, impossible summaries and timeouts cannot become passing
checks or qualified faults. Zod diagnostics were disabled: runtime assertions
and type checking are separate. See [the frozen corpus and all outcomes](../../results/impact-acceptance/README.md).
