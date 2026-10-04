# ImpactGraph

ImpactGraph explains possible effects before changing code. It builds a fresh
local graph for any project and returns actual dependency paths, candidate tests,
optional declared contracts, qualified observations and separate Git associations.
It works without an AI agent and executes no target source or verification command.

## Query before editing

```sh
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . src/auth/session.py
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . src/auth/session.ts --json
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . database:sessions --change "Change expiration semantics"
```

Paths are relative to the chosen root. Multiple paths are accepted. A declared
node ID can select a logical contract. The change description is intent recorded
in the report; it does not create graph evidence or reinterpret source code.

Python imports resolve from the project root and conventional `src/` layout,
including relative imports and package initializers. Imported top-level call
links are conservative: ambiguous names, captures, redefinitions and known
module mutations stay gaps. The graph does not perform full Python runtime dispatch.

For JavaScript/TypeScript, optionally install the tested parser versions:

```sh
python -m pip install -r PATH_TO_ELEVENPOWERS/requirements-impact.txt
```

Relative imports, barrels, CommonJS and uniquely declared workspace package
entries are supported, including `.mts`/`.cts` and JS-extension substitution.
Missing grammars, syntax errors, unresolved aliases, package export maps and
other language adapters are explicit gaps in the lightweight default. For more
precise TypeScript resolution, explicitly select the optional compiler below.
Framework-specific route/ORM extraction remains future work. There is no
regex-based inference of database or route behavior.

## Optional TypeScript compiler

Install TypeScript 5.7.3 into a tools directory with Node available, then supply
its compiler JavaScript path. Installation is explicit; queries never install it.

```sh
npm install --prefix TOOLS --ignore-scripts --no-audit --no-fund typescript@5.7.3
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . src/session.ts --typescript TOOLS/node_modules/typescript/lib/typescript.js
```

The compiler is trusted executable code. The adapter's virtual filesystem exposes
selected source/config bytes and executes no project source or executable config.
TypeScript supplies root `tsconfig.json` resolution, paths, package exports,
barrels, namespaces and concrete imported function/static-method relationships.
`--tsconfig configs/tsconfig.json` selects another relative JSON config. All
selected code remains in scope; tsconfig inclusion is not a substitute for the
repository scanner. Project references are not separate compiler programs.
Instance dispatch, external libraries, unresolved calls, rebound symbols and
parse/config errors remain gaps. This analysis is not a type-check receipt.

Only compiler 5.7.3 is currently qualified. Missing Node/engines, other versions,
5,000 inputs, 32 MiB payload, 20,000 symbols, 50,000 edges or the shared deadline
produce an explicit incomplete result. The standard-library/tree-sitter default
remains available without the compiler. See [producer provenance](../docs/research/impact-producers.md).

## Declare non-import contracts

Commit an optional `impactgraph.json` in the target project. It is discovered on
each query, under the same selection policy as source. An edge points from a
dependent to a dependency. Logical nodes can have an optional selected file anchor.

```json
{
  "schema": 1,
  "nodes": [
    {"id": "route:login", "kind": "route", "label": "POST /login", "path": "api.py"},
    {"id": "database:sessions", "kind": "database", "label": "sessions"}
  ],
  "edges": [
    {"source": "route:login", "target": "file:api.py", "kind": "uses"},
    {"source": "file:session.py", "target": "database:sessions", "kind": "depends_on"},
    {"source": "file:tests/test_session.py", "target": "file:session.py", "kind": "tests"}
  ]
}
```

Node kinds: `component`, `route`, `database`, `config`, `infrastructure`, `test`.
Declared edge kinds: `depends_on`, `uses`, `tests`. Node IDs must be unique,
namespaced and not use reserved `file:`/`symbol:` prefixes. All endpoints must
exist in the graph. Declared paths must be readable selected inputs; linked,
missing or out-of-scope anchors are rejected. Invalid maps are rejected atomically.
These are project assertions, not observed or independently attested contracts.

## Import current runtime/test observations

Export the source fingerprint using `--graph`. An external adapter can produce
the following bounded schema-1 JSON; explicitly pass it with `--observations`.
Use an ignored `.elevenpowers/` file to keep observations outside source inputs.

