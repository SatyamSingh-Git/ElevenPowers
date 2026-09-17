/* GENERATED - do not hand-edit.
 * Human-readable mirror of the GRAPH inlined in index.html, which is the live
 * source. Regenerate with:  python architecture/check.py
 */
window.ELEVENPOWERS_GRAPH = {
  "meta": {
    "updated": "2026-09-17",
    "changelog": "2026-09-17 (h) - parsers.py reads TAP, and reads it as a FORMAT rather than a tool. Found by pointing the runtime at a real repository outside this project: three of its four packages run node --test and the parsers produced ZERO records, so a passing run left no evidence and the default strict profile would refuse a stop on tested work. Both of Node's reporters are read, captured from 22.17.1 rather than remembered, and TAP is dispatched on the OUTPUT before the wrapper fallback - so npm test, yarn test, turbo test and pnpm -r test are counted though they name no runner at all. R10 reproduced on this runner: piped through tail it exits 0 with '# fail 1', so the count outranks the code. And the third part is the one that generalises beyond TAP: a test command this module cannot read now writes a blindspot instead of going silent - deno test and zig build test say so today. The both-ways guard was repaired while here: it hardcoded parser names, so a new parser could be added and the count would not move; it now derives them from whatever returns through _counts_decide, and was seen refusing a brand-new runner that had no table entry. | 2026-09-17 (g) - B5: the bypass fix watched working on live agents, not in a replay. The two tasks that bypassed in B4 were re-run twice each: the gate engaged 4 of 4 against 0 of 2, with src/jinja2/utils.py and src/attr/_make.py now in touched. The confound is excluded rather than assumed - ledger.guided is False on all four, and that flag is set only by the EDIT_TOOLS branch of on_post_tool, so no edit-tool event reached the runtime in any run. The agents wrote through the shell again and the claim opened solely because on_stop now asks the working tree first. $6.87. | 2026-09-17 (f) - atlas.py finally got the measurement 5.9 asks for and shipping did not wait for, and it splits the component in two. The neighbourhood brief fires on 47% of edited files against radius.py's 43%; the drift check fires on 0 of 23 real commits, because mature libraries add tests rather than modules and none of the corpus repositories keeps an architecture document. Silent by design, not broken - but the claim is narrowed in PLAN, the feature page and journey 37, which had recorded the gap rather than hiding it. No code changed: the measurement asked for an honest description, not a fix. | 2026-09-17 (e) - the 12.5% bypass is closed. on_stop now asks the working tree BEFORE concluding there is nothing to gate, and every changed path goes through observe_edit, which is the same rule a tool event uses rather than a second way in. The cause was never a missing tool name: jinja2-0cd69481 ran Bash with seen=0 and touched=0 and still shipped a 5,396-line patch, because agents write files through the shell and written_paths reads only some of those shapes - a syntax race nobody wins, against a working tree that already knows. The probe also caught a standing defect: _changed_paths returned .elevenpowers/ among the task's edits, so the runtime's own ledger had been scoring risk as the user's work, and once that list could open a claim it would have gated a session that changed nothing. | 2026-09-17 (d) - the map got 27 edges more detailed, and it did not get them by hand. core/atlas.py - the module built the day before to catch exactly this - was pointed at this repository and asked which real intra-repo imports the graph does not draw. It found 27 of 99: four inside core (doctor and status both write to blindspots, stress reads evidence and surface), three inside eval, and twenty from the eval plane into the runtime it reuses. Every one is a real import read out of the AST rather than a guess, which is the point: the graph is now checkable against the code by the same tool that checks any other repository's. | 2026-09-17 (c) - B4 took the measurement this whole layer exists for, and it is ZERO. 0 of 14 asked runs came back VACUOUS, against the literature's 46%, and B3's single case did not replicate on the other model - pooled 1 in 22. The frequency claim is withdrawn in PLAN 10; the mechanism is not, because it caught that one case and computes the failed_before 5.13 needs. Coverage 8 of 16 to 14 of 16 and named reproductions 0 of 8 to 5 of 14, which is what made the null readable rather than noise. And the finding that outranks it: 2 of 16 runs BYPASSED THE GATE ENTIRELY - jinja2-0cd69481 shipped a 5,396-line patch graded resolved with ledger.touched empty, so no claim opened and on_stop returned at its first line. Every rate here is conditioned on the gate having seen the work, at a measured 12.5% failure of that condition. | 2026-09-17 (b) - the last two gates that could lose a paid run. _passing required a FRESH passing record, so an edit landing after the tests staled every record and the whole check skipped - no verdict, no failed_before, no reproduction; it cost 2 of 16 B3 runs and is confirmed on click-9f9b149e, whose last passing record's tree is not the tree of its last record. Fresh or stale is now questioned, GONE still is not, and both directions have a probe. And the ledger now records the declared profile and commands, written for diagnosis and never read back, because the B3 bundles could not say which gate closed - the config lived only on disk in a workspace that no longer exists. | 2026-09-17 - stress.confirm closes the half of 5.13 that was left to chance. The reproduction obligation was being satisfied by the suite path on 7 of 7 measured runs and the named path on 0, so reproduced and discriminates were one base-tree run reported twice. Now the red-on-base node ids are run against the current tree: 0 of 16 rehearsed tasks reached a named reproduction before, 6 do now, and the 10 that do not are repos whose red tests are still red - pre-existing breakage the targeted check can tell apart and the suite grain never could. | 2026-09-16 (j) - eval/rehearse.py now drives the real hook instead of hand-building the ledger. It did not predict the missing base commit because it passed base and claims in itself, which tests that a correct ledger works rather than that the runtime builds a correct one. Seen to flip on the very task that lost the sweep: with the fix reverted it reports attrs-577c782c as base=NO and exits 1. | 2026-09-16 (i) - the base commit is now recorded when the TASK opens, not when a claim is inferred. A prompt stating no claim still opens a task, and Ledger.open_by_edit attaches feature_added at the first edit - that ledger carried no base, so stress had no old tree to build and the discrimination check silently never ran. It cost 37% of a paid sweep: 6 of 16 runs, and the correlation with 'claim opened by an edit' was 6 of 6. Where a base existed, stress ran on 8 of 10. Guarded so a later prompt cannot re-base a task mid-flight, which would compare the change against itself; both directions have a probe watched failing. | 2026-09-16 (h) - core/radius.py and core/atlas.py ship together, and they are the same argument applied twice: a rule the agent is asked to remember is soft policy that decays, so compute it instead. radius answers 'what else implements or calls what you just changed' from the diff and the AST; atlas answers 'does the map still describe the code, and do the docs still name files that exist' as a 1995 reflexion model over the committed architecture document. Both report and neither refuses. Both were wrong in ways their fixtures could not show and the real repositories did: radius found no bases at all on click because generic bases are ast.Subscript, then made a base class a sibling of its own subclass through Generic; atlas called radius.py documented because the design note proposing it mentioned it, so docs/design/ is now documentation but not the map. The report also stopped naming tests/test_mypy.yml as the test to run. | 2026-09-16 (g) - eval/rehearse.py: a pre-flight that seeds a real task, applies the gold patch and asks the runtime the sweep's question without paying for an agent. Written because a sweep ran two tasks for $1.42 and recorded discrimination={} on both - stress matched the declared command exactly, agents never type it, and the sizing step measured the wrong predicate. | 2026-09-16 (f) - stress.py now lays the task's new TEST files over the old source before running. Without it a test written after the fix is absent from the base worktree, so every check reports passed-before by construction - the sweep would have measured the harness, not the agent. Caught while sizing the sweep, before spending. | 2026-09-16 (e) - measuring the engagement rate before spending caught a design flaw: the computed reproduction keyed on node identities, and the parsers record nodes mainly when they FAIL - 1,256 failing test records against four passing across every preserved ledger - so it engaged on 1.4% of saved runs. Suites now count, which is what _demonstrated_fix always did. | 2026-09-16 (d) - eval/wheelhouse.py closes the registry answer key. PIP_NO_INDEX plus PIP_FIND_LINKS at a shelf of the backends the corpus declares, so an isolated build resolves locally while pip download click has nowhere to go. Both directions tested against real pip, plus the fail-safe: no shelf means the index is left alone rather than breaking every install. | 2026-09-16 (c) - C1: the reproduction obligation is now COMPUTED. It was satisfiable only if the agent happened to run the test red before writing the fix, which blocked anyone who wrote the test afterwards - ordinary practice. stress.py already builds a worktree at the base commit, so the same run now also reports which tests were already failing there. Collection errors match by file, because a test for behaviour the fix introduces cannot import on the old tree at all. | 2026-09-16 (b) - core/ratchet.py ships: the declared checks going green now commits the tree to a private ref, and the end report offers it back if a later edit moves off it. Cline's store and its compare-and-swap refusal when HEAD has moved; ours is only when to snapshot. PIP_NO_INDEX was tried and reverted the same hour - it closes the registry answer key and breaks pip install -e ., and no environment variable turns build isolation off. | 2026-09-16 - eval/canary.py: the exposure screen the boundary will be tested with. Finds 21 of 36 watchable runs handed the fix's own invented identifiers, against 2 for the sha screen, and names the channel - 14 upstream network, 4 the machine's own site-packages. The site-packages door is one --network none would NOT close, which corrects 4.1. | 2026-09-15 (c) - core/stress.py ships: the runtime now runs every declared check against a detached worktree at the task's base commit and reports the ones that would have passed anyway. PLAN 5.0 as a product feature rather than a development habit, at the user's direction. Reports, never refuses. | 2026-09-15 (b) - Phase B2 ran: eval/pool.py and eval/discriminate.py join the graph. The discrimination census found R10 - a passing suite record was decided by the exit code alone, and pytest piped to tail always exits 0, so 42% of preserved passing suite records say PASS while holding a non-zero failure count. Fixed in core/parsers.py with a probe watched flipping. The v0.8 workflow lane now marks P1 half built rather than planned. | 2026-09-15 - first graph. Built alongside Master Plan v0.8, which moved the project from asking whether evidence EXISTS and is CURRENT to asking whether it DISCRIMINATES, and from acting at Stop to acting where the premise is formed. Two nodes are drawn as they are today and are about to change: evidence.py already computes 'was this tree green, and is it still the same tree' on every edit and prints it as a complaint (Phase C0 keeps it as a snapshot), and obligations.py:149 collects the +28pp reproduction artifact as a receipt at Stop (Phase C1 derives it at the first edit).",
    "title": "ElevenPowers - System Topology"
  },
  "planes": {
    "host": {
      "label": "Claude Code \u00b7 the host",
      "color": "#a78bfa",
      "blurb": "the agent, and the hook events it emits"
    },
    "seam": {
      "label": "Plugin \u00b7 the seam",
      "color": "#f59e0b",
      "blurb": "plugin/ \u2014 where the host meets the runtime"
    },
    "runtime": {
      "label": "core/ \u00b7 the runtime",
      "color": "#10b981",
      "blurb": "evidence, obligations, ledger, verdict"
    },
    "state": {
      "label": ".elevenpowers/ \u00b7 state",
      "color": "#22d3ee",
      "blurb": "durable task state in the repo"
    },
    "eval": {
      "label": "eval/ \u00b7 the harness",
      "color": "#f472b6",
      "blurb": "mining, sweeps, grading, screening"
    },
    "bundles": {
      "label": "results/ \u00b7 preserved",
      "color": "#84cc16",
      "blurb": "runs that survive their workspace"
    },
    "external": {
      "label": "External",
      "color": "#94a3b8",
      "blurb": "git, pytest, the CLI under test, upstream"
    }
  },
  "nodes": [
    {
      "id": "agent",
      "plane": "host",
      "kind": "app",
      "size": 3,
      "label": "Claude Code agent",
      "desc": "The coding agent doing the work. It is never asked to cooperate: it runs its tests the way it always did, and the runtime reads the output. If it never emits a sentinel line or follows a protocol, the evidence is still there. This is the whole premise \u2014 evidence is collected, not demanded.",
      "files": [
        "(the host process)"
      ]
    },
    {
      "id": "ev-session",
      "plane": "host",
      "kind": "event",
      "size": 1,
      "label": "SessionStart",
      "desc": "startup | resume | compact. The compact matcher is load-bearing and under-used: measured elsewhere, constraint violation rises from 0% in full context to 78% after four compaction rounds, and soft organisational policy \u2014 which is exactly what an obligation list is \u2014 decays about 8.3x faster than hard norms. PLAN 5.14 says re-assert obligations here rather than trusting them to survive the summary.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ev-prompt",
      "plane": "host",
      "kind": "event",
      "size": 2,
      "label": "UserPromptSubmit",
      "desc": "Where a request becomes claims. claims.infer reads the request deterministically first; a model call is the documented fallback, not the default. opens_new_task decides whether this continues the last task or starts one, which matters because R7 let a new request inherit the previous task's evidence and read set.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ev-pre",
      "plane": "host",
      "kind": "event",
      "size": 1,
      "label": "PreToolUse",
      "desc": "Fires before Bash, PowerShell, Edit, Write, NotebookEdit. This is where the scope guard asks \u2014 never denies \u2014 when an edit lands somewhere the task has neither read nor been asked about.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ev-post",
      "plane": "host",
      "kind": "event",
      "size": 2,
      "label": "PostToolUse",
      "desc": "Fires after Bash, PowerShell, Read, Edit, Write, NotebookEdit, NotebookRead. The busiest seam: every command result that becomes evidence, and every edit that stales it, arrives here. Also the event Phase C0's ratchet will hang from \u2014 the runtime already recomputes freshness on each edit and currently prints the answer as a complaint.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ev-postfail",
      "plane": "host",
      "kind": "event",
      "size": 1,
      "label": "PostToolUseFailure",
      "desc": "Bash and PowerShell only. Subscribed because H1: a documented failure shape put the error at the top level of the payload while read_result only looked under nested keys, so a real failure produced no evidence at all. Replay fidelity is not delivery fidelity.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ev-stop",
      "plane": "host",
      "kind": "event",
      "size": 2,
      "label": "Stop",
      "desc": "Where the gate computes a state instead of believing one. Also, on the 2026-09-15 evidence, the wrong place to repair anything: the median decisive error lands at step 7 of 27 and 82% of doomed runs keep executing past the point of no return. Kept as the place to REPORT (PLAN 5.11, 5.12).",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "hooks-json",
      "plane": "seam",
      "kind": "config",
      "size": 2,
      "label": "hooks.json",
      "desc": "Which events the runtime actually receives. The scope guard once shipped completely inert because this file subscribed PostToolUse to Bash only, while every unit test passed. core/wiring.py now owns the list and ep-doctor checks the file against it.",
      "files": [
        "plugin/hooks/hooks.json"
      ]
    },
    {
      "id": "ep-hook",
      "plane": "seam",
      "kind": "script",
      "size": 2,
      "label": "ep_hook.py",
      "desc": "One process, one event. Adds the repo root to sys.path and calls core.hook.main. Deliberately thin \u2014 everything interesting is importable and therefore testable.",
      "files": [
        "plugin/bin/ep_hook.py"
      ]
    },
    {
      "id": "ep-doctor",
      "plane": "seam",
      "kind": "script",
      "size": 2,
      "label": "ep_doctor.py",
      "desc": "Feeds the runtime a tool result shaped exactly as the host shapes one and checks the answer comes back right. Exists because three defects in this layer each failed by doing nothing while every unit test stayed green. Its own --host flag was silently discarded for weeks, which is the joke it now tells about itself.",
      "files": [
        "plugin/bin/ep_doctor.py",
        "core/doctor.py"
      ]
    },
    {
      "id": "ep-status",
      "plane": "seam",
      "kind": "script",
      "size": 1,
      "label": "ep_status.py",
      "desc": "What is still owed on this task, on demand, without finishing a turn to find out.",
      "files": [
        "plugin/bin/ep_status.py",
        "core/status.py"
      ]
    },
    {
      "id": "ep-repeat",
      "plane": "seam",
      "kind": "script",
      "size": 1,
      "label": "ep_repeat.py",
      "desc": "Standalone flaky-test runner. ep-repeat 50 --jobs 8 -- pytest tests/test_login.py. None of the fourteen surveyed systems ships anything like it.",
      "files": [
        "plugin/bin/ep_repeat.py",
        "core/repeat.py"
      ]
    },
    {
      "id": "plugin-json",
      "plane": "seam",
      "kind": "config",
      "size": 1,
      "label": "plugin.json",
      "desc": "The Claude Code plugin manifest.",
      "files": [
        "plugin/.claude-plugin/plugin.json"
      ]
    },
    {
      "id": "hook",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "core/hook.py",
      "desc": "The dispatcher. Routes one hook event to the runtime: reads the payload, parses results into evidence, opens claims, observes edits, discharges declared commands, and renders the message the user sees. Everything else in core/ hangs off this.",
      "files": [
        "core/hook.py"
      ]
    },
    {
      "id": "payload",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "payload.py",
      "desc": "Reading what the host ACTUALLY sends, rather than what a hand-written fixture says it sends. command_of, read_result, target_file. Every number this project published before this module was trusted came from payloads written by hand.",
      "files": [
        "core/payload.py"
      ]
    },
    {
      "id": "parsers",
      "plane": "runtime",
      "kind": "engine",
      "size": 2,
      "label": "parsers.py",
      "desc": "Turns test-runner and compiler output into evidence records. Parsing rather than asking. Carries the R5 fix: substring-match plus exit code meant `echo pytest` was a passing suite with zero tests, so a record now knows whether it COUNTED tests and looked.",
      "files": [
        "core/parsers.py"
      ]
    },
    {
      "id": "evidence",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "evidence.py",
      "desc": "The heart of it. An Evidence record binds a command's result to a content hash of exactly the files it observed, and freshness() recomputes FRESH / STALE / GONE on every edit. R1: this was once size and mtime with a vcs_state tie-breaker, which is why the README's central claim had to be withdrawn once. The staleness answer is also a checkpoint pointer that the runtime currently throws away \u2014 see PLAN 1.2.",
      "files": [
        "core/evidence.py"
      ]
    },
    {
      "id": "ledger",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "ledger.py",
      "desc": "External task state: which claims are open, what evidence has arrived, and the verdict computed from both. The largest module here, and the one that turns records into VERIFIED / UNVERIFIED / STALE / CONTRADICTED.",
      "files": [
        "core/ledger.py"
      ]
    },
    {
      "id": "claims",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "claims.py",
      "desc": "Infers which claims a request implies. Deterministic first; a model call is the documented fallback, not the default. Measured over 3,557 real turns: 21% over-claim, 25% missed.",
      "files": [
        "core/claims.py"
      ]
    },
    {
      "id": "obligations",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "obligations.py",
      "desc": "Claim types, risk tiers, and what each combination must prove. Line 149 names `reproduced` \u2014 'that test failed before the fix' \u2014 which the 2026-09-15 audit identified as the highest-value artifact in the field (+28pp against perfect localisation's +8pp), collected here as a receipt at the moment it is worth least. A test seen red before and green after is also discriminating by construction, which is the answer to PLAN 5.10.",
      "files": [
        "core/obligations.py"
      ]
    },
    {
      "id": "surface",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "surface.py",
      "desc": "What a project is actually capable of proving. An obligation no amount of good work can discharge is a design error, not a finding.",
      "files": [
        "core/surface.py"
      ]
    },
    {
      "id": "scope",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "scope.py",
      "desc": "Noticing when an edit has wandered away from the task. Scope is never declared up front \u2014 it is derived from what the task established: files read, files edited, and the areas the request named. It asks; it never denies, because the user is the judge.",
      "files": [
        "core/scope.py"
      ]
    },
    {
      "id": "ratchet",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "ratchet.py",
      "desc": "PLAN 5.6: a long attempt ends at its latest patch, not its best. Measured elsewhere, 60-69% of coding-agent failures reach and edit the CORRECT functions and then produce a wrong patch, and five documented cases produced the reference solution mid-trajectory and corrupted it. When the declared checks are green the working tree is committed to a private ref under refs/elevenpowers/proven - via a temporary index, so the agent's work is never staged as a side effect of observing it - and the end report offers it back if the tree later moves off it. The store and the compare-and-swap restore are Cline's; the refusal when HEAD has moved is the eligibility check the 2026 recoverability work found missing everywhere, having concluded that task success cannot detect a bad recovery decision. Ours is only WHEN: on green-and-fresh rather than per edit, which is what turns a 10-40x test cost into a commit-tree. Offers; never restores.",
      "files": [
        "core/ratchet.py"
      ]
    },
    {
      "id": "stress",
      "plane": "runtime",
      "kind": "engine",
      "size": 3,
      "label": "stress.py",
      "desc": "PLAN 5.0 pointed at the product instead of at the test suite. A passing check is two facts short of evidence: it must be FRESH, which evidence.py answers, and it must be able to FAIL, which nothing answered until now. Runs every declared check the other way round - in a detached git worktree built from the commit the task started at - and if it already passed there, the record is not evidence the change works. Reports, never refuses: 5.12 says detection and intervention are separately justified, and this gate once blocked 75% of runs on a signal it had not measured. Only declared commands are run, same rule as verify.py. The user's working tree is never touched, and the answer is cached per task because the base does not move. Runs the OLD SOURCE with the NEW TESTS laid over it, because a test the agent wrote a minute ago is not in the base commit - without carrying it across, every check comes back 'passed before' by construction and the answer is the harness's rather than the work's. Tests only: carrying the fix across would leave no old behaviour to fail against. One run answers two questions: the exit code says whether the check COULD have failed (5.10), and the output says which individual tests were ALREADY RED back there (5.13) - a test red before and green now is a reproduction whatever order the agent worked in. Collection errors count too, and are the common case: a test for behaviour the fix introduces cannot import on the old tree, so pytest reports the file with no node id at all. MEASURED 2026-09-17 and it came back null: across B3 and B4, 22 runs on 16 real tasks with two models, exactly ONE verdict was VACUOUS and it did not replicate when the other model got the identical task - 0 of 14 on B4. The externally measured 46% is cited, not reproduced here, and PLAN 10 withdraws the frequency claim until a corpus or an n supports it. The mechanism is kept for what it demonstrably does: it caught the one case, and the failed_before it computes on the same run is what 5.13's reproduction depends on. Since 2026-09-17 it also asks the other half of 5.13 instead of waiting for it: confirm() runs the tests just found red on the base tree against the tree as it is, so a reproduction is established BY NAME rather than inferred from the same run that decided discrimination - measured 0 of 7 reproductions came from the named path before this, and 6 of 16 rehearsed tasks reach it now. The declared path is SUBSTITUTED rather than appended to, because pytest tests -q plus node ids runs the directory and the ids both; a token counts as a path only if it exists, which is what separates tests from the no:cacheprovider in -p no:cacheprovider. Passes cannot be read from -q output, so the named failures are subtracted from the ids that were run, and any exit code but 0 or 1 claims nothing.",
      "files": [
        "core/stress.py"
      ]
    },
    {
      "id": "radius",
      "plane": "runtime",
      "kind": "engine",
      "size": 2,
      "label": "radius.py",
      "desc": "What else depends on the thing you just changed. Agents fix one bug and make another - 16 to 37 percent of applied agent patches break a pre-existing test, and recall grows near-linearly while precision saturates - and this project's own corpus holds the case: click-762c97ee, where the agent fixed Choice and never generalised to DateTime. PLAN 5.2 named the remedy and it sat unbuilt. Computed rather than asked for, because constraint violation rises 0 to 78 percent across four compaction rounds and a bad plan measures worse than no plan over 16,991 trajectories - nothing is asked of the agent's memory, so nothing can be forgotten. git diff -U0 gives changed line ranges; ast gives the def/class whose own span intersects them; a sibling is another class that shares a BASE and overrides the same method, never merely the same name. Aider's repomap.py is the better symbol graph and the upgrade path, but it needs four third-party packages and core/ has none. Two defects the fixture could not show and the real click repository did: bases are ast.Subscript in generic code, not Name; and Generic, Protocol and ABC are scaffolding that made a base class a sibling of its own subclass. Names dependents, demands nothing.",
      "files": [
        "core/radius.py"
      ]
    },
    {
      "id": "atlas",
      "plane": "runtime",
      "kind": "engine",
      "size": 2,
      "label": "atlas.py",
      "desc": "The architecture the code actually has, against the one the docs claim. Murphy, Notkin and Sullivan's software reflexion model (FSE 1995) - state a high-level model, extract one from the source, report convergence, divergence and absence - with the high-level model being the architecture document the repository already commits rather than one stated by hand. Divergence: a module this task added that no map names, which is the standing CLAUDE.md rule that gets forgotten, now computed. Absence: a document still naming a path this task removed, which is Tan, Wagner and Treude's mechanism (EMSE 2023, 3,000+ projects) taken verbatim. Scoped to what this change caused; standing drift is one number, never an obligation. docs/design/ is documentation but is NOT the map - found by running this against its own repository, where core/radius.py came back documented because the design note proposing it mentioned it. Also the half that makes the map get used: the neighbourhood of a file, handed over at the first edit of it, which is the only moment it can change the edit. MEASURED 2026-09-17, the check 5.9 required and shipping did not wait for, and the two halves came back very differently. The neighbourhood brief fires on 47% of files a real commit touched - 63 of 135 across five upstream repositories, median 163 characters - the same order as radius.py's 43%, and it is the half that earns its place on any Python repository. The drift check fired on 0 of 23 commits, and not through a defect: every .py those repositories added was a TEST file, correctly not a module an architecture map should name, and none of the five keeps an architecture document at all, so click's map falls back to its README. The drift half applies to a project that both grows modules and maintains a map. This repository is one, which is why it fired here and caught radius.py and atlas.py the day they were written; a mature library is not, and there it is silent by design rather than broken.",
      "files": [
        "core/atlas.py"
      ]
    },
    {
      "id": "verify",
      "plane": "runtime",
      "kind": "engine",
      "size": 2,
      "label": "verify.py",
      "desc": "Computing the missing evidence instead of demanding it. Blocking to make an agent run a command costs another turn at 2.5x the tokens; running it costs seconds and no tokens. Only commands the project declared are ever run. This module is also the ratchet's engine \u2014 Phase C0 needs exactly what it already does.",
      "files": [
        "core/verify.py"
      ]
    },
    {
      "id": "report",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "report.py",
      "desc": "The two messages that are the product's visible surface: the start banner announcing obligations at the first edit, and the end report. On the 2026-09-15 evidence this is the product, and blocking is a profile (PLAN 1.3, 5.12).",
      "files": [
        "core/report.py"
      ]
    },
    {
      "id": "config",
      "plane": "runtime",
      "kind": "lib",
      "size": 1,
      "label": "config.py",
      "desc": "What the project told the runtime about itself: profile and declared commands. A repo with no config behaves exactly as it did before.",
      "files": [
        "core/config.py",
        ".elevenpowers/config.json"
      ]
    },
    {
      "id": "intent",
      "plane": "runtime",
      "kind": "lib",
      "size": 1,
      "label": "intent.py",
      "desc": "Reads the agent's last message for two things the gate must respect. A gate that blocks an agent for asking the USER a question is broken.",
      "files": [
        "core/intent.py"
      ]
    },
    {
      "id": "repeat",
      "plane": "runtime",
      "kind": "lib",
      "size": 2,
      "label": "repeat.py",
      "desc": "Running a command many times, and knowing how many is enough. Three failures in thirty is a 10% rate; ruling it out at 95% needs 29 clean runs because 0.9^29 < 0.05. R9: clean repeats of an UNRELATED command used to certify a flaky test. Candidate for replacement by anytime-valid confidence sequences.",
      "files": [
        "core/repeat.py"
      ]
    },
    {
      "id": "status",
      "plane": "runtime",
      "kind": "lib",
      "size": 1,
      "label": "status.py",
      "desc": "Renders the current belief on demand.",
      "files": [
        "core/status.py"
      ]
    },
    {
      "id": "doctor",
      "plane": "runtime",
      "kind": "engine",
      "size": 2,
      "label": "doctor.py",
      "desc": "The seam self-check, including that hooks.json subscribes every event the runtime handles.",
      "files": [
        "core/doctor.py"
      ]
    },
    {
      "id": "wiring",
      "plane": "runtime",
      "kind": "lib",
      "size": 1,
      "label": "wiring.py",
      "desc": "Which events the runtime needs, and the hook configuration that delivers them. Single source of truth for COMMAND_TOOLS, EDIT_TOOLS, FILE_TOOLS.",
      "files": [
        "core/wiring.py"
      ]
    },
    {
      "id": "blindspots",
      "plane": "runtime",
      "kind": "lib",
      "size": 1,
      "label": "blindspots.py",
      "desc": "A record of the moments the runtime could not understand its host. Anything unparseable lands here, so a host that renames a field becomes a diagnosable symptom instead of a tool that quietly went quiet. Silence must leave a trace.",
      "files": [
        "core/blindspots.py"
      ]
    },
    {
      "id": "ledger-json",
      "plane": "state",
      "kind": "store",
      "size": 2,
      "label": "ledger.json",
      "desc": "The durable task ledger. Survives compaction, which is the point \u2014 PLAN 5.14 measures how fast soft policy evaporates from a summary.",
      "files": [
        ".elevenpowers/ledger.json"
      ]
    },
    {
      "id": "blindspots-jsonl",
      "plane": "state",
      "kind": "store",
      "size": 1,
      "label": "blindspots.jsonl",
      "desc": "Unparseable payloads, appended.",
      "files": [
        ".elevenpowers/blindspots.jsonl"
      ]
    },
    {
      "id": "config-json",
      "plane": "state",
      "kind": "store",
      "size": 1,
      "label": "config.json",
      "desc": "profile (off | guide | strict) and declared commands.",
      "files": [
        ".elevenpowers/config.json"
      ]
    },
    {
      "id": "checkpoints-jsonl",
      "plane": "state",
      "kind": "store",
      "size": 1,
      "label": "checkpoints.jsonl",
      "desc": "Written by the eval recorder, not by the runtime: the candidate patch as it stood at every PROPOSED stop, in both arms. Built to grade a block AT the block, which PLAN 6 says the 12% P2 figure never did.",
      "files": [
        ".elevenpowers/checkpoints.jsonl"
      ]
    },
    {
      "id": "rehearse",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "rehearse.py",
      "desc": "The pre-flight that should have run before the aborted sweep. Seeds a real task at its real base commit, applies the GOLD patch as a correct agent would, records a passing suite with an AGENT-SHAPED command rather than the declared string, and asks the runtime the question the sweep exists to ask. Everything except the agent is genuine - repository, base, fix, declared command, worktree, parsers - so it costs nothing and still exercises the whole path. Written after a sweep spent $1.42 over two runs and recorded discrimination={} on both, because stress matched the declared command exactly and agents never type it. Sizing missed that: it counted any passing suite record at 100% while the code required one carrying the declared string at 0%. A pass here means a sweep would return verdicts; it says nothing about what they will be. Widened 2026-09-16 after it failed to predict the B3 sweep's missing base commit: it had been CONSTRUCTING the Ledger itself, with base and claims passed in, so it built the ledger a correct run would have built and then checked that a correct ledger works - while the defect was in how the runtime builds one. The prompt and every edit now go through core.hook as real events with the task's real prompt text, and only the evidence record is still injected, because there is no agent here to run a command. A rehearsal may stand in for the agent, never for the runtime. It now reports base and claims per task and refuses outright when any run opened without a base.",
      "files": [
        "eval/rehearse.py"
      ]
    },
    {
      "id": "wheelhouse",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "wheelhouse.py",
      "desc": "A local shelf of build backends, so the registry can be switched off. Every repository in the corpus has a released version on PyPI that already carries its own fix, and canary.py found three of the four exposures surviving the tool-denial list fetching exactly that. PIP_NO_INDEX shuts it - and could not be set alone, because pip builds in an ISOLATED environment and fetches setuptools into it, and no environment variable turns that isolation off (PIP_NO_BUILD_ISOLATION, PIP_BUILD_ISOLATION=false|0|no and a pip.ini were each measured and each ignored). So the shelf feeds the isolated build instead, via PIP_FIND_LINKS, which pip reads with the index off. Stages the backends the corpus actually declares, read from its pyproject files: hatchling and hatch-vcs (attrs), flit_core (click, jinja2, itsdangerous), setuptools (markupsafe). Engages ONLY when complete - an incomplete shelf plus a closed index breaks every install, and a guard that breaks honest work is the guard an agent turns off.",
      "files": [
        "eval/wheelhouse.py"
      ]
    },
    {
      "id": "live",
      "plane": "eval",
      "kind": "engine",
      "size": 3,
      "label": "live.py",
      "desc": "Drives the real Claude Code CLI against a seeded workspace. Owns containment (suspended launch bound to a Windows job object with KILL_ON_JOB_CLOSE, after eleven orphaned find.exe processes at 90% CPU), the workspace venv that finally stopped agents installing into the machine, and the closed-book denial list that pip walked straight through.",
      "files": [
        "eval/live.py"
      ]
    },
    {
      "id": "baseline",
      "plane": "eval",
      "kind": "engine",
      "size": 3,
      "label": "baseline.py",
      "desc": "The paired sweep: vanilla against gate, resumable, model-mismatch aborts, per-run exceptions graded `setup`. Checks the shared site before and after every run AND against what the sweep started with, because a per-run comparison cannot see damage already done.",
      "files": [
        "eval/baseline.py"
      ]
    },
    {
      "id": "bundle",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "bundle.py",
      "desc": "A run that survives its workspace: task manifest, base identity, candidate diff, host events, prompts, trajectory, node outcomes, result. Byte-exact patch I/O with core.autocrlf=false after three stacked line-ending defects. E3 was fixed here, which is why the 2026-09-15 free measurements are possible at all.",
      "files": [
        "eval/bundle.py"
      ]
    },
    {
      "id": "mine",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "mine.py",
      "desc": "Builds real tasks from upstream history without Docker. Rejects machine-dependent node ids. Candidate discovery went from 18s to 0.03s with a single git log --name-only.",
      "files": [
        "eval/mine.py"
      ]
    },
    {
      "id": "corpus",
      "plane": "eval",
      "kind": "lib",
      "size": 2,
      "label": "corpus.py",
      "desc": "Band selection and the pinned lock. A corpus of 15 that could not move became 49 that can.",
      "files": [
        "eval/corpus.py",
        "eval/corpus.lock"
      ]
    },
    {
      "id": "checkpoint-mod",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "checkpoint.py",
      "desc": "A passive Stop hook installed in BOTH arms, because an instrument present on one side and absent on the other IS the difference between the sides. Always allows. Takes the diff BEFORE opening its own journal, since opening creates the file and the next thing it does is git add -A.",
      "files": [
        "eval/checkpoint.py"
      ]
    },
    {
      "id": "canary",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "canary.py",
      "desc": "The instrument PLAN 4.1 says a boundary needs before it can be trusted: a token that must be FOUND with the boundary off and ABSENT with it on. Where exposure.py looks for the task's own fix sha, this looks for the answer's vocabulary - identifiers the upstream fix DEFINES that appear nowhere in the base tree. Order is the evidence, not presence: a name arriving in a tool result before the run ever used it is a name it did not invent. On chunk1 it finds 21 of 36 watchable runs against exposure.py's 2 on the same bundles, and it names the door: 14 upstream network, 4 the machine's own site-packages, 3 local. Five runs reached the vocabulary unaided, which is how the screen shows it can still tell the innocent case.",
      "files": [
        "eval/canary.py"
      ]
    },
    {
      "id": "exposure",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "exposure.py",
      "desc": "Screens each run's transcript against its own task's fix sha. Reports a floor and refuses to filter. On the 2026-09-15 evidence this is the most defensible thing in the repository: an independent audit of 731 trajectories found 63% of successful resolutions retrieved rather than derived the fix.",
      "files": [
        "eval/exposure.py"
      ]
    },
    {
      "id": "analyse",
      "plane": "eval",
      "kind": "lib",
      "size": 2,
      "label": "analyse.py",
      "desc": "Scores with an interval over tasks rather than runs, keeping every replicate (E2).",
      "files": [
        "eval/analyse.py"
      ]
    },
    {
      "id": "noise",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "noise.py",
      "desc": "runs_for: how many paired runs a comparison actually needs, from a measured disagreement rate rather than a flip rate.",
      "files": [
        "eval/noise.py"
      ]
    },
    {
      "id": "validate",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "validate.py",
      "desc": "Grades the grader: gold patch resolves, a known regression fails, a wrong patch fails, a setup failure is reported as setup. Four of four.",
      "files": [
        "eval/validate.py"
      ]
    },
    {
      "id": "task",
      "plane": "eval",
      "kind": "lib",
      "size": 2,
      "label": "task.py",
      "desc": "A task and its preservation sets. E1 lived here: the grader ran only f2p, so a patch that broke existing tests scored as resolved \u2014 blind to the exact thing the gate is for.",
      "files": [
        "eval/task.py",
        "eval/tasks.py",
        "eval/tasks_repo.py",
        "eval/mined.py"
      ]
    },
    {
      "id": "chunks",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "chunks.py",
      "desc": "Stratified seeded split, so a paired sweep can be bought in monitorable pieces.",
      "files": [
        "eval/chunks.py"
      ]
    },
    {
      "id": "failures",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "failures.py",
      "desc": "A failure taxonomy where every category cites saved trajectories.",
      "files": [
        "eval/failures.py"
      ]
    },
    {
      "id": "transcript",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "transcript.py",
      "desc": "Reads host transcripts; feeds prompts and replay.",
      "files": [
        "eval/transcript.py",
        "eval/prompts.py",
        "eval/replay.py"
      ]
    },
    {
      "id": "cases",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "claim/scope cases",
      "desc": "Offline case suites for claim inference and the scope guard, run against recorded turns rather than live agents.",
      "files": [
        "eval/claim_cases.py",
        "eval/claims_run.py",
        "eval/scope_cases.py",
        "eval/scope_run.py"
      ]
    },
    {
      "id": "scenarios",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "scenario harness",
      "desc": "The synthetic track that predates mining: hand-built scenarios, a held-out split, and a runner. Kept because \u00a76 says keep easy tasks in the held-out set - they cannot show an improvement and they are the only way to catch a regression.",
      "files": [
        "eval/run.py",
        "eval/scenarios.py",
        "eval/heldout.py"
      ]
    },
    {
      "id": "discriminate",
      "plane": "eval",
      "kind": "engine",
      "size": 2,
      "label": "discriminate.py",
      "desc": "Phase B2.1, and the first experiment this project ever ran for nothing. Asks whether our own recorded evidence measures anything, against runs already bought. It found a prior defect before it could ask its own question: a passing suite record was decided by the exit code alone, and 288 of 295 such records ran pytest through `| tail -N`, where the pipeline reports tail's status. 123 of them (42%) say PASS while holding a non-zero failure count; the worst reads failed=87, passed=1339. Corrects the history without re-running anything, because every record carries the counts the decision should have used. Reports the confound rather than burying it: affected runs ran a median of five suite records against two, so exposure is tangled with difficulty and the outcome split is NOT causal.",
      "files": [
        "eval/discriminate.py"
      ]
    },
    {
      "id": "pool",
      "plane": "eval",
      "kind": "lib",
      "size": 2,
      "label": "pool.py",
      "desc": "Phase B2.2. Pool coverage against a random pick from the same pool, which is selection regret (\u00a75.1). Keyed by sweep, task and arm, because `closedbook` is a different condition by construction and pooling it would lend the others attempts they never had. Measured: the gap runs from +2.0 to +20.0 points across comparable pools, and the `mixed` column says why - it is produced entirely by the 1 to 5 tasks per pool whose attempts disagree. On the same 15 tasks, two passes of the same sweep gave +4.4 and +20.0, a difference of five single lucky runs.",
      "files": [
        "eval/pool.py"
      ]
    },
    {
      "id": "stack",
      "plane": "eval",
      "kind": "lib",
      "size": 1,
      "label": "stack.py",
      "desc": "The composition baseline: best-of-breed pieces installed together. complementarity-matrix.md 6 says this, not vanilla, is the bar this project must beat. Never run.",
      "files": [
        "eval/stack.py"
      ]
    },
    {
      "id": "results",
      "plane": "bundles",
      "kind": "store",
      "size": 3,
      "label": "results/",
      "desc": "Over a hundred paid runs with candidate, base and grade preserved. The three $0 measurements in PLAN Phase B2 run entirely against this directory \u2014 the first time the next experiment costs nothing.",
      "files": [
        "results/",
        "results/prevalence/"
      ]
    },
    {
      "id": "corpus-lock",
      "plane": "bundles",
      "kind": "store",
      "size": 1,
      "label": "corpus locks",
      "desc": "The pinned corpus and its paired chunks, declaring band selection.",
      "files": [
        "eval/corpus.lock",
        "eval/corpus-paired.lock",
        "eval/corpus-paired.chunks.json"
      ]
    },
    {
      "id": "claude-cli",
      "plane": "external",
      "kind": "service",
      "size": 2,
      "label": "claude CLI",
      "desc": "The agent under test. Driven with --disallowed-tools and a permission mode; sub-agent permissions do not propagate, which is one of the ways the closed-book condition leaked.",
      "files": [
        "(claude executable)"
      ]
    },
    {
      "id": "git",
      "plane": "external",
      "kind": "service",
      "size": 2,
      "label": "git",
      "desc": "Base identity, patch export and apply, and the tree the evidence hash is taken over. Always invoked with core.autocrlf=false and core.eol=lf.",
      "files": []
    },
    {
      "id": "pytest",
      "plane": "external",
      "kind": "service",
      "size": 2,
      "label": "test runners",
      "desc": "pytest and friends. Their output is the raw material: the agent runs them anyway, and parsers.py reads what comes back.",
      "files": []
    },
    {
      "id": "upstream",
      "plane": "external",
      "kind": "service",
      "size": 2,
      "label": "upstream repos",
      "desc": "Real repositories mined for real defects \u2014 and, on the 2026-09-15 evidence, also the answer key. pip clones git+ URLs internally, so denying git clone never closed the book. PLAN 4.1 replaces the denial list with --network none plus a pre-staged wheelhouse.",
      "files": []
    },
    {
      "id": "venv",
      "plane": "external",
      "kind": "service",
      "size": 1,
      "label": "workspace venv",
      "desc": "Built with --system-site-packages and placed first on PATH. Three environment variables failed to stop agents installing into the machine; giving them somewhere harmless to install worked.",
      "files": []
    },
    {
      "id": "tests",
      "plane": "external",
      "kind": "service",
      "size": 2,
      "label": "tests/",
      "desc": "513 tests, including tests/test_audit_probes.py where every reproduced defect keeps the probe that found it, with no xfail markers left.",
      "files": [
        "tests/"
      ]
    }
  ],
  "edges": [
    {
      "source": "report",
      "target": "radius",
      "label": "names dependents"
    },
    {
      "source": "report",
      "target": "atlas",
      "label": "names map and doc drift"
    },
    {
      "source": "radius",
      "target": "surface",
      "label": "reads test names"
    },
    {
      "source": "atlas",
      "target": "surface",
      "label": "walks the repo"
    },
    {
      "source": "hook",
      "target": "atlas",
      "label": "briefs before the first edit"
    },
    {
      "source": "agent",
      "target": "ev-session",
      "label": "emits"
    },
    {
      "source": "ev-session",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "agent",
      "target": "ev-prompt",
      "label": "emits"
    },
    {
      "source": "ev-prompt",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "agent",
      "target": "ev-pre",
      "label": "emits"
    },
    {
      "source": "ev-pre",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "agent",
      "target": "ev-post",
      "label": "emits"
    },
    {
      "source": "ev-post",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "agent",
      "target": "ev-postfail",
      "label": "emits"
    },
    {
      "source": "ev-postfail",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "agent",
      "target": "ev-stop",
      "label": "emits"
    },
    {
      "source": "ev-stop",
      "target": "hooks-json",
      "label": "matched by"
    },
    {
      "source": "hooks-json",
      "target": "ep-hook",
      "label": "runs one process per event"
    },
    {
      "source": "ep-hook",
      "target": "hook",
      "label": "core.hook.main"
    },
    {
      "source": "agent",
      "target": "claude-cli",
      "label": "is"
    },
    {
      "source": "hook",
      "target": "payload",
      "label": "read what the host sent"
    },
    {
      "source": "hook",
      "target": "parsers",
      "label": "output -> evidence"
    },
    {
      "source": "hook",
      "target": "evidence",
      "label": "Result"
    },
    {
      "source": "hook",
      "target": "ledger",
      "label": "open, observe, verdict"
    },
    {
      "source": "hook",
      "target": "obligations",
      "label": "risk_of"
    },
    {
      "source": "hook",
      "target": "claims",
      "label": "infer / opens_new_task"
    },
    {
      "source": "hook",
      "target": "scope",
      "label": "normalise / unrelated"
    },
    {
      "source": "ledger",
      "target": "stress",
      "label": "a declared check red on the old tree and green now IS the reproduction"
    },
    {
      "source": "hook",
      "target": "ratchet",
      "label": "green at Stop: keep this state where a later edit cannot lose it"
    },
    {
      "source": "ratchet",
      "target": "git",
      "label": "commit-tree into a private ref, temporary index, nothing of the user's touched"
    },
    {
      "source": "report",
      "target": "ratchet",
      "label": "offer the proven state back, or say why it is not eligible"
    },
    {
      "source": "hook",
      "target": "stress",
      "label": "at Stop: would these checks have failed without the change?"
    },
    {
      "source": "stress",
      "target": "git",
      "label": "detached worktree at the base commit - the working tree is untouched"
    },
    {
      "source": "stress",
      "target": "parsers",
      "label": "read the old tree's output for tests that were already red"
    },
    {
      "source": "stress",
      "target": "ledger-json",
      "label": "cached per task; the base does not move"
    },
    {
      "source": "report",
      "target": "stress",
      "label": "\"could not fail\" lines"
    },
    {
      "source": "hook",
      "target": "verify",
      "label": "discharge"
    },
    {
      "source": "hook",
      "target": "report",
      "label": "the visible surface"
    },
    {
      "source": "hook",
      "target": "wiring",
      "label": "which tools count"
    },
    {
      "source": "hook",
      "target": "blindspots",
      "label": "record what it could not read"
    },
    {
      "source": "claims",
      "target": "obligations",
      "label": ""
    },
    {
      "source": "parsers",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "obligations",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "obligations",
      "target": "surface",
      "label": ""
    },
    {
      "source": "surface",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "verify",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "verify",
      "target": "parsers",
      "label": ""
    },
    {
      "source": "report",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "report",
      "target": "ledger",
      "label": ""
    },
    {
      "source": "report",
      "target": "surface",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "claims",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "config",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "intent",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "obligations",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "repeat",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "scope",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "surface",
      "label": ""
    },
    {
      "source": "status",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "status",
      "target": "ledger",
      "label": ""
    },
    {
      "source": "status",
      "target": "report",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "config",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "evidence",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "ledger",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "parsers",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "payload",
      "label": ""
    },
    {
      "source": "doctor",
      "target": "wiring",
      "label": ""
    },
    {
      "source": "ledger",
      "target": "ledger-json",
      "label": "the durable task state"
    },
    {
      "source": "blindspots",
      "target": "blindspots-jsonl",
      "label": "append what could not be parsed"
    },
    {
      "source": "config",
      "target": "config-json",
      "label": "profile + declared commands"
    },
    {
      "source": "evidence",
      "target": "git",
      "label": "tree hash over observed files"
    },
    {
      "source": "verify",
      "target": "pytest",
      "label": "run only what the project declared"
    },
    {
      "source": "ep-doctor",
      "target": "doctor",
      "label": ""
    },
    {
      "source": "ep-status",
      "target": "status",
      "label": ""
    },
    {
      "source": "ep-repeat",
      "target": "repeat",
      "label": ""
    },
    {
      "source": "plugin-json",
      "target": "hooks-json",
      "label": "declares"
    },
    {
      "source": "wiring",
      "target": "hooks-json",
      "label": "GENERATES it - divergence is impossible, not merely unlikely"
    },
    {
      "source": "hook",
      "target": "claims",
      "label": "infer at UserPromptSubmit"
    },
    {
      "source": "repeat",
      "target": "pytest",
      "label": "n clean runs, derived"
    },
    {
      "source": "live",
      "target": "claude-cli",
      "label": "drives the real CLI, contained in a job object"
    },
    {
      "source": "live",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "live",
      "target": "mine",
      "label": ""
    },
    {
      "source": "live",
      "target": "task",
      "label": ""
    },
    {
      "source": "rehearse",
      "target": "stress",
      "label": "would the check engage at all, on a real task, for nothing?"
    },
    {
      "source": "rehearse",
      "target": "live",
      "label": "the harness's own seeding, so the rehearsal is not a different world"
    },
    {
      "source": "live",
      "target": "wheelhouse",
      "label": "shelf complete? then close the index for the run"
    },
    {
      "source": "wheelhouse",
      "target": "upstream",
      "label": "staged ONCE while online; every run after is offline"
    },
    {
      "source": "live",
      "target": "venv",
      "label": "installs land here, not in the machine"
    },
    {
      "source": "live",
      "target": "checkpoint-mod",
      "label": "recorder installed in BOTH arms"
    },
    {
      "source": "checkpoint-mod",
      "target": "checkpoints-jsonl",
      "label": "the candidate at the moment of the stop"
    },
    {
      "source": "checkpoint-mod",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "baseline",
      "target": "live",
      "label": ""
    },
    {
      "source": "baseline",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "baseline",
      "target": "corpus",
      "label": ""
    },
    {
      "source": "baseline",
      "target": "task",
      "label": ""
    },
    {
      "source": "baseline",
      "target": "mine",
      "label": ""
    },
    {
      "source": "corpus",
      "target": "mine",
      "label": ""
    },
    {
      "source": "corpus",
      "target": "corpus-lock",
      "label": ""
    },
    {
      "source": "mine",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "mine",
      "target": "upstream",
      "label": "mine real defects from history"
    },
    {
      "source": "bundle",
      "target": "git",
      "label": "byte-exact export and apply"
    },
    {
      "source": "bundle",
      "target": "results",
      "label": "a run that survives its workspace"
    },
    {
      "source": "validate",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "validate",
      "target": "live",
      "label": ""
    },
    {
      "source": "validate",
      "target": "task",
      "label": ""
    },
    {
      "source": "analyse",
      "target": "results",
      "label": "interval over tasks, every replicate kept"
    },
    {
      "source": "failures",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "discriminate",
      "target": "results",
      "label": "re-derive what the record should have said, from counts already on disk"
    },
    {
      "source": "discriminate",
      "target": "parsers",
      "label": "the defect it found lives here"
    },
    {
      "source": "pool",
      "target": "results",
      "label": "coverage vs a random pick, per sweep"
    },
    {
      "source": "canary",
      "target": "results",
      "label": "was the run handed the answer's own vocabulary, and by which door?"
    },
    {
      "source": "canary",
      "target": "upstream",
      "label": "the tokens the fix invented, read from the cached repo"
    },
    {
      "source": "exposure",
      "target": "results",
      "label": "screen each transcript against its own fix sha"
    },
    {
      "source": "noise",
      "target": "analyse",
      "label": ""
    },
    {
      "source": "chunks",
      "target": "corpus",
      "label": ""
    },
    {
      "source": "transcript",
      "target": "results",
      "label": ""
    },
    {
      "source": "cases",
      "target": "transcript",
      "label": ""
    },
    {
      "source": "stack",
      "target": "live",
      "label": "the composition baseline - the real bar, never run"
    },
    {
      "source": "scenarios",
      "target": "bundle",
      "label": ""
    },
    {
      "source": "scenarios",
      "target": "task",
      "label": "held-out split: easy tasks catch regressions"
    },
    {
      "source": "task",
      "target": "pytest",
      "label": "f2p + p2p preservation sets"
    },
    {
      "source": "tests",
      "target": "hook",
      "label": "513, and the probes that found each defect"
    },
    {
      "source": "doctor",
      "target": "blindspots",
      "label": "records what it cannot read"
    },
    {
      "source": "status",
      "target": "blindspots",
      "label": "surfaces what went unread"
    },
    {
      "source": "stress",
      "target": "evidence",
      "label": "reads kinds and results"
    },
    {
      "source": "stress",
      "target": "surface",
      "label": "which files look like tests"
    },
    {
      "source": "canary",
      "target": "exposure",
      "label": "uses"
    },
    {
      "source": "checkpoint-mod",
      "target": "task",
      "label": "uses"
    },
    {
      "source": "cases",
      "target": "claims",
      "label": "reuses the runtime"
    },
    {
      "source": "cases",
      "target": "scope",
      "label": "reuses the runtime"
    },
    {
      "source": "live",
      "target": "config",
      "label": "reuses the runtime"
    },
    {
      "source": "live",
      "target": "intent",
      "label": "reuses the runtime"
    },
    {
      "source": "live",
      "target": "wiring",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "parsers",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "wiring",
      "label": "reuses the runtime"
    },
    {
      "source": "rehearse",
      "target": "config",
      "label": "reuses the runtime"
    },
    {
      "source": "rehearse",
      "target": "evidence",
      "label": "reuses the runtime"
    },
    {
      "source": "rehearse",
      "target": "ledger",
      "label": "reuses the runtime"
    },
    {
      "source": "rehearse",
      "target": "task",
      "label": "uses"
    },
    {
      "source": "transcript",
      "target": "claims",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "evidence",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "ledger",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "obligations",
      "label": "reuses the runtime"
    },
    {
      "source": "transcript",
      "target": "payload",
      "label": "reuses the runtime"
    },
    {
      "source": "scenarios",
      "target": "claims",
      "label": "reuses the runtime"
    },
    {
      "source": "scenarios",
      "target": "evidence",
      "label": "reuses the runtime"
    },
    {
      "source": "scenarios",
      "target": "ledger",
      "label": "reuses the runtime"
    },
    {
      "source": "scenarios",
      "target": "obligations",
      "label": "reuses the runtime"
    },
    {
      "source": "scenarios",
      "target": "parsers",
      "label": "reuses the runtime"
    }
  ]
};
