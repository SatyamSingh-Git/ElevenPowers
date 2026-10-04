# ImpactGraph: dynamic imports, fixtures and focused test candidates

Authorized 2026-10-04: repair the missed dynamic-import and pytest fixture
relationships, then make test recommendations more specific. This is an
extension of the existing read-only graph and report; no new automatic hook,
test execution during queries, model session or project-specific rule.

The prior graph found 31/31 known consumers and 23/26 known test references,
but both versions detected only 5/6 qualified faults. The process-output fault
was missed through `importlib.import_module`; Jinja's nodes test depends on
the `env` fixture in an ancestor `conftest.py`. New cases must be frozen before
the runtime repairs. Reused misses remain regression evidence, not new held-out
acceptance or evidence of improved agent patches.

## Existing paths to extend

Use Python's standard-library AST and unique selected module index. Recognize
literal `importlib.import_module` calls through proven ordinary import aliases;
absolute names and literal relative-package anchors have the documented Python
semantics. Unknown expressions, starred/duplicate arguments, local module
collisions, mutated/shadowed aliases and unavailable roots remain explicit gaps.
Never import target source. A literal import is a possible dependency, not proof
that the call executed. Add enclosing-function witnesses while retaining
conservative file relationships.

Resolve supported pytest fixture declarations from established pytest import
bindings, function arguments and literal fixture marks. Local fixtures and
ancestor conftest scopes have nearest-scope precedence. Fixture dependencies,
autouse and literal usefixtures marks add explained paths. Parameters supplied
directly by parametrize are not fixture requests. Dynamic registrations,
plugin loading, unresolved fixture requests and unsupported override/collection
forms remain gaps, never guessed name matches. Read selected source only.

Keep `tests` as the complete conservative candidate set. Add a bounded
`test_selection` partition: focused witnesses have a continuous call, literal
import, fixture, declared or observed path; ordinary import/file-membership
paths remain broader fallback candidates. Compute focused paths independently
so a shorter broad path cannot hide a longer specific witness. Deduplicate
recommendations by file, retain both groups and explain that focused candidates
are not assertion coverage or safe test exclusion. CLI Markdown shows both.

Fixture dependencies are bound to requesting contexts. Context instances point
to the canonical definition and to context-resolved dependencies; a shared
fixture depending on a locally overridden fixture cannot leak that override
into sibling test scopes. Unknown class registrations and imports stay gaps.

## Frozen evaluation and delivery

Preserve runtime f31f6a2 as the old version. Freeze twelve new authored queries
across the same pinned Python repositories, using symbol queries here and
file queries in the reused prior corpus,
six development and six held out by relationship family. Source hashes and
known references are evaluator-owned. The known process/nodes misses and prior
24 cases are separately reused regression data. Extra candidates remain unknown
under the partial oracle. Record focused/fallback breadth, known-reference
recall, negative hits, independent faults and bounded read samples.

Execute actual pytest fixture introspection before implementing its semantics.
Validate new fixture and literal-import faults with unchanged/comment controls
and independent actual pytest assertions in disposable inputs. Preserve every
attempt, code identity and before/after seal. A narrower suggestion is useful
only alongside its retained fallback; never credit a smaller set as speedup
without equal-scope independent execution. Automatic advisories remain pending
until detection, specificity and installed-session cost are qualified.

Run focused controls after each repair and full regression at final delivery,
with one independent whole-branch review. Update README, guide, plan, status,
journey, validation and every architecture view; render the map and check links.
Push completed parts continuously, then integrate the exact hosted Ubuntu/
Windows Python 3.11/3.13 verified head into the already authorized main branch.

Primary semantics: [Python importlib](https://docs.python.org/3/library/importlib.html),
[pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html).
Python AST/index extraction is reused from this repository; fixture semantics
follow pytest (MIT), without vendoring its implementation or importing it in
the runtime. This extension adds source-bound relationships and evidence tiers.
