# Host card: Claude Code

Source: official documentation at code.claude.com/docs, fetched 2026-09-09. This card records the host surface an adapter can use. Version-gated features are noted with the version the docs cite.

## Extension surfaces

| Surface | Mechanism | Notes |
|---|---|---|
| Plugin | Directory with `.claude-plugin/plugin.json`, plus `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `monitors/monitors.json`, `bin/`, `settings.json` at plugin root | Load for one session with `--plugin-dir <path>` (repeatable) or `--plugin-url`; `settings.json` may set `agent` to make a plugin agent the main thread |
| Skills | `skills/<name>/SKILL.md` with frontmatter | Only name + description are always in context (listing budget is 1% of context window; least-used skills truncated first). Body loads on invocation and then persists in the conversation. `context: fork` runs the skill in a subagent. `paths:` scopes activation. `hooks:` registers hooks when invoked. `allowed-tools`, `model`, `effort` per skill |
| Subagents | `agents/<name>.md` with frontmatter: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation: worktree` | Fresh context (no history) unless fork; returns only final message; model per subagent; `CLAUDE_CODE_SUBAGENT_MODEL` env forces default; depth limit 3, concurrency 20 |
| Hooks | `hooks.json` in plugin or `hooks` in settings; shell commands receiving JSON on stdin; exit 2 blocks where supported; JSON output with `hookSpecificOutput` for `additionalContext`, `updatedInput`, `permissionDecision` | See event table |
| MCP | `.mcp.json` in plugin or `--mcp-config` | Tool descriptions are untrusted content from the runtime's point of view |
| Instruction files | `CLAUDE.md` hierarchy (managed, user, project, local), `.claude/rules/*.md` with optional `paths:` frontmatter, `@imports` up to 4 hops, nested CLAUDE.md loaded on directory access | Delivered as a user message after the system prompt; docs state it is context, not enforcement, and recommend hooks for anything that must happen |
| Auto memory | `~/.claude/projects/<project>/memory/MEMORY.md` index (first 200 lines or 25KB loaded) plus topic files read on demand | Machine-local; frontmatter `type` field; `modified` timestamp added on write (v2.1.214+) |

## Hook events relevant to a runtime adapter

| Event | Fires | Can block | Can inject | Use in the runtime |
|---|---|---|---|---|
| `SessionStart` (matchers `startup`, `resume`, `clear`, `compact`, `fork`) | session begins or resumes | yes | `additionalContext` | load or resume the task ledger; re-inject the stage brief after compaction (matcher `compact`) |
| `UserPromptSubmit` | before Claude processes a prompt | yes (erases prompt) | `additionalContext`, `updatedInput` | intake, compile, inject stage brief |
| `PreToolUse` (matcher by tool name, e.g. `Edit\|Write`, `Bash`, `mcp__.*`) | before a tool runs | yes; `permissionDecision` allow/deny/ask; `updatedInput` | `additionalContext` | scope guard, destructive-command guard, secret guard, budget check |
| `PostToolUse` | after a tool succeeds | no (tool already ran); exit 2 shows stderr to Claude | `additionalContext`, `systemMessage` | parse test/build/lint output into evidence records; truncate floods |
| `PostToolUseFailure` | after a tool fails | no | `additionalContext` | failed-tool-call accounting; loop detection |
| `PostToolBatch` | after a parallel batch resolves, before the next model call | yes (stops the loop) | `additionalContext` | budget enforcement; forced replan point |
| `Stop` | Claude finishes responding; input includes `last_assistant_message` | yes (continues the conversation) | | evidence-contract check; bounded number of blocks then UNVERIFIED report |
| `SubagentStart` (matcher agent type) | subagent spawned | no | `additionalContext` | inject role spec for ephemeral critics |
| `SubagentStop` | subagent finishes; includes its `last_assistant_message` | yes | `additionalContext` | merge subagent evidence; require a critic to produce findings in a schema |
| `TaskCreated` / `TaskCompleted` | task list changes | yes | `updatedInput` on create | block marking a task complete without evidence |
| `PreCompact` / `PostCompact` (matchers `manual`, `auto`) | around compaction | no | | persist ledger; re-inject brief |
| `InstructionsLoaded` (matchers `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`) | an instruction file enters context | no | | measure instruction token share; detect conflicting instruction files |
| `PermissionRequest` / `PermissionDenied` | permission decision needed / auto mode denied | `decision` field; `retry` | `additionalContext` | policy layer for risk-tiered permissions |
| `PreModelSwitch` / `PostModelSwitch` | model change requested / applied | yes (pre) | `additionalContext` | routing policy enforcement |
| `WorktreeCreate` / `WorktreeRemove` | worktree lifecycle | yes (create) | | checkpoint strategy |
| `SessionEnd`, `StopFailure`, `Notification`, `MessageDisplay`, `FileChanged`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `Elicitation`, `ElicitationResult`, `TeammateIdle`, `Setup` | various | some | | observability only |

