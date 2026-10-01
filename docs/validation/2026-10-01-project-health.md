# Generalized project-health validation — 2026-10-01

Scope: fresh read-only staged health, automatic bounded private native
observations/timing, and explicit disposable native acceptance across Claude,
Codex, Gemini, Cursor and Copilot. Runtime has no Snag-specific paths, commands
or policy. Spec: [project health](../design/project-health.md).
Plan: [delivery steps](../superpowers/plans/2026-10-01-project-health.md).

## Environment and evidence

Windows, Python 3.13.2 in the existing virtual environment, Node 22.17.1 and Git.
The environment was placed first on PATH. Tests requiring previous owner temp/
cache directories used the authorized account. No package was installed and no
model session or paid sweep was launched. Optional engines were already
present from the previous delivery; health only inspects their metadata.

| Check | Observed result |
|---|---|
| Native phase/receipt and staged health controls | RED before implementation; current combined group below includes them |
| Optional environment metadata | Two missing-behavior controls RED→GREEN |
| Disposable preparation | Real unittest and Node producers fail, source correction passes; no activation |
| Acceptance qualification | Seven new inspection controls RED→GREEN; 10 acceptance controls initially pass |
| Doctor CLI, acceptance, host doctor | 29 pass after CLI implementation |
| Five launchers × two languages | 10 pass in 59.82 seconds; real failure, pass, timeout, stale/rerun and completion |
| Read ordering/budget/state/timing boundaries | Four controls RED→GREEN; scan-limit control already passed |
| Independent-review reproductions | All five RED→GREEN |
| Corrected focused health/CLI/acceptance/report/host group | 67 pass in 132.74 seconds |
| Full suite before five review corrections | 1,189 pass, 28 skip in 814.34 seconds; this is not the corrected-suite result |
| Corrected full suite | 1,194 pass, 28 skip in 691.95 seconds, exit 0 |
| Required audit probes | 104 pass in 146.51 seconds |
| Grader | Four known cases classified correctly: resolved, regressed, unfixed, setup |
| Launcher doctor | All reported checks pass, including success/failure/completion/blocking; replay only |
| Standard-library runtime | `python -S` imports health, acceptance, strength and exporter successfully |
| Installed Claude Code 2.1.286, no model prompt | Disposable exercise processed SessionStart; startup observed, pipeline/acceptance waiting and task UNVERIFIED |
| Architecture | `check.py --render`: 95 nodes, 216 edges, seven planes; all four tabs draw |

The focused command is in [development](../development.md). Full-suite and skip
counts describe this environment only. Timings are measurements of retained
samples and these checks, not a product speed improvement or latency guarantee.

## Fresh-review corrections

The fresh reviewer covered the whole runtime range from `5b245f9` through
`05f429e`. Five Important findings were verified before the one correction pass:

1. Mixed verbose pytest failure could be replaced by a passing individual test
   sharing its timestamp. Health now selects declared command-level aggregates;
   conservative equal-time ordering cannot hide incomplete/failing execution.
2. Malformed pending patch records caused an uncaught AttributeError during the
   final edit coverage read. They now return actionable incomplete diagnostics.
3. Tolerant runtime config loading silently defaulted malformed saved JSON.
   Health now validates a bounded saved configuration before using the loader.
4. An unrelated successful phase hid an unresolved current-session error.
   Same-phase recovery is required; historical failures remain diagnostic.
5. An exercise contract changed after the nested health read but acceptance still
   passed. Bounded contract fingerprints and native observations are rechecked
   before returning. This does not add a second repository source scan.

All five tests are in `tests/test_health_review.py`. No Minor findings were
deferred. Corrected runtime was published in `cf174d0` (part 13).

## Native-session and reporting limits

Version-only probes found Claude Code 2.1.286 and Codex CLI 0.159.2. Gemini,
Cursor and Copilot executables were unavailable. A real installed Claude 2.1.286
session in `.venv/project-health-acceptance/claude-python` processed one SessionStart
without submitting a model prompt. Its retained callback sample was 117.32 ms;
this measures handler plus initial diagnostic write, excluding launcher/host
startup and final registry write. Browser access was explicitly declined.
Readiness correctly reports startup observed, pipeline waiting and task UNVERIFIED;
acceptance remains waiting. Ten real producer/launcher contract cases are separate
from this installed startup. Full versioned exercises remain unverified on all
five hosts; no model-dependent exercise or paid evaluation was run.

Preparation creates only a new explicit destination, with no host launch or
package download. Existing or linked destinations are refused. Inspection needs
immutable tests/configuration/wiring, current generation/task/session, all three
outcomes and current fresh completion. Operator versions and local callbacks are
unsigned metadata. Current freshness is checked; the earlier manual stale-view
step is not independently attested. Acceptance does not certify production
correctness, all side effects or compatibility with another installed version.

## Delivery decisions

The user approved the milestone before the saved design was written, so execution
continued inline from that approval. A clean feature branch reused the current
checkout/environment instead of a separate worktree. Missing attribution after a
current startup conservatively qualifies health until phase recovery. Paid or
unavailable installed-host exercises remain unverified, and runtime review does
not substitute for the executor's separate documentation/render/link checks.

## Incremental publication

Seventeen actual publication parts: plan; bounded observations; report identity/
timings; shared health; diagnostic safety; readiness CLI; engine metadata;
preparation; acceptance inspection; doctor CLI; real five-launcher producers;
boundary corrections; independent-review fixes; rendered architecture; six
guides; status/roadmap/journey/validation; README/provenance/final results and main.
Each part has a descriptive commit; no empty count-padding commits are used.
Final local checks are recorded above. The main workflow publishes Windows/Linux
and Python 3.11/3.13 checks for the final commit; its exact-head result is reported
in the delivery handoff and available in GitHub Actions. An older green badge
does not establish the result for a newer publication.
