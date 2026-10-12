# 74 — A contract needs a producer

2026-10-12

PatchProof could identify a patch and associate ordinary receipts. It still had
no applicable API compatibility observation. We added one narrow producer-backed
property: backward compatibility of a project-declared standalone OpenAPI file.
Language and host are irrelevant to that declaration; actual API implementation
behavior remains a different question.

We borrowed oasdiff rather than implementing another schema-diff engine. Running
the real producer first changed the design: its breaking command could call an
invalid document an endpoint removal. Validation must precede compatibility.
Both specifications now pass validation at WARN before comparison at ERR.

Implicit configuration was another input. An empty private config and stripped
environment overrides make the policy explicit; external references are disabled
because otherwise a two-file receipt could depend on unrecorded remote contents.
The executable version and bytes are recorded alongside the Git inputs and policy.

Reporting only reads saved observations. A contract result, its execution,
freshness and requested-patch association remain separate. A changed spec, engine,
declaration or range cannot reuse the old association. Unknown/corrupt history
does not become an absent green check. Nothing upgrades a spec comparison into
proof of deployed behavior or agent coding improvement.

The first cross-project exercise also exposed an overly broad directory rule:
an ancestor Git repository rejected otherwise disposable scratch. Each project
now initializes its own fresh Git boundary, and every mutation names that root.
No caller-specific directory exception was introduced.

The model-free exercise uses unrelated JSON/Python and YAML/JavaScript projects
and distinguishes current, failed, incomplete, stale and absent observations.
Review and full qualification are recorded in the dated validation as they finish.
The fresh review then exposed what the producer alone did not qualify: duplicate
JSON names could hide paths, and dynamic schema references could pass without
observed external inputs. Strict JSON names and a producer-derived structural
guard now leave those inputs incomplete. Original bytes remain the comparison
inputs. Malformed receipt shapes and deep JSON now preserve controlled errors;
older policy observations are retained but stale. All three findings were
witnessed before repair, and no second reviewer was dispatched.
See [guide](../the-guide/contracts.md), [design](../docs/design/patchproof-openapi.md)
and [validation](../docs/validation/2026-10-12-patchproof-openapi.md).