```json
{
  "schema": 1,
  "producer": "my-coverage-adapter 1.0",
  "run": "local-run-2026-10-04",
  "complete": true,
  "source_fingerprint": "COPY_THE_64_CHARACTER_SOURCE_FINGERPRINT_FROM_THE_GRAPH",
  "edges": [
    {"source": "file:tests/test_session.py", "target": "file:session.py", "kind": "observed_test"}
  ]
}
```

```sh
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . --graph --output graph.txt
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . session.py --observations .elevenpowers/impact-observations.json
```

The artifact path must remain inside the project and not traverse linked parents
or nested repositories. The chosen artifact is excluded from the source
fingerprint. Only `observed_call` and `observed_test` edges are imported. Current
complete source/declaration coverage, exact fingerprint, complete execution,
producer/run identity and valid endpoints are required. Source/map/selection
changes quarantine the old artifact instead of converting it into current evidence.
Malformed, missing and incomplete artifacts remain visible as issues.

This interface is a local unsigned relationship import. A producer label is not
authentication, an observed test relationship does not establish assertions, and
OpenTelemetry conversion remains planned. Actual Python/Node coverage conversion
is available through the explicit offline command below.

## Convert actual coverage

Collect coverage and a receipt in a separate explicit test run. Conversion reads
that evidence; it launches no tests, host or compiler. It supports coverage.py
7.10.7 JSON format 3 with `--show-contexts`, and Node 22.x native V8 coverage
(local producer acceptance: 22.17.1). Contextless Python data cannot establish
which test executed source. Node must have one caller-declared isolated test
file; transformed scripts and source maps are rejected as incomplete.

```sh
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact_capture.py --project . --kind python --report COVERAGE.json --receipt RECEIPT.json --output .elevenpowers/observed.json
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . src/session.py --observations .elevenpowers/observed.json
```

Use `--kind v8` for a V8 report. The receipt is a schema-1 JSON object with
`producer`, `run`, `execution: "complete"`, integer `exit_code: 0`, counted
`passed > 0`, `failed: 0`, identical `before`/`after` source fingerprints from
`build(project).fingerprint`, and `report_sha256` of the raw report bytes. Python
also requires `contexts`, an explicit nonempty context-to-relative-test-path
mapping; Node requires `test`, the isolated relative test path. Empty/global
contexts and unsupported producer versions cannot invent attribution.

The source fingerprint must be captured before and after the actual test run,
with producer outputs outside selected source. The converter reads current
inputs again before accepting observations. A receipt and its context mapping
are unsigned caller assertions, not authentication of a fabricated report.
Executed source is not proof that a test asserts that behavior.

Store project output under `.elevenpowers/`; other in-project destinations are
refused to preserve input identity. External output is allowed. Export refuses
overwrite without `--force`. Reads are bounded to 8 MiB for the report, 1 MiB
for the receipt, 500,000 line/range entries and the shared 0–300 second deadline.
Complete input/declaration coverage is required. Static parser/dispatch gaps can
coexist with a current observation, and remain visible in the whole query.
Stale, unread, invalid, incomplete or unattributed captures yield no active edges.
Exit 0 means a complete conversion, 1 an exported incomplete conversion, and 2
an invocation/export failure. The retained [actual producer example](../results/impact-acceptance/README.md)
shows Jinja's fixture-dependent nodes test recovered this way.

## History, output and bounds

```sh
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . session.py --history 30
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . session.py --json --output impact.txt
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . session.py --seconds 10 --max-depth 4 --max-results 50 --check
```

History is opt-in and reads only file lists/commit IDs. Co-change appears in a
separate section and never propagates as a dependency. Requested history is a
bounded recent sample; truncation, unavailable Git and commits with more than
40 selected files are visible. There is no ownership or author-data inference.

Reports group direct, transitive, declared and observed witnesses. They include
the path and source line for each edge, source fingerprint, quarantined inputs,
candidate tests and coverage issues. These labels describe evidence; they are
not calibrated HIGH/MEDIUM/LOW breakage probabilities. A test import suggests a
check to run; it is not a passing test or proof that its assertions are sufficient.

### Python dynamic imports, fixtures and recommendation tiers

