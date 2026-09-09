# Host card: Gemini CLI (google-gemini/gemini-cli)

Clone: `scratchpad/repos/gemini-cli` (paths relative to clone root). "Read" = seen in source or in-repo docs; "Inferred" = conclusion from the read material. In-repo docs are complete and versioned with the code, so most citations are `docs/**`. The host was not run.

## Identity

- Commit: `ed2ac40df67a319bf348bd7e3d10494696b31b38`, 2026-09-08T22:40:34Z (`git log -1`). Title: "fix(core): preserve explicit versioned Flash model IDs (#29252)". Package version `0.61.0-nightly.20260908` (`package.json`).
- License: Apache-2.0 (`LICENSE`; `packages/cli/package.json:5`, `packages/core/package.json:5`).
- Language: TypeScript on Node >= 20 (`package.json` `engines`). Workspaces: `packages/cli`, `packages/core`, `packages/sdk`, `packages/a2a-server`, `packages/vscode-ide-companion`, `packages/devtools`, `packages/test-utils`.

## Instruction files

- Default file name `GEMINI.md` (`packages/core/src/tools/memoryTool.ts:11`), overridable to one or many names via `context.fileName` (e.g. `["AGENTS.md","CONTEXT.md","GEMINI.md"]`) (`docs/cli/gemini-md.md`; `docs/reference/configuration.md` `context.fileName`).
- Hierarchy (Read, `docs/cli/gemini-md.md`): 1) global `~/.gemini/GEMINI.md`; 2) workspace files found in the workspace directories and their parents; 3) just-in-time files found when a tool touches a directory, scanning up to a trusted root. All are concatenated and sent with every prompt. Discovery code: `packages/core/src/utils/memoryDiscovery.ts`.
- Bounds: `context.discoveryMaxDirs` default 200; upward traversal stops at `context.memoryBoundaryMarkers` (default `[".git"]`); `context.includeDirectories` extends the workspace; `context.loadMemoryFromIncludeDirectories` default false (`docs/reference/configuration.md` `context` section). No byte cap on file size was found in docs or `memoryDiscovery.ts` (grep for `MAX_` empty), so size limits are an open question.
- Imports: `@./relative.md` within a context file (`docs/cli/gemini-md.md`; `docs/reference/memport.md`). `/memory show|reload` inspects the merged text.
- Extensions can contribute their own context file via `contextFileName` in `gemini-extension.json` (`docs/extensions/reference.md`).
- System prompt override: `GEMINI_SYSTEM_MD=1|<path>` fully replaces the built-in prompt; `GEMINI_WRITE_SYSTEM_MD` exports it; `${AgentSkills}`, `${SubAgents}`, `${AvailableTools}` substitutions (`docs/cli/system-prompt.md`).

## Hooks and lifecycle events

Present, and broader than most hosts.

- Events (Read, `docs/hooks/reference.md`; enum in `packages/core/src/hooks/types.ts:44-54`): `SessionStart`, `SessionEnd`, `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeToolSelection`, `BeforeTool`, `AfterTool`, `PreCompress`, `Notification`.
- Config location: `hooks` object in `settings.json`; precedence project `.gemini/settings.json` > user `~/.gemini/settings.json` > system `/etc/gemini-cli/settings.json` > extension `hooks/hooks.json` (`docs/hooks/index.md` "Configuration"). Schema: `hooks.<Event>: [{ matcher, sequential, hooks: [{ type: "command", command, name, timeout(ms, default 60000), description }] }]`. Only `type: "command"` exists. Master switch `hooksConfig.enabled` (default true), `hooksConfig.disabled[]` (`docs/reference/configuration.md` `hooksConfig`).
- Protocol: JSON on stdin (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `timestamp`, plus event fields), JSON on stdout. Exit 0 = parse stdout; exit 2 = block with stderr as reason; other = warning and continue (`docs/hooks/reference.md` "Global hook mechanics"). Runner: `packages/core/src/hooks/hookRunner.ts`; aggregation of multiple hooks: `hookAggregator.ts`.
- BLOCK a tool call: yes. `BeforeTool` with `decision: "deny"|"block"` + `reason` (sent to the model as a tool error; turn continues), `hookSpecificOutput.tool_input` merges/overrides arguments, `continue: false` kills the loop. `AfterTool` `decision: "deny"` replaces the tool result with `reason`; `tailToolCallRequest` chains another tool (`docs/hooks/reference.md` "Tool hooks"). Matchers are regex over tool names; MCP tools are `mcp_<server>_<tool>`.
- INJECT text: yes. `BeforeAgent` `hookSpecificOutput.additionalContext` is appended to the prompt for that turn; `SessionStart` `additionalContext` becomes the first history turn (interactive) or is prepended to the prompt (non-interactive); `AfterTool` `additionalContext` is appended to the tool result. `BeforeModel` can rewrite `llm_request` (model, messages, config) or return a synthetic `llm_response`; `BeforeToolSelection` restricts `toolConfig.allowedFunctionNames`/`mode` (`docs/hooks/reference.md`).
- BLOCK completion: yes. `AfterAgent` fires after the final response; `decision: "deny"` + `reason` rejects it and sends `reason` back as a new prompt (retry); input includes `stop_hook_active` to detect retry loops; `continue: false` stops instead; `clearContext` wipes LLM history (`docs/hooks/reference.md` "AfterAgent").
- Advisory only: `SessionStart` never blocks; `SessionEnd`, `PreCompress`, `Notification` ignore flow control.
- Trust: project hooks are fingerprinted (`name:command`) and re-confirmed when changed; store `trusted_hooks.json` (`packages/core/src/hooks/trustedHooks.ts:19-29`; `docs/hooks/index.md` "Security and risks"). Env passed: `GEMINI_PROJECT_DIR`, `GEMINI_SESSION_ID`, `GEMINI_CWD`, `CLAUDE_PROJECT_DIR` alias.

