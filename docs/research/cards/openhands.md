# openhands

- Repo: https://github.com/All-Hands-AI/OpenHands redirects to https://github.com/OpenHands/OpenHands. That repo is now ONLY the "Agent Canvas" React/TypeScript frontend (`AGENTS.md` lines 27-40: "This repo is only the agent-canvas frontend"). All agent logic moved to https://github.com/OpenHands/software-agent-sdk, which was cloned and studied as the primary source.
- Frontend (OpenHands/OpenHands): commit `7e5191c42e8dbb2e24b4f907a099fa05e57e8f47`, 2026-09-09, MIT (`LICENSE`), TypeScript (946 .ts + 945 .tsx of 2207 files).
- SDK (OpenHands/software-agent-sdk): commit `6a1e4d0f08dcdd02786526a51b7965e1877008bc`, 2026-09-09, MIT (`LICENSE`), Python (1289 .py of 1678 files). Four packages: `openhands-sdk`, `openhands-tools`, `openhands-agent-server`, `openhands-workspace`.
- Path shorthand below: `sdk:` = `openhands-sdk/openhands/sdk/`, `tools:` = `openhands-tools/openhands/tools/`, `server:` = `openhands-agent-server/openhands/agent_server/`, `ws:` = `openhands-workspace/openhands/workspace/`, `fe:` = frontend repo root.

OpenHands is an append-only event-sourced coding agent. A `LocalConversation` owns a file-backed `EventLog`; an `Agent` each step projects the log into a `View`, optionally condenses it via an LLM-summarizing tombstone mechanism, calls the LLM with tool schemas, and executes returned tool calls in parallel threads. Tools (tmux terminal, str_replace file editor, task tracker, browser, sub-agent delegation) run either in-process (`LocalWorkspace`) or inside a Docker/Apptainer/cloud container running `openhands-agent-server`, which the frontend talks to over REST+WebSocket. Skills (ex-"microagents") are keyword/path/task-triggered markdown injected into user or tool messages. Everything (agent, condenser, security analyzer, workspace) is a Pydantic discriminated-union model so conversations serialize and resume.

## Request flow (cite files)

1. Entry: `Conversation(agent=..., workspace=cwd)` then `send_message()` and `run()` (`examples/01_standalone_sdk/01_hello_world.py`). Over the wire: frontend `fe:src/api/agent-server-conversation-service` -> `server:conversation_router.py` -> `server:conversation_service.py` (`ConversationService`, line 675) -> same `LocalConversation`.
2. `send_message()` (`sdk:conversation/impl/local_conversation.py` 1813-1868): resets FINISHED/STUCK to IDLE, runs `agent_context.get_user_message_suffix()` for keyword-triggered skills, emits a `MessageEvent(source="user", extended_content=[skill text])`.
3. `run()` (same file 1908-2060): loop under state lock; breaks on PAUSED/STUCK; on FINISHED runs Stop hooks (can deny and push a feedback message); `_check_stuck_or_nudge()`; then `agent.step()`; then budget check (`_budget_exceeded_detail`) and `max_iteration_per_run` (default 500, line 217).
4. `Agent.step()` (`sdk:agent/agent.py`): executes pending unconfirmed actions first; `prepare_llm_messages(state.view, condenser, llm)` (`sdk:agent/utils.py`) returns messages or a `Condensation` event (which is emitted and the step returns); `make_llm_completion` with all tools; response classified TOOL_CALLS / CONTENT / REASONING_ONLY / EMPTY (`sdk:agent/response_dispatch.py`).
5. Tool calls -> `ActionEvent` per call (security_risk + ~10-word `summary` popped from arguments), critic optionally scored, `_ActionBatch.prepare` truncates after `FinishTool`, partitions hook-blocked actions, runs the rest via `ParallelToolExecutor` (`sdk:agent/parallel_executor.py`), emits `ObservationEvent`/`AgentErrorEvent` in original order, then `finalize` sets FINISHED or injects an iterative-refinement follow-up.

## Event stream model

