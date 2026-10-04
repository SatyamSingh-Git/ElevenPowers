# A focused list still needs its fallback

The previous real-project graph missed the process-output test through a literal
`importlib.import_module` and Jinja's nodes test through an ancestor environment
fixture. Both versions caught five of six qualified faults. The next work was
to repair those relationships and make suggestions more specific, for any
project using ElevenPowers.

Before the runtime changed, twelve symbol queries were frozen against the same
ElevenPowers and Jinja pins. Six development and six held-out cases use disjoint
relationship families. The author can read their definitions; they are authored
partial references, not blinded representative ground truth. The old runtime
was archived first. Every intermediate result remains available.

Actual importlib resolution and pytest fixture introspection came before the
adapter. Literal imports need qualified aliases and selected unique roots.
Fixture requests follow local/ancestor visibility, override chains, autouse and
literal marks. Direct parametrized values cannot become fixtures. Each test
gets its own context binding: sibling overrides and one test's direct parameter
must not leak through a shared fixture into another test.

Jinja exposed another binding mistake. Assigning
`Environment.template_class` was treated as rebinding the class name, removing
its symbol. Actual name bindings now differ from attribute mutations for class
export identity. Function implementation mutation still invalidates a qualified
function. Unsupported registration or dispatch remains a gap.

The corpus also contained an author error. The pinned process module and its
test do not use redaction, although the new scrub case labelled them as a
consumer and test. The frozen corpus was not rewritten. A separate
corpus/source-bound withdrawal excludes the mistaken labels equally for both
versions. Twelve valid test references remain: old recovery is 4/12; repaired
recovery is 11/12. Development improves 2/6 to 6/6, held out 2/6 to 5/6. The
remaining held-out miss crosses a subprocess CLI boundary. The reused previous
corpus improves from 23/26 to 24/26 tests while retaining 31/31 consumers.

Specificity needs a separate traversal. A shorter import path must not hide a
longer call/fixture witness. The report now partitions recommendations into
focused files, broader fallbacks and supporting files, preserving the complete
legacy list. Six of the twelve valid references are focused. For Jinja's
ChoiceLoader and PrefixLoader queries, one focused file sits beside 23 fallback
files and one support file. That helps choose a first check; it cannot establish
that the other tests are safe to omit.

Three real unchanged/comment/fault controls used sealed disposable source.
The first classifier qualified two; repaired recommendations detected both
while old recommendations detected neither. The Environment fault caused 20
assertion failures, but pytest omitted `AssertionError:` from some rewritten
assertion messages. The evaluator had mistaken those actual assertions for
unknown errors. A numeric actual pytest assertion reproduced the defect; the
first string-valued control unexpectedly passed and was retained as an
insufficient reproduction. Runtime errors mentioning assertions still fail
qualification.

A separate regrade verifies raw report/output hashes and historical source
seals before classifying the same producer artifacts. It preserves the original
controller identity and grades, records the new classifier, and runs no tests.
All three faults then qualify, detected 3/3 repaired versus 0/3 old. The process
fault is reused regression evidence; the environment/fixture faults are newly
authored. This demonstrates better test recommendations under these conditions.
It does not demonstrate better agent-written code or universal safety.

Three descriptive build samples ranged 3.763–5.649 seconds on the pinned
ElevenPowers input and 0.828–2.193 seconds on Jinja. They ran on one Windows
machine under ordinary concurrent load. Query/end-to-end/native overhead was
not separately sampled. Automatic hooks still need noise and cost acceptance;
plugin collection, subprocess boundaries, frameworks, live traces and source
maps remain contributor work.

The final independent review found four correctness defects: class-assigned
marks were omitted; wildcard/re-exported fixtures could fall through to an
ancestor; a valid indirect override chain was called cyclic; and default-time
rebinding or attribute-container mutation could leave a literal import wrongly
qualified. Nine parent controls reproduced them RED, then 149 integrated
controls passed after repair. Six fresh real pytest counterparts agreed with
the repaired graph. Post-review frozen reads preserve the measured recovery.
A comprehension-scope ranking issue remains Minor and deferred: the file stays
in fallback. Earlier graphs and producer grades are retained, not replaced by
the reviewed runtime.

See [all outcomes and reproduction](../results/impact-relevance/README.md),
[the guide](../the-guide/impactgraph.md) and
[delivery checks](../docs/validation/2026-10-04-impact-relevance.md).