## MCP

- Config: `mcpServers.<name>` in `settings.json` (any layer) or in an extension manifest; transports stdio (`command`/`args`/`env`/`cwd`), SSE (`url`), streamable HTTP (`httpUrl`, `headers`); OAuth for remote servers (`docs/tools/mcp-server.md` "Configuration properties", "OAuth support"). CLI: `gemini mcp add|list|remove` with `--trust`.
- Restriction: per-server `includeTools[]` / `excludeTools[]` (exclude wins; extension and settings lists union for exclude, intersect for include), `trust: true` bypasses confirmations, global `mcp.allowed[]` / `mcp.excluded[]` server lists, `--allowed-mcp-server-names` flag (`docs/tools/mcp-server.md`; `docs/reference/configuration.md` `mcp`). Policy-engine rules can target `mcpName` + `toolName` (`docs/reference/policy-engine.md` TOML schema).
- Prompts: supported; server prompts become slash commands and run `prompts/get` (`docs/tools/mcp-server.md` "MCP prompts as slash commands").
- Resources: supported; `resources/list` at discovery, `@server:resource` references call `resources/read`, plus `list_mcp_resources` / `read_mcp_resource` tools (`docs/tools/mcp-resources.md`).
- Untrusted folders never connect MCP servers (`docs/cli/trusted-folders.md`).

## Extensions and commands

- Extensions: installed to `~/.gemini/extensions/<name>` with `gemini-extension.json` (`name`, `version`, `mcpServers`, `contextFileName`, `excludeTools`, `settings[]`, `themes`, `plan`), optional `commands/*.toml`, `hooks/hooks.json`, `skills/<name>/SKILL.md`, `agents/*.md`, `policies/*.toml` (`docs/extensions/reference.md`). Managed with `gemini extensions install|uninstall|enable|disable|update|link|new`; changes need a restart. Extension policies cannot `allow`; they run in tier 2.
- Custom commands: TOML files under `~/.gemini/commands/` (user) and `<project>/.gemini/commands/` (project wins); path becomes name (`git/commit.toml` -> `/git:commit`); fields `prompt`, `description`; `{{args}}`, `!{shell}` (confirmed before running), `@{file}` (`docs/cli/custom-commands.md`).
- Skills: `SKILL.md` per directory following agentskills.io; tiers built-in < extension < user (`~/.gemini/skills/` or `~/.agents/skills/`) < workspace (`.gemini/skills/` or `.agents/skills/`); only name/description are in the system prompt until the model calls `activate_skill` and the user consents (`docs/cli/skills.md`; `docs/tools/activate-skill.md`). `gemini skills install|list|uninstall`.
- SDK: `@google/gemini-cli-sdk` exposes `GeminiCliAgent` for programmatic embedding (`packages/sdk/README.md`). ACP mode `--acp` / `--experimental-acp` for editors (`docs/cli/acp-mode.md`; `docs/cli/cli-reference.md:59`).

## Subagents

- Present, enabled by default; disable with `experimental.enableAgents: false` (`docs/core/subagents.md` "Disabling subagents"). Built-ins: `codebase_investigator`, `cli_help`, `generalist`, browser agent. Each subagent is exposed to the main model as a tool of the same name; `@name` prefix forces it.
- Custom agents: Markdown with YAML frontmatter in `.gemini/agents/*.md` (project) or `~/.gemini/agents/*.md` (user); body is the system prompt; frontmatter `name`, `description`, `kind: local|remote`, `tools[]` (wildcards `*`, `mcp_*`, `mcp_<server>_*`), `mcpServers`, `model` (default `inherit`), `temperature`, `max_turns` (30), `timeout_mins` (10) (`docs/core/subagents.md` "Configuration schema"; loader `packages/core/src/agents/agentLoader.ts`, `AgentDefinition.modelConfig` in `agents/types.ts:221`).
- Per-subagent model: yes, via frontmatter `model` or `agents.overrides.<name>.modelConfig.model` / `runConfig.maxTurns` in settings, and `modelConfigs.overrides` with `overrideScope` (`docs/core/subagents.md` "Persistent configuration"). Note `--model` does not override subagent models (`docs/cli/model.md`).
- Subagents cannot call subagents (recursion protection). Remote agents over A2A (`docs/core/remote-agents.md`, `packages/a2a-server`).