Literal `importlib.import_module("package.module")` calls are recognized through
qualified import aliases. Literal relative names need a literal package anchor.
Rebinding, shadowing, mutation, ambiguous selected module roots and computed
names remain coverage gaps. Target modules are never imported or executed.
Enclosing top-level functions retain call witnesses; class attribute setup does
not remove an otherwise unique class export.

The source-only pytest adapter recognizes default `test_*.py`/`*_test.py` files,
top-level tests and supported `Test*` methods, local and ancestor `conftest.py`
fixtures, fixture chains, nearest-scope overrides, autouse and literal
`usefixtures` marks. Direct parametrized values are distinguished from indirect
fixture requests. Fixture bindings belong to each requesting test context, so
a local override or direct value cannot leak into another test's path.
Plugins, custom collection, imported/assigned registrations, class fixtures,
inheritance and dynamic requests remain explicit limits. The runtime does not
depend on pytest; actual pytest introspection and tests qualify the adapter.

JSON retains the existing conservative `tests` list and adds `test_selection`:

| Group | Meaning |
|---|---|
| `focused` | One file recommendation with a continuous qualified call, literal-import, fixture, declared or observed witness |
| `fallback` | Broader test candidates, including import and file-membership relationships |
| `support` | Non-collectable supporting Python files such as `conftest.py` |

An independent traversal preserves a stronger, longer witness even when a
shorter import path also exists. A function body's aggregate file edge cannot
stand in for an actual test/function call. Markdown displays all three groups.
Each group is deduplicated by file; the legacy list can still contain multiple
nodes in a file. Query depth/result/traversal caps remain visible. The explicit
`safe_to_exclude_fallback: false` means a focused list is a prioritization aid,
never permission to skip fallback, support or full verification. Source paths
are possible dependencies; they do not prove execution or assertion coverage.

Symbol queries can narrow the requested input:

```bash
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_impact.py --project . 'symbol:src/session.py#SessionManager' --max-depth 20 --json
```

The [frozen relevance results](../results/impact-relevance/README.md) retain old,
intermediate and final outcomes, a separately withdrawn reference, and actual
fault/control execution. Automatic advisories and subprocess-to-source
relationships remain unfinished.

Queries rebuild automatically from current bytes, including dirty edits,
additions, removals, renames and project policy/map changes. No index setup or
cache invalidation command is needed. Scans respect Git ignores, generated and
nested repository boundaries, project exclusions and file/byte budgets. Project
Git fsmonitor commands are disabled. No project state is written; temporary
process capture for history is removed. Exports require explicit `--output` and
refuse overwrite unless `--force` is supplied. Prefer a non-source output suffix
or ignored destination so a saved report does not become its own next input.

Defaults: 30 seconds, project scan budgets (20,000 files/256 MiB otherwise),
4 MiB per source/explicit input, 10,000 rows per declaration/observation list,
50,000 graph edges, six hops and 100 query results. `--max-files`/`--max-bytes`
must be positive; `--seconds` accepts finite 0–300; depth is 1–20, results 1–1,000,
history 0–200. History accepts at most 2 MiB of output and 10,000 associations;
the shared process runner separately caps temporary capture at 8 MiB. Native
filesystem/parser calls and process output polling are cooperative limits,
not an OS resource boundary or atomic filesystem snapshot.

Exit 0 means a report was produced, including qualified gaps. `--check` exits 1
for incomplete requested coverage. Invalid invocation/export failure exits 2.
Complete means within the selected inputs, supported adapters and budgets,
not exhaustive semantic knowledge or a safety certificate.

## Python API and remaining work

```python
from pathlib import Path
from core.impact import analyze, build

graph = build(Path('.'), seconds=30)
report = analyze(graph, ['src/auth/session.py'], max_depth=6, max_results=100)
portable_snapshot = graph.to_dict()
```

Existing runtime gates and radius hints remain unchanged. The initial graph is
an explicit CLI/API capability shared by all hosts. Automatic hook queries wait
for measured relevance/noise/overhead, especially on larger projects. Later
adapters can add precise type/call resolution, framework contracts, CI provenance,
traces and test coverage to the same graph. PatchProof/OpenCodeMap/TestMiner remain
separate unfinished features.

See the [design](../docs/design/impact-graph.md),
[delivery checks](../docs/validation/2026-10-04-impact-graph.md) and
[journey](../journey/60-an-impact-path-needs-a-reason.md).
