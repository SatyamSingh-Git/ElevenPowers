# 52 — Tests that notice a change

The user approved generalized test-strength analysis and asked for 25 meaningful
pushes as work became ready. The earlier ten onboarding and fifteen report pushes
were completed deliveries, so this feature started from the portable report head.
Parts 1–20 were published during implementation, rather than reconstructed at the
end. No project name or absolute acceptance path enters runtime policy.

B7 had earned mutation detection a place, while B8 had shown that handing exact
survivors to an agent encourages tests aimed at the list. The product therefore
borrows mutation operators and saves human observations. It does not add a new
completion gate, infer properties or ask a model to generate tests.

The engines were executed before their APIs were wrapped. Cosmic Ray 8.7.0 generated
real comparison/number mutations on Windows. Stryker instrumenter 9.5.1 emitted
zero-based replacement locations for JavaScript and TypeScript. Its first probe
used the factory with a logger instead of an injector and failed immediately;
the observed constructor/API then produced the expected mutations. These are
optional installed dependencies, not vendored engines or runtime downloads.

Shared code selects changed production files against a base, respects ignores and
boundaries, copies inputs under limits, requires positive passing tests, caps
attempts and elapsed time, and saves metadata per attempt. Weak tests left changes
undetected; boundary assertions detected them in actual unrelated Python, Node and
TypeScript project fixtures. Deleted tracked files exposed a copy bug: Git's index
still listed absent files. The copy was corrected to preserve current absence.

The one fresh reviewer found three Important defects, all reproduced before repair.
`dependencies: null` or a number raised TypeError instead of staying advisory.
A marker created by baseline tests made a harmless later mutation fail. An editable
Python `.pth` imported original source, so a copied mutation appeared undetected.
The corrections validate containers first, start every test from pristine inputs,
and reject known original-source Python import/read redirection. Those controls
failed first and passed after repair; the corrected full suite is the release gate.

The portable report reads saved results and checks input freshness; it never starts
analysis. It includes counts, paths, operators and lines, not replacement source
or captured output. Automatic agent feedback does not expose individual mutants.

What remains bounded: whole changed-file scope, sampled operators, possible
equivalent behavior, optional setup, unsupported Python startup overrides and
filesystem rather than OS security isolation. Large dependency copies and long CI
need a focused command or yield explicit incompleteness. These results establish
the mechanism on controlled projects, not better production patches or native
installed-session acceptance in the four added hosts. The dated validation record
contains exact suite, architecture, publication and remote checks.