## Headless mode

- Trigger: `gemini -p "<prompt>"` (or non-TTY stdin; `-p` text is appended to piped stdin) (`docs/cli/headless.md`; `docs/cli/cli-reference.md:52`). Runner: `packages/cli/src/nonInteractiveCli.ts`.
- Output: `--output-format text|json|stream-json`. `json` = one object `{ response, stats, error? }`; `stream-json` = JSONL events `init`, `message`, `tool_use`, `tool_result`, `error`, `result` (result carries aggregated stats and per-model token usage) (`docs/cli/headless.md`; `OutputFormat` branches in `nonInteractiveCli.ts:119-601`). So tool calls and token usage are reported.
- Flags: `-m/--model`, `--approval-mode default|auto_edit|yolo|plan`, `--yolo` (deprecated), `-s/--sandbox`, `--resume [latest|index|uuid]`, `--include-directories`, `--allowed-tools` (deprecated in favour of policies), `--allowed-mcp-server-names`, `-e/--extensions`, `--skip-trust`, `--admin-policy`, `--list-sessions`, `--delete-session` (`docs/reference/configuration.md` "Command-line arguments"; `docs/cli/cli-reference.md` options table).
- Turn budget: `model.maxSessionTurns` in settings (default -1); in non-interactive mode hitting it exits with an error (`docs/cli/session-management.md` "Session limits"). Exit codes: 0 ok, 1 error, 42 input error, 53 turn limit (`docs/cli/headless.md`). Subagent budgets: `max_turns`, `timeout_mins`.
- Untrusted folder in CI: `--skip-trust` or `GEMINI_CLI_TRUST_WORKSPACE=true`, else `FatalUntrustedWorkspaceError` (`docs/cli/trusted-folders.md`).

## Sandbox and approvals

- Approval modes (`packages/core/src/policy/types.ts:48-53`): `default` (write tools ask), `autoEdit` (edit tools auto-approved), `yolo` (all allowed; `security.disableYoloMode` can forbid), `plan` (read-only). Default from `general.defaultApprovalMode` (`docs/reference/configuration.md`).
- Policy engine (`docs/reference/policy-engine.md`): TOML `[[rule]]` with `toolName`, `mcpName`, `agentName`, `argsPattern`, `commandPrefix`, `commandRegex`, `decision = allow|deny|ask_user`, `priority`, `modes[]`, `interactive`; tiers Default(1) < Workspace/Extension(2, workspace currently disabled) < User (`~/.gemini/policies/*.toml`, 3) < Admin (`/etc/gemini-cli/policies`, `adminPolicyPaths`, 4). Defaults: read-only tools allowed, `write_file`/`run_shell_command` ask, shell redirection asks unless `allow_redirection`. Runtime "always allow" choices are persisted as rules scoped to the current mode and more permissive ones.
- Sandboxing (`docs/cli/sandbox.md`): `-s`, `GEMINI_SANDBOX=true|docker|podman|sandbox-exec|runsc|lxc`, or `tools.sandbox`; macOS Seatbelt profiles (`permissive-open` default), Docker/Podman image `ghcr.io/google/gemini-cli` with cwd mounted at the same path, Windows native (icacls low integrity), gVisor, LXC. Per-tool sandboxing via `security.toolSandboxing`; `~/.gemini/policies/sandbox.toml` (`packages/core/src/policy/sandboxPolicyManager.ts:104`).
- Trusted folders (`security.folderTrust.enabled`, off by default): untrusted workspaces ignore `.gemini/settings.json`, `.env`, MCP servers, custom commands, and force prompts (`docs/cli/trusted-folders.md`).
- Checkpointing (`general.checkpointing.enabled`) snapshots to a shadow git repo `~/.gemini/history/<project_hash>` before writes; `/restore` (`docs/cli/checkpointing.md`).

## Context management and memory