Implication for the architecture: the three capabilities the plan's adapter contract requires (inject at turn boundaries, intercept tool calls, block completion) all exist natively. `PostToolBatch` and `TaskCompleted` add two control points v0.1 of the plan did not know about.

## Headless mode (for the evaluation harness)

- `claude -p "<prompt>"` runs non-interactively; exit code 0 on success.
- `--bare` skips auto-discovery of hooks, skills, commands, subagents, plugins, MCP servers, auto memory and CLAUDE.md; recommended for reproducible runs; uses `ANTHROPIC_API_KEY`, never OAuth. Context is then supplied explicitly: `--append-system-prompt`, `--append-system-prompt-file`, `--settings`, `--mcp-config`, `--agents <json>`, `--plugin-dir`, `--plugin-url`. This is the correct way to run each baseline arm with exactly one framework loaded.
- Without `--bare`, a `-p` run executes project hooks and connects project `.mcp.json` servers with no trust prompt. Evaluation task repositories are untrusted content, so harness runs must use `--bare`.
- `--output-format json` returns `result`, `session_id`, usage, `total_cost_usd` and a per-model cost breakdown (client-side estimates). `--output-format stream-json --verbose` gives per-event NDJSON; the `system/init` event lists loaded `plugins`, `plugin_errors`, `mcp_servers`, `mcp_server_errors` (use to fail a run whose framework did not load). `--forward-subagent-text` (v2.1.211+) includes subagent text; `parent_tool_use_id` reconstructs the subagent tree.
- `--json-schema` with `--output-format json` yields `structured_output` (useful for forcing a final evidence report schema from baselines).
- Permissions: `--permission-mode` (`auto`, `dontAsk`, `acceptEdits`, and others), `--allowedTools` with permission-rule syntax, `--permission-prompts none` (v2.1.259+) to deny anything that would prompt and tell Claude not to retry; denials appear in `permission_denials` of the result. `AskUserQuestion` is removed under `--permission-prompts none`, which matters for measuring "necessary clarifying questions": use a permission mode that keeps the tool, or count questions from the stream.
- `--continue` / `--resume <session_id>` for multi-turn and multi-session evaluations.
- `--max-turns` and `--max-budget-usd` (print mode only) cap turns and dollars per run; `--fallback-model` names fallbacks; `--effort` sets `low` to `max`; `--no-session-persistence` keeps runs stateless; `--strict-mcp-config` ignores every MCP server except the ones passed; `--disallowedTools` removes tools from context; `--append-subagent-system-prompt` (v2.1.261+) reaches every subagent. Model pinned with `--model <id>`.
- Background bash tasks are killed about five seconds after the result; background subagents keep the process alive up to `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` (default 10 minutes).
- Skills and commands can be invoked inside the `-p` prompt as `/name`, which is how Spec Kit and gstack command sequences can be driven headlessly.

