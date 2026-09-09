# superpowers

- Repo: https://github.com/obra/superpowers (name unchanged, clone succeeded)
- Commit: b36e0829c6d0140e93cfef2ca599b1b07d4a7797, 2026-08-12 09:53 -0700, "Release v6.3.0"
- License: MIT (`LICENSE`, Jesse Vincent 2025); `.claude-plugin/plugin.json` also declares "license": "MIT"
- Primary language: Markdown (94 of 195 files, ~29k lines). Code: shell 41 files (~7.2k lines incl. tests), JS/TS/CJS/MJS ~4.2k lines (mostly the brainstorm server and its tests), Python 542 lines (Hermes adapter + tests). No runtime dependencies (`package.json` has none; `CLAUDE.md` "zero-dependency plugin by design").
- Files: 195 (excluding `.git`)

Superpowers is a skills library plus a per-host bootstrap injector. It targets people running an LLM coding agent (Claude Code first; also Codex, Cursor, Gemini CLI, Copilot CLI, Kimi, OpenCode, Pi, Hermes, Devin, Antigravity per `README.md:10-23`) who want the agent to follow a fixed engineering process: brainstorm -> spec -> plan -> subagent-per-task implementation with review -> finish branch, with TDD, systematic debugging and evidence-before-claims enforced by instruction text. It contains no tool implementations, no retrieval, and no model calls of its own; all behavior is instruction text plus a few helper shell scripts (`docs/porting-to-a-new-harness.md:38-58`).

## Request flow (cite files)

1. Session start. On Claude Code, `hooks/hooks.json:3-15` registers a `SessionStart` hook (matcher `startup|clear|compact`) running `hooks/run-hook.cmd session-start`. `hooks/run-hook.cmd` is a cmd/bash polyglot that locates bash on Windows (`:21-35`) and execs the script on Unix (`:43-46`). `hooks/session-start:11` cats `skills/using-superpowers/SKILL.md`, JSON-escapes it with bash substitutions (`:16-24`), wraps it in `<EXTREMELY_IMPORTANT>You have superpowers...</EXTREMELY_IMPORTANT>` (`:27`) and emits it as `hookSpecificOutput.additionalContext` (`:41-43`), or `additional_context` for Cursor / top-level `additionalContext` for Copilot (`:38-46`).
2. Other hosts do the same injection differently: OpenCode prepends the bootstrap to the first user message via `experimental.chat.messages.transform` (`.opencode/plugins/superpowers.js:124-137`) and registers the skills dir via the `config` hook (`:107-113`); Pi inserts a user message on the `context` event after `session_start`/`session_compact` (`.pi/extensions/superpowers.ts:23-56`); Hermes returns `{"context": bootstrap}` from `pre_llm_call` on the first turn (`.hermes-plugin/__init__.py:91-104`); Gemini uses `GEMINI.md` `@`-includes (`GEMINI.md:1-2`, `gemini-extension.json:5`); Kimi declares `sessionStart.skill: using-superpowers` and an inline tool map (`.kimi-plugin/plugin.json:22-25`).
3. User request arrives. The injected bootstrap instructs: "Invoke relevant or requested skills BEFORE any response or action" and "If you think there is even a 1% chance a skill might apply ... you ABSOLUTELY MUST invoke the skill" (`skills/using-superpowers/SKILL.md:10-24`). Routing rules: "Let's build X" -> brainstorming; "Fix this bug" -> systematic-debugging (`:28-31`). A 12-row Red Flags table pre-empts rationalizations for skipping (`:33-50`).
4. The model loads a skill via the host's Skill tool (Claude Code), `skill` (OpenCode), `activate_skill` (Gemini, `skills/using-superpowers/references/gemini-tools.md:17`), `skill_view` (Hermes), or plain `read` (Pi, `.pi/extensions/superpowers.ts:91`). The skill body then drives the rest: brainstorming -> writing-plans -> subagent-driven-development or executing-plans -> finishing-a-development-branch (`skills/brainstorming/SKILL.md:94-104`, `skills/writing-plans/SKILL.md:153-171`, `skills/executing-plans/SKILL.md:33-38`).
5. Subagent dispatch is done by the model filling markdown templates (`skills/subagent-driven-development/implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md`, `skills/requesting-code-review/code-reviewer.md`) and calling the host's subagent tool. The three shell scripts under `skills/subagent-driven-development/scripts/` prepare files for those subagents; nothing in the repo calls a model.