- `Event` base (`sdk:event/base.py`): frozen Pydantic, `id`, `timestamp`, `source` (agent/user/environment), `parent_id` (conversation tree; forks share parents). `LLMConvertibleEvent.to_llm_message()` is the only path into the model; `events_to_messages()` re-batches parallel `ActionEvent`s sharing `llm_response_id` into one assistant message and coalesces adjacent plain user messages.
- Types: `SystemPromptEvent` (static prompt + dynamic_context as two content blocks + tool defs, `sdk:event/llm_convertible/system.py`), `MessageEvent`, `ActionEvent` (thought, reasoning_content, thinking_blocks, action, tool_call, security_risk, summary, critic_result — `sdk:event/llm_convertible/action.py`), `ObservationEvent` / `UserRejectObservation` / `AgentErrorEvent` (`observation.py`), `Condensation` / `CondensationRequest` / `CondensationSummaryEvent` (`sdk:event/condenser.py`), plus non-LLM `ConversationStateUpdateEvent`, `PauseEvent`, `HookExecutionEvent`, `TokenEvent`, `LLMCompletionLogEvent`.
- Persistence: `EventLog` (`sdk:conversation/event_store.py`) writes one JSON file per event `events/event-{idx:05d}-{id}.json` (`sdk:conversation/persistence_const.py`) with a flock + length-marker sidecar; `base_state.json` is the agent/state source of truth (`sdk:conversation/state.py` 430-580).
- `View` (`sdk:context/view/view.py`) is the projection: appends `LLMConvertibleEvent`s, applies `Condensation.apply()` (drop forgotten ids, insert summary at offset), then `enforce_properties` over four invariants (`sdk:context/view/properties/`): ObservationUniqueness, BatchAtomicity (all parallel calls of one response), ToolCallMatching (every tool_use has one tool_result), ToolLoopAtomicity (Anthropic thinking-block checksum). `manipulation_indices` is the intersection of legal cut points; condensers cut only there.

## What goes into the model (always-loaded vs on-demand, with token estimates)

Estimates are read from byte counts (~4 chars/token), not measured runs.
- Always (static system block, cached across conversations): 18 sections in `sdk:context/prompts/sections/static.py`, ordered in `sdk:context/prompts/presets.py`: SOUL, ROLE, MEMORY, EFFICIENCY, FILE_SYSTEM, CODE_QUALITY, VERSION_CONTROL, PULL_REQUESTS, PROBLEM_SOLVING_WORKFLOW, SELF_DOCUMENTATION, SECURITY policy, SECURITY_RISK_ASSESSMENT (on by default via `Agent._add_security_prompt_as_default`), BROWSER_TOOLS (off in cli_mode), EXTERNAL_SERVICES, ENVIRONMENT_SETUP, TROUBLESHOOTING, PROCESS_MANAGEMENT, model-specific IMPORTANT (claude/gemini/gpt-5 variants). Body text ~18.0 KB => ~4.5k tokens.
- Always (dynamic block, second content block, no cache marker): `sdk:context/prompts/sections/dynamic.py` — REPO_CONTEXT (legacy trigger-less skills e.g. AGENTS.md, wrapped in `<UNTRUSTED_CONTENT>`, unbounded), MEMORY_CONTEXT (<=6000 chars, ~1.5k tokens, `sdk:context/memory.py`), SKILLS list (name + description <=1024 chars each, `to_prompt` in `sdk:skills/skill.py` 1431), custom suffix, CUSTOM_SECRETS names, CURRENT_DATETIME last (only volatile value).
- Always (tools): terminal ~4.8 KB (`tools:terminal/descriptions.py`), file_editor ~5.4 KB, task_tracker ~6.4 KB, think ~2.5 KB, finish ~0.5 KB (`sdk:tool/builtins/`) => ~5-6k tokens; browser tool set (`tools:browser_use/definition.py`, 30 KB, 48 `browser_*` names) adds roughly 5k more. Every tool schema also gets `security_risk` and `summary` params (`sdk:llm/router/base.py` docstring, `agent.py` `_extract_summary`).
- Baseline per turn therefore ~10-11k tokens without browser, ~15k with, before any history.
- History: full `View` every turn until the condenser fires. Observations are truncated at 50,000 chars (`sdk:utils/truncate.py` `DEFAULT_TEXT_CONTENT_LIMIT`); terminal output at 30,000 chars (`tools:terminal/constants.py` `MAX_CMD_OUTPUT_SIZE`).
- On demand: `invoke_skill` tool loads a full SKILL.md (`sdk:tool/builtins/invoke_skill.py`); daily memory logs are never injected; keyword/path skills injected only when triggered.