## Telemetry (for trace capture)

- Enable with `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Metrics: `claude_code.token.usage` (attributes `type` input/output/cacheRead/cacheCreation, `model`, `query_source` main/subagent/auxiliary), `claude_code.cost.usage`, `claude_code.lines_of_code.count`, `claude_code.commit.count`, `claude_code.code_edit_tool.decision`, `claude_code.active_time.total`.
- Events: `claude_code.user_prompt`, `claude_code.api_request` (tokens, cache, `cost_usd`, `duration_ms`, `request_id`), `claude_code.api_error`, `claude_code.tool_result` (`tool_name`, `success`, `duration_ms`, input and result sizes), `claude_code.tool_decision` (`source`: config, hook, user_*), `claude_code.assistant_response`. `prompt.id` correlates a prompt with its events.
- Content flags: `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT`, `OTEL_LOG_RAW_API_BODIES` (inline truncated at 60KB, or `file:/dir` untruncated). The last one gives the full per-call input, which is what the context-share metric needs.

## Startup context and compaction (documentation's own worked example)

Illustrative sizes from the docs' context-window simulation: system prompt about 4,200 tokens, auto memory index about 680, environment block about 280, MCP tool names about 120 (schemas deferred by default; `ENABLE_TOOL_SEARCH=auto` loads them upfront when they fit in 10% of the window), skill descriptions about 450, user CLAUDE.md about 320, project CLAUDE.md about 1,800. A subagent starts with its own copy of the system prompt (about 900), project CLAUDE.md, and the MCP and skill listings.

Compaction replaces the conversation with a structured summary. Reloaded automatically afterwards: system prompt, CLAUDE.md files, auto memory index, MCP tools, up to five most recently modified files with the rules that match them, and the bodies of invoked skills (5,000 tokens each, 25,000 combined). Not reloaded: the skill listing (skills never invoked become invisible after compaction), conversation-only instructions, nested CLAUDE.md files until re-read. Hook output on exit 0 goes to the debug log, not the transcript; only `additionalContext` JSON and exit-2 stderr reach the model.

## Facts that change the plan

1. Skill listings are budgeted at 1% of the context window and truncated by usage frequency. A framework with many skills silently loses discoverability. This is measurable in the probe runs via `/context` and `/skill-doctor` (v2.1.252+).
2. Invoked skill bodies persist in the conversation and survive compaction up to 5,000 tokens each, 25,000 tokens combined. Superpowers-style meta-skills therefore have a lasting per-session cost.
3. The docs themselves state CLAUDE.md is "context, not enforced configuration" and recommend `PreToolUse` hooks for anything that must happen. This is direct support for the plan's gates-over-text principle from the host vendor.
4. Auto memory exists natively with a 200-line index and on-demand topic files, with no provenance, confidence, or decay. The plan's memory design must either wrap it or replace it; replacing it means disabling it with `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` in evaluation arms so that memory effects are attributable.
5. `--bare` is the only correct baseline mode for the harness; anything else loads the machine's own configuration into the measurement.
6. Subagents get fresh context and can be assigned a model, a permission mode, a worktree, and a turn cap. Ephemeral critics map directly onto this without any custom infrastructure.
7. `TaskCompleted` can be blocked. The evidence engine can gate the host's own task list, not only the final Stop.
8. `--max-budget-usd` and `--max-turns` give the harness hard caps without any custom code, and `--bare` plus `--strict-mcp-config` plus `--plugin-dir` isolates each baseline arm to exactly one framework.
9. After compaction the skill listing is gone. Any framework that relies on model-invoked skills degrades silently on long tasks; this is a measurable failure mode (Appendix E code C4) and an argument for the ledger re-injection hypothesis H17.
10. Hook stdout on exit 0 never reaches the model. Runtime injections must use the `additionalContext` JSON form or exit 2, or they are silently dropped.
