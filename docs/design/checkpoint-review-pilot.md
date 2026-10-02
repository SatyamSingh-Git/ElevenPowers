# A fixed-patch test-quality pilot

Approved scope, 2026-10-02: compare ordinary review and ElevenPowers-assisted
review from identical saved production and test inputs. A retained no-review
checkpoint supplies the third comparison. This first component experiment asks
whether review adds useful behavioral tests; it does not estimate production
repair rate, general coding quality or performance.

The four cases are selected before review from archived upstream patches:
ItsDangerous `6c58e969`, Click `ad39d749`, Jinja2 `065334d1`, and attrs
`97f8d175`. The last is a preservation control whose historical changed-line
sample had no survivors. These are deliberately selected real Python projects,
not a representative or random project sample. Environment qualification is
free, includes the whole ordinary suite without deselection, and retains failed
qualification records. A failed qualification receives no model call.

Each eligible case receives one ordinary review and one assisted review, in
alternating order. At most eight subscription calls use Claude Sonnet 5 at
medium effort, with 480 seconds per call, no API fallback and no favorable
retries. Only new `tests/**/test_*.py` files may be submitted. Existing source,
tests, configuration and documentation are sealed and checked independently.
Scope violations remain unqualified rather than being silently repaired.

Before review, the shipping Cosmic Ray adapter samples changed production
files with 180 seconds, 32 attempts and 30 seconds per test command. The first
free whole-suite audit is retained: it supplied a lead on one case, no lead on
one and timed-out baselines on two. Before any review call, a second free
analysis uses the relevant existing public test module for each case (timed
serialization, CLI testing, template security, annotations). This supported
focused-command setting is the frozen treatment; final grading retains the
full ordinary suite. No case is replaced based on analysis results. Its
observations are summarized as function-level leads, with explicit incomplete
coverage and possible equivalence. Mutation identities, operators, replacements
and final fault fixtures are withheld. This is an explicit experimental consumer
of the shipping analysis, not installed-session or automatic feedback evidence.
The analysis cost is separate from the equal review-call time caps.

Final checks freeze the historical changed-line fault sample and a cosmetic
AST-formatting control before model calls. Both reviewers are judged against the
same fixtures, from fresh private copies, using the full suite. Only an actual
test failure counts as detection; collection/setup failure, empty execution,
timeouts and exhausted output bounds remain separate. Meaningfulness labels
from the prior blinded audit are retained where available, and unlabeled or
equivalent changes cannot establish behavioral improvement. Added tests also
need inspection for source-spelling assertions, instrumentation tricks and
unsupported behavioral contracts. A formatting control is useful evidence,
not proof against every form of brittle test.

Review workspaces omit upstream Git history and evaluator fixtures. Prompts
forbid external answer retrieval. Ordinary native CLI tools can access beyond
the workspace, so this is not an operating-system exposure boundary; that
limitation qualifies every causal interpretation. Subscription host settings
and host-managed settings may also affect both arms. The installed CLI's safe
mode disables ordinary customizations and plugins equally in both review arms;
it is compatible with subscription authentication, unlike `--bare`.

Built on: upstream BSD-3-Clause Pallets and MIT attrs source patches and test suites; the prior
B7 research fault sample and blinded labels; Cosmic Ray 8.7.0 (MIT)
through `core.strength`; and this repository's subscription authentication and
contained process helpers. The added piece is a bounded review comparison with
immutable starting inputs, withheld grading fixtures and explicit failure
states. The historical mutation generator remains a research fixture producer
and is not imported into `core` or the reusable evaluation helpers.

Publish every attempted slot, including failures and unchanged outcomes. Report
per-case detection gains, regressions, preservation-control behavior, review
time and analysis overhead. Any positive result supports only the bounded
test-quality intervention that was actually measured.