## What goes into the model (always-loaded vs on-demand, with token estimates)

Always-loaded (per session, re-injected on clear/compact):
- `skills/using-superpowers/SKILL.md`: 485 words, ~630 tokens, plus ~40 words of wrapper (`hooks/session-start:27`) -> ~680 tokens on Claude Code/Cursor/Copilot.
- Gemini adds `references/gemini-tools.md` (618 words, ~800 tokens) -> ~1,450 tokens. Hermes adds `references/hermes-tools.md` (287 words) -> ~1,050 tokens. OpenCode/Pi add an inline tool map (~80-200 words).
- Inferred, not in this repo: Claude Code also lists all 14 skill frontmatter descriptions in the system prompt (~350 words, ~450 tokens).

On-demand (loaded only when a skill is invoked or a file is read):
- 13 other `SKILL.md`: 20,263 words, ~26,300 tokens. Largest: subagent-driven-development 4,825 words (~6,300 tokens), writing-skills 3,779, brainstorming 2,324 (`wc -w skills/*/SKILL.md`).
- Supporting docs: 22,324 words, ~29,000 tokens, of which `skills/writing-skills/anthropic-best-practices.md` is 5,803 words and the four subagent prompt templates total 3,790 words (~4,900 tokens; these get read by the controller and then pasted into dispatches, so they cost roughly twice).
- A full feature workflow (brainstorming + writing-plans + SDD + using-git-worktrees + TDD + finishing + verification) loads ~12,500 words, ~16,000 tokens of skill text into the controller context, before any templates, plan, or code.
- Prompt templates: 6 (`implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md`, `code-reviewer.md`, `brainstorming/spec-document-reviewer-prompt.md`, `writing-plans/plan-document-reviewer-prompt.md`).

Inventory: 14 skills; 0 agent definition files (roles exist only as prompt templates); 0 slash commands; 1 hook event on Claude Code (SessionStart) with equivalents for Cursor (`hooks/hooks-cursor.json`), Pi (5 event handlers), Hermes (1); 0 rules files; 5 platform reference files; 11 helper scripts (3 SDD, 5 brainstorm server, 2 debugging, 1 graph renderer).

## Task understanding and planning