## Condensers (each one, detailed)

Only three concrete classes exist in the SDK (grep `class .*Condenser` — the old OpenHands AmortizedForgetting/RecentEvents/BrowserOutputMasking condensers are gone).
- `CondenserBase` (`sdk:context/condenser/base.py`): `condense(view, agent_llm) -> View | Condensation`; `handles_condensation_requests()` default False. `RollingCondenser` adds `condensation_requirement()` returning HARD/SOFT/None and `get_condensation()`; on `NoCondensationAvailableException`, SOFT returns the view unchanged (retry next step), HARD tries `hard_context_reset()` then re-raises.
- `NoOpCondenser` (`no_op_condenser.py`): returns the view; testing only.
- `PipelineCondenser` (`pipeline_condenser.py`): applies a list in order, stops at the first `Condensation`.
- `LLMSummarizingCondenser` (`llm_summarizing_condenser.py`), the only production one. Fields: `llm` (separate summarizer LLM, streaming forced off), `max_size` (class default 240; `default_condenser()` uses 80 with `keep_first=4`), `max_tokens` (None), `keep_first` (2), `minimum_progress` 0.1, `hard_context_reset_max_retries` 5, scaling 0.8. Triggers (`get_condensation_reasons`): REQUEST (unhandled `CondensationRequest` in view), TOKENS (`get_total_token_count` > min(max_tokens, `agent_llm.effective_max_input_tokens`)), EVENTS (len(view) > max_size). TOKENS and REQUEST are HARD; EVENTS alone is SOFT. What it drops (`_get_forgotten_events`): keeps `keep_first` head events, keeps a tail of (target/2 - keep_first - 1) events where target is len(view) for REQUEST, `max_size` for EVENTS, or the suffix that removes enough tokens to get under max_tokens/2 for TOKENS; takes the strictest; snaps both cut points forward to the next legal `manipulation_index`. Forgotten events are rendered via `str(event)` (500-char previews per event, `N_CHAR_PREVIEW` in `event/base.py`), fed to `prompts/summarizing_prompt.j2` (asks for USER_CONTEXT, TASK_TRACKING with preserved task IDs, COMPLETED, PENDING, CURRENT_STATE, CODE_STATE, TESTS, CHANGES, DEPS, VERSION_CONTROL_STATUS), and the summary is inserted as a user-role `CondensationSummaryEvent` at the cut. Previous summaries are inside the forgotten range so they get re-summarized. Raises `NoCondensationAvailableException` if 0 events or < 10% of the view would be forgotten (e.g. one tool loop spans the view). `hard_context_reset`: summarize the entire view at offset 0, retrying up to 5 times while shrinking each event string by 20%.
- Who fires it: `Agent.step` calls it every step through `prepare_llm_messages`; on `LLMContextWindowExceedError` or `LLMMalformedConversationHistoryError` the agent emits `CondensationRequest` (after `state.rebuild_view()` for the malformed case) and returns, so the next step condenses (`agent.py` step, lines ~61-104 of the excerpt). Users can call `Conversation.condense()` (`sdk:conversation/base.py`).
- Documented rationale: `sdk:context/condenser/README.md` — halve the context regularly to bound cost and keep prompt-cache rebuilds cheap.

## Microagents