- Startup: built-in system prompt (or `GEMINI_SYSTEM_MD`), merged GEMINI.md hierarchy, optional directory tree (`context.includeDirectoryTree` default true), skill and subagent catalogs, tool declarations (`docs/cli/system-prompt.md`; `docs/reference/configuration.md` `context`).
- Compression: automatic when usage crosses `model.compressionThreshold` (default 0.5 of context), `contextManagement.historyWindow.maxTokens` 150000 / `retainedTokens` 40000, per-message truncation, tool-output distillation (summarize above 20000 tokens) and output masking of old tool results (`docs/reference/configuration.md` `model`, `contextManagement`; `packages/core/src/config/config.ts` reads `compressionThreshold`). Dedicated `chat-compression-*` model configs (`configuration.md` ~line 837). Hook `PreCompress` is advisory.
- Memory across sessions: the agent edits Markdown memory files directly (repo `GEMINI.md`, private project memory dir, global `~/.gemini/GEMINI.md`) (`docs/tools/memory.md`). Experimental `experimental.autoMemory` mines idle sessions into a review inbox (`/memory inbox`) (`docs/cli/auto-memory.md`).
- No repository index; `@file` completion uses ripgrep/fuzzy search (`tools.useRipgrep`; `context.fileFiltering.*`).

## Telemetry

- Session transcripts: `~/.gemini/tmp/<project_hash>/chats/<session>.jsonl` (`docs/cli/session-management.md`; `packages/core/src/services/chatRecordingService.ts:479-512`). Saved: prompts, responses, tool inputs/outputs, token usage (input/output/cached), thoughts. Retention `general.sessionRetention` (30 days default).
- OpenTelemetry (`docs/cli/telemetry.md`): `telemetry.enabled`, `target local|gcp`, `otlpEndpoint`, `otlpProtocol`, `outfile` (e.g. `.gemini/telemetry.log`), `logPrompts`, `traces`. Per-call events `gemini_cli.api_request`, `gemini_cli.api_response` (with `input_token_count`, `output_token_count`), `gemini_cli.tool_call`, `gen_ai.client.inference.operation.details` (`gen_ai.usage.input_tokens`/`output_tokens`), `gemini_cli.chat_compression`, `gemini_cli.agent.start|finish`. So per-call token usage is recorded when telemetry is on.
- Hook transcripts: every hook receives `transcript_path` (`docs/hooks/reference.md`).

## Model selection

- Precedence: `--model` > `GEMINI_MODEL` env > `model.name` setting > local Gemma router > default `auto` (`docs/cli/model-routing.md`). Aliases `auto`, `pro`, `flash`, `flash-lite` (`packages/core/src/config/models.ts:110-113`); `DEFAULT_GEMINI_MODEL = 'gemini-2.5-pro'`, `PREVIEW_GEMINI_MODEL = 'gemini-3-pro-preview'` (`models.ts:54, 61`). `/model` dialog in-session.
- Providers: Gemini only, through auth types `oauth-personal`, `gemini-api-key`, `vertex-ai`, `cloud-shell`, `compute-default-credentials`, `gateway` (`packages/core/src/core/contentGenerator.ts:63-70`). Local Gemma via LiteRT-LM is used only for routing decisions (`docs/core/local-model-routing.md`). Automatic fallback on quota/server errors (`docs/cli/model-routing.md`). Per-model generation params via `modelConfigs` (`docs/cli/generation-settings.md`).

## Adapter assessment

- Inject text at turn boundary: PRESENT. `BeforeAgent` hook `hookSpecificOutput.additionalContext` (per turn) and `SessionStart` `additionalContext`; `BeforeModel` can rewrite the whole outgoing request, which is stronger than Codex offers.
- Intercept tool calls: PRESENT. `BeforeTool` deny/rewrite (`tool_input` merge), `AfterTool` replace/append/tail-call, `BeforeToolSelection` allowlist; policy engine TOML for static rules.
- Block completion: PRESENT. `AfterAgent` `decision: "deny"` + `reason` forces a retry turn with the reason as the new prompt; `stop_hook_active` guards loops.
- Degraded adapter (hooks disabled via `hooksConfig.enabled=false` or project hooks untrusted in an untrusted folder): run `gemini -p --output-format stream-json`, prepend context to the prompt, enforce policy via user-tier `~/.gemini/policies/*.toml`, and loop on `result` events with `--resume latest`. Loses in-turn interception and retry-on-finish; `AfterTool` context injection is also lost.

## Open questions

- Byte/size limit for concatenated GEMINI.md content (none documented; `memoryDiscovery.ts` only caps directory count).
- Whether `AfterAgent` fires in non-interactive mode for every turn, and how many retries it allows before giving up (only `stop_hook_active` documented).
- Exact `stream-json` event payload schemas (documented by name only in `docs/cli/headless.md`; source in `packages/cli/src/nonInteractiveCli.ts`).
- Workspace-tier policies are marked disabled in `docs/reference/policy-engine.md`; confirm whether extension `policies/` still load in headless runs.
- `experimental.enableAgents` default and whether subagent tool calls pass through `BeforeTool` hooks of the parent session (docs say local subagent actions are "checked individually").
