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
other language adapters are explicit gaps. JS/TS calls, tsconfig path mappings,
conditional package exports and framework-specific route/ORM extraction remain
future adapters. There is no regex-based inference of database or route behavior.

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
the first delivery has no built-in OpenTelemetry or coverage-file converter.

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
