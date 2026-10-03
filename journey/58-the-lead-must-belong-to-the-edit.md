# 58 — The lead must belong to the edit

The fixed-patch review gave a useful result and a clear failure in the analysis.
Both reviewers improved Jinja2's test sensitivity by five meaningful faults;
ElevenPowers supplied no additional improvement. Its bounded whole-file sample
never reached the function the patch changed. Giving a reviewer a survivor in
an earlier unrelated function was a poor use of the analysis budget.

The next build therefore changed selection for every repository using the tool.
Git supplies current changed-line hunks. The installed Cosmic Ray and Stryker
parsers/operators remain the mutation producers. Function spans relate those
positions to the edit; module-only changes stay within changed lines. Actual
changed-line candidates precede other candidates in the enclosing function.
Small samples rotate across files and functions, and language shares follow
selected file counts. Reports distinguish edited lines from enclosing-function
context and qualify the one command that was measured.

Independent review found why that description needed adversarial controls. A
new file arrives as one large hunk; selecting only a function that enclosed the
whole hunk assigned every candidate to `module` and hid later functions. A nested
JavaScript edit admitted a mutation replacing the outer function because the
spans merely overlapped. Broad hunks now partition by function and each mutation's
complete span must fit its selected target. One Python file also took turns owed
to three JavaScript files. Weighted allocation and real mixed-project controls
now give each file a turn when the budget can cover them.

Deletion needed two kinds of honesty. A deleted line has current neighboring
context, but removed behavior cannot be mutated in the current tree. Entire
deleted production files disappeared from the old selection altogether. Their
coverage limitation now remains explicit. It must not suppress available changed
source: analysis can run on current files and still finish incomplete about the
removed behavior. Selected bytes changing before the private snapshot likewise
prevent stale attribution. Legacy records stay readable without relabeling them
as targeted samples. Human reports retain complete line ranges.

A real guard probe found a separate restoration-variable error: saved source
bytes had overwritten the original-project path used by the Python read guard
during mutation attempts. The baseline was guarded, attempts were not. The path
now survives forwarding, with legitimate private-read and forbidden-original-read
controls seen failing and passing. Earlier analysis is retained with that limit;
a private copy and diagnostic read guard still do not establish an OS sandbox.

The free upstream check now reaches what the previous sample missed. Under an
eight-candidate cap, the old Jinja2 sample had zero candidates in `do_attr`; all
four applicable targeted candidates belong there. attrs moved from eight earlier
`attrib` candidates to eight in edited `_is_class_var`. Focused execution then
completed four Jinja2 attempts (one detected, three undetected), and eight attrs
attempts (five detected, three undetected). Those survivors are possibilities
for that command, not established defects or a whole-suite verdict. Click's final
bounded baseline timed out, and the artifact keeps that result. These are gains
in analysis relevance, not evidence of an added coding-quality advantage.

The previously stopped regrade also finished: twelve grade sets, nine exact
matches. Click F03 combines actual failures and 1,049 setup errors in all three
arms. The corrected evaluator retains setup, yielding 2/8 plus one setup result
instead of the historical 3/8. Original grades and producer hashes stay frozen;
the separate reproduction contains every current grade and correction. Jinja2's
five-fault improvement in both arms and the four tied pairs remain unchanged.

No new model sessions ran. The next proof requires held-out active behavioral
gaps, equally funded ordinary review, independent behavior checks and equivalent
controls. Any engaged mechanism can count; task size is not the criterion.
The product must show a measured improvement beyond that comparison before
claiming it makes coding better.

See the [dated evidence](../docs/validation/2026-10-03-strength-regions.md),
[engine provenance](../docs/research/mutation-engines.md),
[commands](../the-guide/commands.md#ep_strength--inspect-changed-code-test-strength)
and [current plan](../PLAN.md).