- Brainstorming classifies every request as Spike / Bounded / Architectural and must say the classification aloud before the first question (`skills/brainstorming/SKILL.md:22-53`). "When in doubt ... take the heavier one. The ratchet is one-way" (`:50-52`). A `<HARD-GATE>` forbids any implementation action before explicit human approval on every path (`:14-20`, `:55-61`).
- Architectural path: one question per message (`:170-172`), 2-3 approaches with a recommendation (`:176-179`), sectioned design with approval per section (`:183-187`), spec written to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` and committed (`:206-209`), self-review for placeholders/contradictions/scope/ambiguity (`:211-220`), then writing-plans only (`:229-231`).
- writing-plans produces `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` with a required header naming the spec and a Global Constraints block (`skills/writing-plans/SKILL.md:56-80`), per-task Files/Interfaces blocks (`:85-96`), 2-5 minute steps with literal test and implementation code (`:45-52`, `:98-128`), a No Placeholders rule (`:131-139`), and a self-review for spec coverage and type consistency (`:141-151`).
- Bounded path skips the spec and plan: short design in chat, stop for yes, then implement with TDD (`skills/brainstorming/SKILL.md:88-92`).

## Context selection and repository understanding

No indexing, embeddings, or retrieval code exists. Context selection is instruction-only:
- "Explore project context — check files, docs, recent commits" (`skills/brainstorming/SKILL.md:88`, `:166`).
- Subagents get curated context, never the controller's history: task brief file, interfaces from earlier tasks, global constraints, report path (`skills/subagent-driven-development/SKILL.md:251-271`); "Never make a subagent read the whole plan file" (`:261-262`). `scripts/task-brief` extracts one task by awk on `Task N` headings (`:28-34`).
- Reviewers read one diff file produced by `scripts/review-package` (`git log --oneline`, `git diff --stat`, `git diff -U10` over BASE..HEAD, `:32-43`) and are told the context lines are the changed files; "Do not crawl the broader codebase" (`task-reviewer-prompt.md:38-50`).
- Debugging: read stack traces, reproduce, `git diff`, instrument component boundaries, trace backward (`skills/systematic-debugging/SKILL.md:52-118`; `root-cause-tracing.md`).

## Memory across sessions

- No user or project memory store. Nothing learns preferences.
- Persisted artifacts: specs and plans committed to `docs/superpowers/` (`brainstorming/SKILL.md:206-209`; `writing-plans/SKILL.md:18`). The repo itself contains 36 such files under `docs/superpowers/` from dogfooding.
- SDD ledger `<repo>/.superpowers/sdd/<plan-basename>/progress.md`, git-ignored via a self-writing `.gitignore` (`scripts/sdd-workspace:35-39`). Purpose is compaction recovery: "Conversation memory does not survive compaction ... controllers that lost their place have re-dispatched entire completed task sequences" (`subagent-driven-development/SKILL.md:131-134`); resume logic at `:141-152`. Deleted when the branch finishes (`:482-484`).
- Brainstorm visual sessions persist under `.superpowers/brainstorm/` when `--project-dir` is passed (`skills/brainstorming/scripts/start-server.sh:9-10`).
- Personal skills in `~/.claude/skills/` are the suggested place for reusable learnings (`skills/writing-skills/SKILL.md:12`).

## Verification: what counts as done

- TDD: "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"; code written before a test must be deleted (`skills/test-driven-development/SKILL.md:31-45`); verify RED and GREEN mandatory (`:113-183`).
- verification-before-completion: no success claim without running the command in the same message; regression tests must be shown to fail when the fix is reverted (`skills/verification-before-completion/SKILL.md:14-36`, `:82-86`); agent reports are not evidence, VCS diff is (`:47`, `:100-104`).
- SDD: implementer writes a report with RED/GREEN command output (`implementer-prompt.md:130-139`); task reviewer returns two verdicts, spec compliance and quality, treats the report as "unverified claims" and does not re-run suites (`task-reviewer-prompt.md:64-92`, `:94-160`); scoped re-review verdicts each finding ADDRESSED/NOT ADDRESSED (`re-review-prompt.md:80-100`); final whole-branch review on the most capable model (`SDD/SKILL.md:445-456`).
- finishing-a-development-branch runs the full suite before the menu and again on the merged result (`skills/finishing-a-development-branch/SKILL.md:14-26`, `:98-104`); using-git-worktrees runs a baseline suite (`:121-132`).
- No browser/UI verification. The only browser component is the brainstorm visual companion, used for design mockups, not QA (`skills/brainstorming/visual-companion.md:1-30`).
- No mechanical gate: every check is model-instructed; nothing in hooks blocks a commit or a claim.

## Multi-agent / roles

- Controller/implementer/task-reviewer/re-reviewer/final-reviewer, all defined as prompt templates dispatched to the host's generic subagent (`Subagent (general-purpose)` in every template; mapped per host in `references/*-tools.md`, `.kimi-plugin/plugin.json:25`).
- Workers are forbidden from spawning subagents (`implementer-prompt.md:50-60`; same block in all three reviewer templates), based on observed duplicate review seats (`SDD/SKILL.md:272-277`).
- Implementers return one of DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT in under 15 lines; detail goes to a report file (`implementer-prompt.md:140-153`; handling at `SDD/SKILL.md:286-302`).
- Sequential by design: "Never dispatch multiple implementation subagents in parallel" (`:282`); batch same-shape edits into one dispatch (`:223-229`). dispatching-parallel-agents is for independent failures only (`skills/dispatching-parallel-agents/SKILL.md:36-45`).
- Controller never fixes code itself (`SDD/SKILL.md:408-409`).

## Model routing

Instruction-only, in `skills/subagent-driven-development/SKILL.md:184-219`: cheap tier for 1-2 file transcription tasks, standard for integration, most capable for design and the final review; reviewers scaled to diff risk; fix rounds 4-5 escalate one tier; "Always specify the model explicitly" because an omitted model inherits the session's. Codex reference adds `reasoning_effort` and a config backstop `default_subagent_model` (`references/codex-tools.md:62-79`). Templates carry `model: [MODEL — REQUIRED ...]` (`implementer-prompt.md:8-9`). No code enforces any of this.

## Failure recovery / checkpoints

- Ledger + `git log` are the recovery map after compaction (`SDD/SKILL.md:150-152`); BASE recorded before each dispatch so multi-commit tasks are reviewed whole (`:248-249`, `:290`; `scripts/review-package:3-5`).
- Fix loop capped at 5 rounds; rounds 1-3 resume the same implementer, 4-5 fresh implementer on a stronger model; at the cap the controller adjudicates and records `Ruling:` lines, and lists all rulings in its final message (`:354-429`, `:473-480`).
- Continuous execution: the controller stops only for irreversible ops, security-sensitive actions, out-of-worktree side effects, or a plan where "every path forward is a guess" (`:17-31`).
- executing-plans stops on any blocker and asks (`skills/executing-plans/SKILL.md:40-48`). Debugging: after 3 failed fixes, stop and question architecture with the human (`systematic-debugging/SKILL.md:191-212`).
- Isolation via worktrees, with detection of existing isolation and submodule guard (`using-git-worktrees/SKILL.md:16-45`).

## Security posture (prompt injection, permissions, destructive commands)

- No permission layer, tool allowlist, or command filtering exists; the plugin defers entirely to the host.
- Prompt injection: not addressed. Reviewers are told to distrust implementer reports for accuracy (`task-reviewer-prompt.md:64-71`), not to treat file or web content as untrusted instructions. The bootstrap injects only the plugin's own file (`hooks/session-start:11`), so the hook itself is not an injection vector. The OpenCode install instruction is "Fetch and follow instructions from https://raw.githubusercontent.com/..." (`README.md:228`), a remote-instruction-following pattern.
- Destructive commands: discard requires the literal typed word `discard` (`finishing-a-development-branch/SKILL.md:135-149`, `:222`); never `git worktree remove --force` without showing the user (`:177-198`); no force-push unless explicitly requested (`:228`); SDD stop-list (`SDD/SKILL.md:27-31`); never start on main without consent (`:128-129`); `git clean -fdx` warning (`:153-154`).
- Brainstorm server: binds 127.0.0.1 by default (`skills/brainstorming/scripts/server.cjs:100`), 32-byte random key required on every request and WebSocket (`:124-125`, `:341-351`, `:445`), `timingSafeEqual` (`:321-325`), HttpOnly SameSite=Strict cookie (`:399`), WebSocket Origin check (`:377-383`), token file chmod owner-only (`:140`). Auth hardening was a dedicated spec (`docs/superpowers/specs/2026-06-10-visual-companion-auth-hardening-design.md`).

## Host coupling (what host features it depends on; portability)

Depends on: a session-start context injection mechanism (the "entire integration", `docs/porting-to-a-new-harness.md:52-58`); a skill-loading tool or file read; a subagent tool that accepts a model parameter and ideally can be resumed (fallback to fresh dispatch documented at `SDD/SKILL.md:377-379`); a todo tool; bash for the three SDD scripts and the hook (`run-hook.cmd:37-39` exits silently with no bash on Windows, so no bootstrap); git worktrees; Node for the visual companion. Skills name actions not tools (`porting:39-46`), so porting is a manifest plus a tool-map file: 12 host manifests exist at the repo root (`.claude-plugin`, `.codex-plugin`, `.cursor-plugin`, `.devin-plugin`, `.kimi-plugin`, `.hermes-plugin`, `.opencode`, `.pi`, `gemini-extension.json`, `.agents/plugins`). `.codex-plugin/plugin.json:24` declares `"hooks": {}`; how Codex gets the bootstrap was not verified from source here.

## Observability

- Ledger lines per task, fix round, ruling, and parked finding (`SDD/SKILL.md:405-406`, `:437-439`); report files per task; "Rulings I made" summary to the human (`:473-480`).
- Skills must announce "Using [skill] to [purpose]" (`using-superpowers/SKILL.md:24`) and the brainstorming classification (`brainstorming/SKILL.md:24-27`).
- `tests/claude-code/analyze-token-usage.py` parses Claude Code JSONL transcripts into main-session vs per-subagent token usage (`:1-40`). No runtime telemetry.
- Behavior evals live in a separate repo (superpowers-evals, "Drill") driving tmux sessions with an LLM judge (`docs/testing.md:26-36`); `tests/` covers only non-LLM code plus a few `claude -p` prompt tests (`tests/claude-code/README.md`).

## Trace: trivial task (border radius)

Read from `using-superpowers/SKILL.md` and `brainstorming/SKILL.md`; the outcome depends on model compliance, which I cannot observe.
1. Bootstrap (~680 tokens) is already in context. The Red Flags table ("This doesn't need a formal skill", "The skill is overkill", `:44-47`) and brainstorming's description ("modifying behavior", `brainstorming/SKILL.md:3`) push the model to invoke brainstorming before touching a file. Cost: ~3,000 tokens of skill text, one tool call.
2. Classify as Bounded, announce it (`:24-27`), explore context, ask "the clarifying questions that matter" one per message (`:88-89`), present a few-sentence design, then STOP for an explicit yes (`:90-91`, `:69`). Minimum one extra human round-trip; likely two if a clarifying question is asked.
3. using-git-worktrees may ask consent for a worktree (`using-git-worktrees/SKILL.md:41-45`): possibly a third round-trip, plus dependency install and baseline test run if accepted.
4. Implement "via normal workflow (TDD applies)" (`brainstorming/SKILL.md:92`). TDD loads ~1,800 tokens; a CSS radius has no natural failing test, and the exceptions list only prototypes/generated code/config (`test-driven-development/SKILL.md:24-27`), so the model either writes a low-value snapshot test or asks permission to skip. Then verification-before-completion (~750 tokens) before saying done.
Estimated overhead: ~5,500-7,000 tokens of instruction text loaded, 2-4 extra assistant turns, 1-3 human approvals, for a one-line change. No subagents on this path.

## Trace: hard task (auth race)

1. Bootstrap routes "Fix this bug" to systematic-debugging (`using-superpowers/SKILL.md:31`), ~1,900 tokens.
2. Phase 1 (`systematic-debugging/SKILL.md:48-118`): read the error fully, reproduce consistently ("If not reproducible -> gather more data, don't guess"), check recent changes with git, add boundary logging in the multi-component auth path and run once, trace the bad value backward (`root-cause-tracing.md`, ~960 tokens if read). This is where an intermittent race spends most turns: several instrumented runs before any edit.
3. Phase 2-3 (`:120-166`): find a working analogous flow, list differences, write one hypothesis, make the smallest change to test it.
4. Phase 4 (`:168-212`): failing test first via TDD; `condition-based-waiting.md` (~650 tokens) prescribes polling a condition instead of sleeps, which is the relevant technique for race tests. Then verification-before-completion's revert-and-rerun for the regression test (`verification-before-completion/SKILL.md:82-86`). After three failed fixes the skill forces a stop to discuss architecture (`:198-212`).
5. If the race surfaces as several unrelated failing test files, dispatching-parallel-agents applies (`dispatching-parallel-agents/SKILL.md:36-40`, race example at `:94-113`); otherwise no subagents.
Estimated overhead: ~4,000-6,000 tokens of skill text; extra turns are dominated by mandated reproduction and instrumentation (likely 5-15 tool calls before the first edit). Human gates only on "I don't understand X" (`:162-166`) or the 3-fix breaker. No spec or plan is written; brainstorming is not on this path. "No root cause" handling (retry/timeout) is allowed only after the full process (`:266-275`).

## Strengths (ranked, concrete, cited)

1. Controller context hygiene is engineered, not just advised: task briefs, review packages, and report files are passed by path so diffs and task text never enter the controller (`SDD/SKILL.md:231-233`, `:263-266`, `:316-324`; `scripts/task-brief`, `scripts/review-package`).
2. Compaction-safe execution via a plan-scoped ledger with explicit resume rules and BASE-recorded ranges (`SDD/SKILL.md:131-152`; `scripts/sdd-workspace:6-9`).
3. Bounded fix loop with model escalation, a breaker, and an audit trail of rulings surfaced to the human (`SDD/SKILL.md:354-429`, `:473-480`).
4. Skills are treated as tested code: baseline-without-skill, pressure scenarios, rationalization capture (`skills/writing-skills/testing-skills-with-subagents.md:1-50`; `skills/systematic-debugging/CREATION-LOG.md`, `test-pressure-*.md`).
5. Portability by design: action vocabulary plus per-host tool maps, one skill body across 12 hosts (`docs/porting-to-a-new-harness.md:38-70`).
6. Destructive-action discipline in finishing (typed `discard`, no `--force`, no force-push) (`finishing-a-development-branch/SKILL.md:132-198`, `:212-228`).

## Weaknesses (ranked, concrete, cited)

1. No enforcement: every gate is a sentence the model may ignore; the repo's own CLAUDE.md admits agents routinely violate its guidelines (`CLAUDE.md:7-8`). No hook blocks a commit, a claim, or a skipped review.
2. Fixed ceremony on trivial work: the 1% rule (`using-superpowers/SKILL.md:11`) plus "the approval gate never does [scale]" (`brainstorming/SKILL.md:18-19`, `:55-61`) impose multi-turn approval on one-line edits (see trivial trace).
3. Instruction volume: SDD alone is 4,825 words (~6,300 tokens) and a full workflow loads ~16k tokens of process text before any project content; rationalization tables are repeated in nearly every skill.
4. TDD absolutism ("Write code before the test? Delete it", `test-driven-development/SKILL.md:37-45`) fits poorly for CSS, config, and exploratory work; exceptions require asking.
5. Windows: the hook silently does nothing without Git bash at a hardcoded path or on PATH (`hooks/run-hook.cmd:21-39`); JSON is hand-escaped in bash (`hooks/session-start:16-24`).
6. `task-brief` depends on `Task N` heading format (`scripts/task-brief:28-34`); `review-package` uses `-U10` diffs that can be very large for a big task, and the reviewer is told to read it once (`task-reviewer-prompt.md:38-42`).
7. Model routing exists only as prose; nothing verifies a model was set (`SDD/SKILL.md:204-206`).

## Genuinely innovative vs mostly prompt engineering

Mostly prompt engineering, deliberately (`CLAUDE.md:38-40`, zero dependencies). The parts that go beyond prompt text: (a) file-handoff scripts that make subagent context isolation mechanical rather than aspirational; (b) the ledger as a compaction-recovery structure derived from observed failures (`SDD/SKILL.md:131-134`); (c) the RED/GREEN methodology for authoring behavior-shaping docs, grounded in a cited persuasion study (`skills/writing-skills/persuasion-principles.md:1-8`); (d) the harness-portability contract (actions not tools). The brainstorm visual companion (`server.cjs`, 723 lines) is real software but peripheral.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Twelve host manifests and five tool-map files to keep in sync (root dotdirs; `scripts/sync-to-codex-plugin.sh`, `scripts/bump-version.sh`, `.version-bump.json`).
- 36 dogfooding specs/plans shipped in `docs/superpowers/` inside the plugin.
- Repeated Red Flags / Common Rationalizations tables across 10+ skills; `anthropic-best-practices.md` (5,803 words) bundled as a reference.
- Sequential-only implementation (`SDD/SKILL.md:282`) plus per-task review and re-review means at least 2 subagent dispatches per task and up to 11 in a bad loop; a real session's final-review fix wave "cost more than all its tasks combined" (`:459-461`).
- The bootstrap re-injects on every `compact` (`hooks/hooks.json:5`); harmless but the Pi adapter needs marker checks to avoid double injection (`.pi/extensions/superpowers.ts:37`, `.opencode/plugins/superpowers.js:133`).
- `receiving-code-review` forbids any gratitude wording (`:139-148`), a stylistic rule with its own enforcement text.

## Reusable pieces (specific files or ideas, and the license terms for reuse)

MIT for all repo-authored content, attribution required (`LICENSE`). Directly reusable:
- `skills/subagent-driven-development/scripts/{sdd-workspace,task-brief,review-package}` (bash, ~130 lines total).
- Prompt templates: `implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md`, `requesting-code-review/code-reviewer.md` (status contract, no-subagents clause, read-only clause, severity calibration).
- `hooks/session-start` + `hooks/run-hook.cmd` as a cross-host context-injection pattern; `.pi/extensions/superpowers.ts` and `.opencode/plugins/superpowers.js` as adapter references.
- `skills/systematic-debugging/condition-based-waiting.md`, `find-polluter.sh`, `root-cause-tracing.md`.
- `skills/writing-skills/persuasion-principles.md`, `testing-skills-with-subagents.md` (method for evaluating instruction text).
- `skills/finishing-a-development-branch/SKILL.md` destructive-action rules.
- `tests/claude-code/analyze-token-usage.py` for transcript cost breakdowns.
Caution: `skills/writing-skills/anthropic-best-practices.md` reproduces Anthropic guidance; its license is not the repo's MIT and should be checked before redistribution.

## Must not copy

- The coercive bootstrap wording ("1% chance", "You cannot rationalize your way out", `using-superpowers/SKILL.md:10-16`) and the never-scaling approval gate as-is; they are the source of the trivial-task overhead. Adopt the routing idea, not the absolutism.
- "Your human partner" voice and the project-specific contributor policy (`CLAUDE.md`); the maintainers state the terminology is deliberate to their project.
- The "fetch and follow instructions from a URL" install pattern (`README.md:228`).
- `anthropic-best-practices.md` verbatim (license unclear).
- Skill bodies verbatim as a compliance shortcut; the maintainers say the content is tuned by evals and rejects untested rewording (`CLAUDE.md:38-40`, `:96-102`), so a fork inherits tuning it cannot re-validate.

## Transferable abstractions (name each, one line)

- Bootstrap-as-integration: one always-loaded router file, everything else on demand.
- Action vocabulary + per-host tool map: skills say "dispatch a subagent", a table says what that is here.
- Three-path triage (spike/bounded/architectural) with a one-way ratchet.
- Hard gate: no implementation before stated intent is approved.
- Rationalization table: enumerate the excuses a model uses and rebut each inline.
- File handoff: briefs, reports, and diff packages by path, never pasted into the controller.
- Plan-scoped ledger: append-only progress file that survives compaction and drives resume.
- Recorded BASE per task so review ranges are exact.
- Bounded fix loop with tier escalation and a breaker.
- Rulings log: every controller decision written down and surfaced at the end.
- Scoped re-review: verdict listed findings, flag only new breakage in the fix diff.
- No-subagents-for-workers contract to prevent duplicate review seats.
- Model tier per role, always explicit.
- Status contract (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT) with detail in a file.
- Evidence-before-claims: name the command, run it, read it, then claim.
- Typed-confirmation for irreversible actions.
- Red/green testing of instruction text with baseline runs.

## Open questions that need a probe run to answer

1. Does brainstorming actually trigger on a one-line CSS request, and how many turns does the approval gate cost in practice?
2. Real controller token growth over a 10-task SDD plan, including template re-reads and dispatch prompts (`analyze-token-usage.py` could measure it).
3. How often the fix loop reaches rounds 4-5, and whether the model escalation changes the outcome.
4. Whether "resume the original implementer" works on Claude Code (it needs a resumable agent handle) or always falls back to a fresh dispatch.
5. Whether compaction actually preserves enough for the ledger resume rules to work, or the controller re-dispatches anyway.
6. How Codex receives the bootstrap given `"hooks": {}` in `.codex-plugin/plugin.json`.
7. Behavior on Windows without Git bash (the hook exits 0 silently) and whether the user is ever told.
8. Whether small/cheap models thrash under the 1% rule (the repo has Haiku-specific tests at `tests/explicit-skill-requests/run-haiku-test.sh`).
9. Reviewer quality when `review-package` output exceeds the reviewer's practical read size.
10. Whether the TDD "delete the code" rule is followed or silently ignored in practice.