Renamed "skills"; `.openhands/microagents/` and `~/.openhands/microagents/` remain as legacy load paths (`sdk:skills/skill.py` 914-917, 1102-1107).
- Formats: AgentSkills `SKILL.md` directories (name/description/version/license/allowed-tools frontmatter, `scripts/ references/ assets/`), legacy OpenHands markdown with frontmatter `triggers`, and third-party files auto-mapped (`.cursorrules`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` -> `PATH_TO_THIRD_PARTY_SKILL_NAME`, `skill.py` ~line 380).
- Triggers (`sdk:skills/trigger.py`): `KeywordTrigger`, `TaskTrigger`, `PathTrigger` (gitignore-style globs). Matching is whole-token, case-insensitive (`_keyword_matches` regex `(?<![a-z0-9])kw(?![a-z0-9])`, so `git` does not fire on `github`). `Skill.match_trigger` returns the first keyword hit; `match_path_trigger` compiles the glob to an anchored regex.
- Injection: user-message keywords -> `AgentContext.get_user_message_suffix` (`sdk:context/agent_context.py`) renders `templates/skill_knowledge_info.j2` as `<EXTRA_INFO>` appended to that user message, deduped per conversation by `state.activated_knowledge_skills`. Path rules -> `get_tool_use_suffix` appends `<EXTRA_INFO>` to the tool `ObservationEvent.extended_content` when the agent touches a matching file. Trigger-less legacy skills go whole into `<REPO_CONTEXT>`; AgentSkills-format skills are listed by name/description only and loaded via `invoke_skill`.
- Sources and precedence (`skill.py` `load_project_skills`, `load_user_skills`, `load_public_skills`): project `.agents/skills` > `.openhands/skills` > `.openhands/microagents`; user `~/.agents/skills` > `~/.openhands/skills` > `~/.openhands/microagents`; public skills cloned from `OpenHands/extensions` into `~/.openhands/skills-cache/` filtered by a marketplace JSON. `disabled_skills` is the deny-list. Claude/Gemini-named repo files are gated by model family (`agent_context.py` `_resolve_dynamic_data`).
- Known gap: `send_message` has `# TODO(calvin)` — activated skill names are not carried through condensation, so after a summary the injected skill text can be lost and will not re-fire (`local_conversation.py` ~1848).

## Tools / actions

- Registry: `Tool(name=...)` specs resolved from a name registry (`sdk:tool/registry.py`); `ToolDefinition[Action, Observation]` generic with Pydantic action schemas; MCP tools wrapped as `MCPToolDefinition` (`sdk:mcp/`).
- Default set (`tools:preset/default.py` `get_default_tools`): `TerminalTool`, `FileEditorTool`, `TaskTrackerTool`, `BrowserToolSet` (unless cli_mode), optional `TaskToolSet` for sub-agents; built-ins `FinishTool`, `ThinkTool` always (`sdk:tool/builtins/__init__.py` `BUILT_IN_TOOLS`), plus conditional `InvokeSkillTool`, `SwitchLLMTool`, `vision_inspect`.
- Terminal (`tools:terminal/`): persistent tmux session (`terminal/tmux_terminal.py`, subprocess and PowerShell fallbacks), soft timeout with `is_input` continuation, secrets exported as env vars when the key name appears in the command and masked in output (`impl.py` 317-377). Windows swaps the tool to `execute_powershell` and rewrites prompt text (`static.py` `_refine`).
- File editor (`tools:file_editor/definition.py`): `view/create/str_replace/insert/undo_edit`, absolute paths, returns old/new content.
- Others: `task_tracker` (plan list with statuses), `planning_file_editor`, `apply_patch`, `glob`, `grep`, `browser_use`, `ask_oracle` (consults an LLM profile named "oracle"), `tom_consult`, `delegate`, `task`, `workflow`.
- Tool errors (`ValueError`, validation) become `AgentErrorEvent` with `AGENT_OUTCOME` classification so the model self-corrects (`agent.py` `_execute_action_event`).

## Runtime and sandbox

- `BaseWorkspace` (`sdk:workspace/base.py`): `execute_command`, `file_upload/download`, `git_changes/diff`, `pause/resume`, cost accounting. `LocalWorkspace` runs on the host with full filesystem access (README "Option 1: Without a Sandbox" warning).
- `RemoteWorkspace` talks HTTP to an agent-server; `DockerWorkspace` (`ws:docker/workspace.py`) starts `ghcr.io/openhands/agent-server:latest-python`, random host port 30000-39999, forwards `SESSION_API_KEY`; `DockerDevWorkspace` builds images; `ws:apptainer/`, `ws:cloud/`, `ws:remote_api/` variants.
- Container image (`server:docker/Dockerfile`): python:3.13-bookworm builder, non-root user via `useradd`, installs tmux/git/sudo, `EXPOSE ${PORT}`; PyInstaller binary variant.
- Agent server (`server:api.py`, `sockets.py`): FastAPI; WebSocket first-message auth with session API key; binding to 0.0.0.0 without a key is guarded (`server:__main__.py` `_WILDCARD_HOSTS`). `RemoteConversation` (`sdk:conversation/impl/remote_conversation.py`) mirrors events to the client; `LLMCompletionLogEvent` streams completion logs out of the container.
- Isolation is container-level only; no seccomp/network policy visible in the SDK (inferred from Dockerfile and workspace files read).

## Evaluation harness

Not in either repo. `.agents/skills/run-eval.md` and `.agents/skills/manage-evals/references/eval-infrastructure.md` describe a three-repo pipeline: `software-agent-sdk/.github/workflows/run-eval.yml` (PR labels `run-eval-1/50/200/500`, release trigger at 50) dispatches `OpenHands/evaluation` `eval-job.yml`, which runs runners from `OpenHands/benchmarks` (swebench, swebenchpro, swebenchmultimodal, gaia, swtbench, commit0, multiswebench, terminalbench, programbench); results to GCS `openhands-evaluation-results`, up to 256 parallel runtimes. In-SDK eval support is limited to `AgentFinishedCritic` (`sdk:critic/impl/agent_finished.py`: score 1.0 iff last action is Finish and git patch non-empty) and `EmptyPatchCritic`.

## Task understanding and planning

- No separate planner in the default loop; the PROBLEM_SOLVING_WORKFLOW prompt section (explore -> analyze -> test -> implement -> verify) is the plan. `TaskTrackerTool` gives an explicit checklist, and the summarizer prompt is told to preserve task IDs.
- A distinct "planning" preset (`sdk:context/prompts/sections/planning.py`, `tools:preset/planning.py`) replaces the whole static prompt with a read-only Planning Agent that writes `.agents_tmp/PLAN.md` and asks clarifying questions; wired by `examples/01_standalone_sdk/24_planning_agent_workflow.py`.
- `ThinkTool` is a no-op scratchpad tool.

## Memory across sessions

- Default: prompt tells the agent to use `AGENTS.md` as persistent memory and to grep `workspace/conversations/` for past event histories (`static.py` `MemorySection._AGENTS_MD_GUIDANCE`).
- Opt-in `AgentContext.load_memory` (`agent_context.py`; `server:conversation_service.py` `_with_load_memory`): two tiers, `~/.openhands/memory/MEMORY.md` and `<workspace>/.openhands/memory/MEMORY.md`, read by `sdk:context/memory.py` `load_memory`, 6000-char budget split evenly and truncated from the top, injected as `<MEMORY_CONTEXT>` marked untrusted; `YYYY-MM-DD.md` daily logs never auto-loaded. The agent is instructed to write them itself; no automatic extraction.
- Conversation persistence/resume via `base_state.json` + event files; forks via `parent_id` (`local_conversation.py` ~781-900).

## Verification: what counts as done

- Done = the model calls `FinishTool` (`sdk:tool/builtins/finish.py`) or returns plain content (`_handle_content_response` sets FINISHED, inferred from dispatch). Nothing checks tests ran.
- Optional gates: critic `iterative_refinement` (score < threshold, default 0.6, up to 3 retries, `sdk:critic/base.py`) injects a "task appears incomplete" user message via `_ActionBatch.finalize`; Stop hooks can deny finishing (`run()`); `/goal` loop (`sdk:conversation/goal/`) uses a second LLM judge with `JUDGE_PROMPT` that demands "authoritative evidence" and returns strict JSON `{score, complete, missing}`, unparseable => score 0 and keep working.

## Multi-agent / delegation

- `TaskToolSet` (`tools:task/`): `TaskAction(description, prompt, subagent_type, resume)`; `manager.py` creates a child `LocalConversation` with its own agent, inherits or overrides `max_iteration_per_run`, updates parent metrics. Built-in subagents as markdown (`tools:preset/subagents/`): general-purpose, code-explorer (read-only terminal), bash-runner, web-researcher. File-based agents from `.agents/agents/*.md` / `.openhands/agents/*.md` with first-registration-wins precedence (`sdk:subagent/AGENTS.md`, `registry.py`); frontmatter supports `tools`, `skills`, `model`, `permission_mode`, `condenser`, budgets. Body becomes `system_message_suffix` (appended, not replacing).
- `DelegateTool` (`tools:delegate/`): `spawn` ids/agent_types then `delegate` tasks dict, parallel.
- `ACPAgent` (`sdk:agent/acp_agent.py`, 4551 lines) wraps Claude Code / Gemini CLI / Codex as the agent via Agent Client Protocol; OpenHands supplies prompt-only context.

## Model routing

- `RouterLLM` (`sdk:llm/router/base.py`): subclass of `LLM` with `llms_for_routing` and `select_llm(messages)`; implementations `MultimodalRouter` (vision model when images present) and `RandomRouter` (`router/impl/`). `SwitchLLMTool` lets the model switch mid-conversation; `fallback_strategy.py` for provider failover; LLM profiles store (`llm_profile_store.py`). Condenser uses its own `llm` (default: same model with `usage_id="condenser"`, `tools:preset/default.py`).

## Failure recovery

- `StuckDetector` (`sdk:conversation/stuck_detector.py`): scans last 20 events since the last user message for identical action/observation repeats, action/error repeats (nudge message once at threshold, STUCK after threshold+1), agent monologue, alternating A/B patterns; context-window-error loop check is a stub returning False. STUCK ends the run; a new user message resets.
- LLM errors in `step`: malformed function call -> user-role error message; content-policy block -> nudge; context/malformed-history -> `CondensationRequest`; `MaxBudgetReached` / `MaxIterationsReached` -> `ConversationErrorEvent` and ERROR status. Crash recovery synthesizes `AgentErrorEvent` for in-flight tool calls (`properties/observation_uniqueness.py` docstring).
- `hard_context_reset` as last resort. `run()` wraps everything in `ConversationRunError` carrying the persistence dir.

## Security posture

- Actor-side: LLM annotates every tool call with `security_risk` (LOW/MEDIUM/HIGH) using the SECURITY_RISK_ASSESSMENT prompt; `LLMSecurityAnalyzer` just returns it (`sdk:security/llm_analyzer.py`). `ConfirmationPolicy` `AlwaysConfirm`/`NeverConfirm` (default, `state.py` 123)/`ConfirmRisky(threshold)` decides confirmation; HIGH or UNKNOWN-without-analyzer always confirms (`analyzer.py` `should_require_confirmation`).
- Independent: `defense_in_depth/` (pattern scanner + `policy_rails.py` fetch-to-exec, raw-disk-op, catastrophic-delete on a shell AST `_shell_ast.py`), `ToolShieldLLMSecurityAnalyzer` (separate guardrail LLM over action history), `GraySwanAnalyzer` (Cygnal API), `EnsembleSecurityAnalyzer` (worst-case fusion).
- Hooks (`sdk:hooks/types.py`): PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/SessionEnd/Stop shell scripts fed JSON on stdin; can block actions (`UserRejectObservation(rejection_source="hook")`).
- Prompt-injection framing: repo files and memory wrapped in `<UNTRUSTED_CONTENT>`; supply-chain rules in the risk prompt; skill `<location>` deliberately omitted so the model must use `invoke_skill`. Secrets masked in terminal output; `secret_registry.py` encrypts at rest with Fernet (`agent_context.py` `_decrypt_secrets` docstring).

## Host coupling / headless

- Headless = the Python SDK itself: ~15 lines (`examples/01_standalone_sdk/01_hello_world.py`); async `arun()`; remote via `RemoteConversation`. No `openhands` CLI in either repo; SELF_DOCUMENTATION prompt references a CLI docs page, so a separate CLI repo exists (not studied).
- Frontend coupling is via a generated `@openhands/typescript-client` only (`fe:src/api/no-direct-agent-server-calls.test.ts` CI guard); runtime service URLs are passed to agents as a context suffix (`fe:docs/architecture.md`). Agent server also exposes OpenAI-compatible endpoints (`server:openai/`) and PostHog/HTTP telemetry (`server:telemetry/`).

## Observability

- Laminar tracing via `@observe` on `agent.step`, `conversation.run`, tools, condenser (`sdk:observability/laminar.py`). Per-conversation `ConversationStats` (`conversation_stats.py`) with per-`usage_id` metrics (agent vs condenser vs critic). `log_completions=True` writes every LLM request/response; rich `visualize` on every event for the terminal visualizer (`sdk:conversation/visualizer/default.py`). `AgentErrorEvent.classification` (`event/error_classification.py`) gives structured failure kinds.

## Trace: trivial task (border radius)

User sends "change the submit button border radius to 8px". `send_message` finds no keyword skill (unless a repo skill lists "button"), emits the MessageEvent. `run()` -> `step()`: view is [SystemPrompt, Message]; condenser sees 2 events, no reason, returns view. LLM gets ~11k tokens of prompt + tools. Following EFFICIENCY/PROBLEM_SOLVING it will typically issue one `terminal` `grep -rn "border-radius\|rounded" src/` (tmux, output capped 30k chars), then `file_editor str_replace` on the CSS/Tailwind class, both annotated LOW risk and auto-summarized. `NeverConfirm` means no pause. It may run a build/test per prompt section 5 but the prompt says to consult the user if tests are not set up. Then `FinishTool` with a summary -> FINISHED. Expected 3-5 steps; each step re-sends the whole view (no incremental caching beyond provider prompt cache on the static block). No verification that the UI actually changed unless a browser tool is used.

## Trace: hard task (auth race)

"Fix an intermittent auth race condition." Same entry; TROUBLESHOOTING section instructs 5-7 hypotheses only after repeated failures, so the first pass is exploration via grep/cat (code-explorer sub-agent only if `TaskToolSet` is enabled). PROBLEM_SOLVING says write a reproducing test first; for an intermittent race the model will likely loop `pytest -x` runs. Failure modes visible in code: identical `pytest` action + identical failing observation 3-4 times trips `_is_stuck_repeating_action_observation` and halts the run as STUCK (thresholds in `conversation/types.py`), which is wrong for a flaky test being re-run deliberately. As the view passes 80 events, `LLMSummarizingCondenser` forgets the middle half; the summary prompt captures TESTS/CHANGES but tool outputs are pre-truncated to 500-char previews, so stack traces from the early reproduction are lost — the agent must re-run them. No goal judge unless `/goal` is used; the agent decides done itself, and `AgentFinishedCritic` would pass on any non-empty patch. Hook-based Stop denial or `iterative_refinement` are the only automatic re-checks.

## Strengths (ranked, concrete, cited)

1. Event-sourced, append-only log with tombstone condensation and provable view invariants (`event_store.py`, `event/condenser.py`, `context/view/properties/`) — resumable, forkable, debuggable, and API-shape-safe (Anthropic tool_use pairing, thinking-block atomicity).
2. Condensation policy is explicit and bounded: HARD vs SOFT, minimum-progress guard, hard reset with shrinking retries, and re-summarizing prior summaries (`llm_summarizing_condenser.py`, `condenser/README.md`).
3. Prompt as typed sections with cache tiers and guards (`prompts/section.py`, `presets.py`), datetime deliberately last for cache stability.
4. Layered security that separates actor and judge: LLM self-rating + shell-AST policy rails + optional guardrail LLM + ensemble (`security/`), and untrusted-content framing of repo files.
5. Everything is a serializable discriminated union (`DiscriminatedUnionMixin`), so agent, condenser, analyzer, and workspace configs round-trip through `base_state.json` and REST.
6. Skills are format-agnostic (AgentSkills, legacy, `.cursorrules`, `CLAUDE.md`) with progressive disclosure and path-scoped rules (`skills/skill.py`, `agent_context.py`).

## Weaknesses (ranked, concrete, cited)

1. Summaries are built from 500-char event previews (`str(event)`, `N_CHAR_PREVIEW`), so condensation discards most tool output detail; the condenser LLM never sees full observations.
2. Stuck detector cannot distinguish deliberate retries from loops and its context-window-loop check is a stub (`stuck_detector.py` `_is_stuck_context_window_error` returns False).
3. Skill activation is not condensation-aware (`TODO(calvin)` in `local_conversation.py`); triggered knowledge silently vanishes after a summary.
4. Baseline prompt cost is high: ~10-15k tokens of instructions/tools every turn, including a 2.5 KB SECURITY policy and self-documentation marketing text (`static.py` `SelfDocumentationSection`).
5. "Done" is unverified by default; critics are thin (`agent_finished.py` checks only Finish + non-empty patch).
6. The 4551-line `acp_agent.py` and 3123-line `local_conversation.py` are monoliths; the frontend `AGENTS.md` is 700 lines of accreted notes.
7. `LocalWorkspace` default gives the agent host filesystem access; sandboxing is opt-in via Docker.

## Genuinely innovative vs mostly prompt engineering

- Innovative: tombstone `Condensation` events over an immutable log plus `manipulation_indices` computed from API-shape properties; HARD/SOFT condensation requirement with hard reset; two-tier cache-aware system prompt; shell-AST policy rails; path-triggered rules injected into tool observations.
- Mostly prompt engineering: the PROBLEM_SOLVING/TROUBLESHOOTING/EFFICIENCY sections, model-family IMPORTANT blocks, the summarizer template, the goal judge, security self-rating.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Full view re-serialized every step; `View.from_events` is O(n) with enforcement, mitigated only by an incremental cache (`agent/utils.py` docstring, issue 3053).
- Sync and async code paths duplicated line-for-line (`step`/`astep`, `condense`/`acondense`, `run`/`arun`).
- Per-tool `security_risk` + `summary` parameters cost output tokens on every call and rely on the actor's honesty.
- 48 browser tool names in one tool set inflate the schema when enabled.
- Windows support by regex-rewriting prompt text `bash` -> `powershell` (`static.py` `_refine`) is brittle by the authors' own comment.
- Skill keyword matching is plain substring-token matching on every user message; a common word as a trigger injects the whole skill.

## Reusable pieces (specific files or ideas, and the license terms for reuse)

MIT (both repos; attribution + license notice required, no copyleft).
- `sdk:context/view/` (View, properties, manipulation indices) and `sdk:event/condenser.py` — the tombstone/projection pattern, ~600 lines, dependency-light.
- `sdk:context/condenser/llm_summarizing_condenser.py` + `prompts/summarizing_prompt.j2` — cut-point selection and structured summary schema.
- `sdk:context/prompts/section.py`, `registry.py`, `presets.py` — cache-tiered prompt sections with guards.
- `sdk:conversation/stuck_detector.py` — pattern definitions, minus the thresholds.
- `sdk:security/defense_in_depth/policy_rails.py` + `_shell_ast.py` — composed-threat rails.
- `sdk:skills/skill.py` `_keyword_matches`, `path_matches_glob`, `to_prompt` — trigger and progressive-disclosure listing.
- `sdk:conversation/goal/judge.py` + `prompts.py` — evidence-demanding completion judge.
- `sdk:context/memory.py` — two-tier MEMORY.md loader with fair-share truncation.

## Must not copy

- Prompt text that references OpenHands brand/docs (`SelfDocumentationSection`, `Co-authored-by: openhands`) — not license-restricted, just wrong for another product.
- `LocalWorkspace` host-access default and `NeverConfirm` default policy.
- The summarizer's 500-char preview truncation.
- Frontend `AGENTS.md`-style accreted notes as documentation.

## Transferable abstractions (name each, one line)

- Condensation-as-event: forget by appending a tombstone, never by mutating history.
- Manipulation indices: derive legal cut points from provider message-shape invariants.
- HARD/SOFT condensation requirement with graceful skip vs forced hard reset.
- Cache-tiered prompt sections: static (cross-conversation cache) vs dynamic, volatile value last.
- Progressive skill disclosure: list name+description, load body via a tool; triggers inject into the message that caused them.
- Path-scoped rules injected into tool observations rather than the system prompt.
- Actor-annotated risk + independent policy rails + confirmation policy as three separable layers.
- Critic/iterative-refinement hook on `Finish` and a separate evidence-based goal judge.
- Sub-agents as markdown with first-registration-wins precedence and inherited budgets.
- Per-usage_id metrics so condenser/critic cost is attributable.

## Open questions that need a probe run to answer

- Actual rendered token count of the default static + dynamic + tool block for Claude and GPT-5 (estimated 10-15k here).
- How often the EVENTS trigger (80) fires before the TOKENS trigger on a 200k-context model, and the quality loss from 500-char previews in summaries.
- False-positive STUCK rate on legitimate repeated test runs.
- Whether skill knowledge lost after condensation measurably hurts (the TODO).
- Prompt-cache hit rate across conversations given the dynamic block has no cache marker.
- Parallel tool execution correctness with the shared tmux session (`tool_concurrency_limit`).
- Real SWE-bench numbers for this commit (only obtainable from the `OpenHands/evaluation` pipeline).
