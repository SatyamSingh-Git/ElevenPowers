# Support landscape: hosts, languages and delivery integrations for ElevenPowers (researched 2026-11-22)

Repository sources are local paths in `e:\ElevenPowers` at commit `553a25c` (read on 2026-11-22, not modified). External claims carry the publication or check date of the source. "Primary" means vendor docs or the original survey; "secondary" means a comparison or summary site and should be treated as weaker.

## Q1. Which coding-agent hosts does ElevenPowers support today, and how far is each verified?

### Takeaway
There are five host adapters (Claude Code, OpenAI Codex CLI, Gemini CLI, Cursor Agent desktop, GitHub Copilot CLI), all built on one shared runtime. Only Claude Code has passed installed, live-session acceptance, and only in some cells. The other four have been checked against their documented contracts, through launcher subprocesses and reversible setup, and have never been seen delivering a live callback. The project itself says "full native acceptance remains open on all hosts."

### Cited Findings
- Adapter modules exist only for Codex, Copilot, Cursor and Gemini (`core/hosts/codex.py`, `copilot.py`, `cursor.py`, `gemini.py`), plus shared lifecycle, setup, packaging, readiness, doctor and acceptance modules. Claude Code is the original native integration: `plugin/.claude-plugin/plugin.json` and `plugin/hooks/hooks.json` wire SessionStart, UserPromptSubmit, PreToolUse (matcher `Bash|PowerShell|Edit|Write|NotebookEdit`), PostToolUse and completion to `plugin/bin/ep_hook.py`. — [core/hosts/](core/hosts/), [plugin/hooks/hooks.json](plugin/hooks/hooks.json)
- "Claude Code retains its existing installation. Codex, Gemini CLI, Cursor Agent and GitHub Copilot CLI have native adapters, reversible project setup, configuration diagnostics and self-contained bundles. The four new integrations have documented-contract and launcher checks; live installed sessions remain an acceptance step." — [the-guide/platforms.md](the-guide/platforms.md)
- Each host has a setup target with a config file and a bundle format: Codex `.codex/hooks.json` / `.codex-plugin/plugin.json`; Gemini `.gemini/settings.json` / `gemini-extension.json`; Cursor v1 `.cursor/hooks.json` / `.cursor-plugin/plugin.json`; Copilot `.github/hooks/elevenpowers.json` / legacy root `plugin.json`. All of them are driven by `ep_setup.py HOST --project PATH`, `ep_ready.py` and `ep_doctor.py --platform`. — [the-guide/platforms.md](the-guide/platforms.md)
- Scope limits the guide states for each adapter:
  - Cursor: targets "Cursor Agent's documented desktop interface". Cursor CLI and cloud agents are not certified.
  - Copilot: targets local Copilot CLI and "does not certify VS Code, the cloud agent, or every installed CLI version".
  - Neither Cursor nor Copilot has an ordinary Stop report field, so the user has to run `ep_status.py`.
  - Copilot's `resultType: success` is transport status, not the process exit code, so command observations stay incomplete.
  — [the-guide/platforms.md](the-guide/platforms.md)
- Live verification to date:
  - claude/python acceptance passed in installed Claude Code 2.1.292 on 2026-10-11, "1/10" cells of the five-host by two-language matrix.
  - Fresh Claude Code 2.1.292 Python and JavaScript installed exercises each passed 12/12 checks. The guide calls this "2/10 host/language cells; the other four hosts still need installed exercises."
  - Installed Codex 0.159.2 showed the hooks as trusted, but "no callback was recorded".
  - On 2026-10-01 the Gemini, Cursor and Copilot executables were not available locally.
  — [the-guide/platforms.md](the-guide/platforms.md)
- The status page's "Remaining readiness limits" say: "Versioned live sessions on Codex, Gemini CLI, Cursor Agent and Copilot CLI remain open." Claude has observed startup, edit, exact fail/pass and completion, but "intentional incomplete execution remains unqualified, so full native acceptance remains open on all hosts". A full native-host receipt on a private acceptance project and latency measurements also remain open. — [docs/status.md](docs/status.md) (line 1526 onward)
- Every bundle requires `python` 3.11+ on the host PATH. — [the-guide/platforms.md](the-guide/platforms.md)

### Inferences
- In practice there is one supported host (Claude Code, partially accepted). The other four are "built, contract-tested, unproven live." Getting a live acceptance cell on Codex, the second host that is actually installed on this machine, costs less than adding a sixth adapter.
- The Python 3.11+ runtime dependency is a real adoption barrier for JS/TS-only users of Cursor and Copilot, who may not have a suitable Python on PATH.

### Gaps
- I did not count which adapter features (for example the advice-context fields) degrade on each host beyond the limits listed above. `core/hosts/contract.py` would hold that detail.

## Q2. Which languages, test runners, mutation engines and analysis features are supported, and which are Python-only?

### Takeaway
Test-result reading is broadly multi-language. Deeper evidence is split:
- Python and JS/TS: mutation strength and import-level impact analysis.
- Python only: function-level "is this function checked by a test" (TestMiner, `ep_review --functions`) and call-level impact links.
- Java, Go, Rust, C#, Ruby, PHP: results are read (counted for some, exit code only for Maven/Gradle), with no mutation, per-test coverage or impact support.

### Cited Findings
- Runners whose counts are parsed, in dispatch order in `_parse_known`: pytest, unittest, vitest, jest, tsc (type errors), `go test`, `cargo test|nextest`, rspec, `mix test`, phpunit, `dotnet test`. TAP is read from named harnesses (prove, bats, tap, tape) and from test-claiming commands whose output is TAP (for example `node --test`, `npm test`, `turbo test`). — [core/parsers.py](core/parsers.py) lines 497–575
- Wrapper commands where the runner is hidden and the exit code is the evidence: npm/pnpm/yarn/bun test, make test/check, tox/nox, hatch, poetry, just, `bazel test`, rake, `gradle(w) …test`, `mvn …test`, composer, `ctest`, `swift test`, `flutter test`. Counts are recovered only when the output carries a jest, pytest, rspec or mix summary. Maven's `Tests run:` output is recognised as test output but not counted. — [core/parsers.py](core/parsers.py) lines 89–117, 719–740
- Typecheck is recognised for mypy, pyright and `typecheck` scripts; lint for ruff, eslint, flake8 and clippy. — [core/parsers.py](core/parsers.py)
- Test-command auto-discovery covers package.json scripts (npm, pnpm, yarn, bun), Cargo.toml (`cargo test`), go.mod (`go test ./...`) and pytest config. Otherwise the command declared in tox, make or CI is used. There is no auto-discovery for Maven, Gradle or .NET. — [core/config.py](core/config.py) `discover_commands`
- Mutation ("strength") engines:
  - Two engines: Cosmic Ray (`cosmic-ray==8.7.0`, optional) for `.py`, and Stryker through `stryker_worker.mjs` for `.js .jsx .ts .tsx .mjs .cjs .mts .cts`.
  - `SUFFIXES` restricts strength to those extensions.
  - The runner splits paths into `.py` versus everything else.
  — [core/strength/engines.py](core/strength/engines.py), [core/strength/scope.py](core/strength/scope.py), [core/strength/runner.py](core/strength/runner.py), [requirements-strength.txt](requirements-strength.txt)
- TestMiner (`ep_testminer`, and `ep_review --functions`):
  - It works on "the Python functions you name", via coverage.py `dynamic_context = test_function`.
  - "The test command must be a direct `pytest` or `python -m pytest|unittest`".
  - Function verdicts use Python AST return annotations.
  — [core/testminer/coverage_run.py](core/testminer/coverage_run.py), [core/testminer/functions.py](core/testminer/functions.py), [the-guide/commands.md](the-guide/commands.md) §ep_testminer
- `ep_review` (PINNED / NOT PINNED, decided by reverting the change and rerunning the project's own command) is language-agnostic in mechanism, but "Only Python runs are checked for importing your checkout." — [the-guide/commands.md](the-guide/commands.md) §ep_review
- ImpactGraph (`ep_impact`) coverage by language:
  - Python: imports and conservative top-level call links.
  - JS/TS: relative imports, barrels, CommonJS and workspace packages via tree-sitter grammars, with an optional TypeScript 5.7.3 compiler mode.
  - Any language: declared relationships.
  - "Other language adapters are explicit gaps." Framework route/ORM extraction is future work.
  — [the-guide/impactgraph.md](the-guide/impactgraph.md)
- `ep_impact_capture` accepts `--kind python` (coverage.py) or `--kind v8` (native Node coverage). — [the-guide/commands.md](the-guide/commands.md) §ep_impact_capture
- The host acceptance matrix is defined only for `--language python|javascript`. — [the-guide/commands.md](the-guide/commands.md) §ep_doctor

### Inferences
- Coverage per language, by tier:
  - Python: all features (parse, review, strength, TestMiner, impact calls, coverage capture).
  - JS/TS: parse, review, strength, impact imports and V8 capture. No function-level TestMiner equivalent.
  - Go, Rust, .NET, Ruby, PHP, Elixir: counted parse plus review only.
  - Java/Kotlin (Maven/Gradle): exit-code parse plus review only.
- Given Q7, the most valuable single gap is TestMiner and function verdicts for TS/JS. The language with the weakest support relative to its usage is Java.

### Gaps
- I did not measure how reliably the non-Python/JS counted parsers work on real outputs. The repository's "run the producer" rule implies each was captured from a real run, but I did not audit that.

## Q3. Which delivery surfaces exist today?

### Takeaway
Delivery works through local CLIs, host hooks, a portable Markdown/JSON report, PatchProof bundles, and a read-only GitHub Action that writes a job summary and uploads an artifact. There is no PR comment, Check Run, status check, SARIF output, GitLab integration, MCP server or IDE extension.

### Cited Findings
- CLI entry points in `plugin/bin/`: `ep_check`, `ep_contract` (OpenAPI compatibility), `ep_doctor`, `ep_github`, `ep_hook`, `ep_host`, `ep_impact`, `ep_impact_capture`, `ep_inputs`, `ep_milestones`, `ep_patchproof`, `ep_ready`, `ep_repeat`, `ep_report`, `ep_review`, `ep_setup`, `ep_status`, `ep_strength`, `ep_testminer`, `ep_validate`. — [plugin/bin/](plugin/bin/)
- `ep_report.py --project PATH` exports Markdown by default, or JSON with `--format json`. It scrubs credentials, and it excludes prompts, transcripts and outputs. — [docs/status.md](docs/status.md) "Portable report acceptance"
- GitHub presentation (`ep_github.py`, and the reusable Action `github/patchproof` pinned by SHA):
  - It writes `evidence.json` and `summary.md` to the job summary and uploads them as a workflow artifact.
  - "It uses no write token, PR comment or Check Run publisher."
  - It is informational and should be kept separate from branch protection.
  - GitHub Enterprise Server is unsupported because of the v4 uploader.
  - A live fork/PR publication session was not run.
  — [the-guide/patchproof-github.md](the-guide/patchproof-github.md)
- A search of `core/`, `plugin/`, `the-guide/`, `docs/status.md` and `PLAN.md` for `mcp`, `modelcontextprotocol`, `sarif` and `gitlab` found no implementation (run 2026-11-22). — repository grep

### Inferences
- Moving from "artifact plus job summary" to "Check Run with annotations plus optional SARIF" would put evidence where reviewers already look. It needs a write-scoped token, which the current design deliberately avoids. That is a design decision to surface, not just work to schedule.

### Gaps
- I did not check whether `PLAN.md` explicitly withdraws or defers MCP or PR-comment delivery.

## Q4. What does the 2026 host landscape look like, and which hosts expose pre-tool, post-tool and stop hooks?

### Takeaway
By late 2026, hook APIs are close to universal among serious agents, and they come in two families:
- Shell-command hooks configured in JSON: Claude Code, Codex, Gemini CLI, Cursor, Copilot (CLI, VS Code and the cloud agent share one harness), Windsurf/Devin Desktop, Kiro, Cline.
- In-process JS/TS plugins: OpenCode, Amp, Cline's SDK, and Claude Code "Mods".

Aider has no hook API, and Zed's own agent had none as of March 2026. Junie is undocumented. Roo Code is reportedly shut down. ACP lets Zed and JetBrains host Claude Code, Codex, Gemini CLI and Copilot CLI as external agents.

### Cited Findings
- **Claude Code** (primary docs plus secondary dates):
  - Hooks shipped 2025-06-30 (v1.0.38). In-process "Mods" shipped 2026-10-01 (v2.1.287).
  - Pre-tool blocking is supported, and post-tool fires for any tool. — [digitalapplied, 2026-10-03](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
  - Official docs listed 33 hook events on 2026-10-08. — [wal.sh annotation, 2026-10-15](https://wal.sh/research/2026-q2-cli-coding-agents/)
  - When PreToolUse hooks disagree, deny wins. — [Claude Code docs](https://code.claude.com/docs/en/agent-sdk/hooks)
- **OpenAI Codex CLI**:
  - Hooks went GA on 2026-05-14. — [digitalapplied, 2026-10-03](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
  - Events: PreToolUse, PermissionRequest, PostToolUse, UserPromptSubmit, Stop, SessionStart, subagent and compaction. It can also run as an MCP server. — [RockB matrix, 2026-04-13](https://baeseokjae.github.io/posts/ai-coding-agent-capability-matrix-2026/), [wal.sh, 2026-04-18](https://wal.sh/research/2026-q2-cli-coding-agents/)
  - The repository's adapter cites the [official Codex hooks docs](https://learn.chatgpt.com/docs/hooks).
- **Gemini CLI**:
  - Hooks were announced 2026-01-28, with pre-tool blocking and post-tool support. — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
  - BeforeAgent/AfterAgent and tool events; the extension format is `gemini-extension.json`. — [Gemini hooks reference](https://geminicli.com/docs/hooks/reference/) (as cited in [the-guide/platforms.md](the-guide/platforms.md))
- **Cursor**:
  - Hooks entered beta in v1.7 on 2025-09-29. Pre-tool blocking is supported; post-tool fires for MCP tools only, per the 2026-10-03 comparison. — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
  - Cursor uses event-specific hooks (beforeShellExecution, beforeMCPExecution, beforeReadFile). One governance vendor wires 13 Cursor events, versus 6 for Claude. — [Endor Labs](https://www.endorlabs.com/learn/introducing-agent-governance-using-hooks-to-bring-visibility-to-ai-coding-agents)
  - Hook failure fails open unless `failClosed` is set. — [avanderlee](https://www.avanderlee.com/ai-development/agent-hooks-claude-code-cursor-codex/)
- **GitHub Copilot** (primary):
  - VS Code agent hooks are in preview. Events: `sessionStart`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `preCompact`, `subagentStart`, `subagentStop`, `agentStop`, `sessionEnd`.
  - "VS Code, the GitHub Copilot app, and Copilot CLI share the Copilot harness and its hook format."
  - Config lives in `.github/hooks/*.json` and `~/.copilot/hooks/`. The harness also reads `.claude/settings.json`, with a warning that payloads and tool names may differ.
  - Page dated 2026-11-18. — [VS Code docs](https://code.visualstudio.com/docs/copilot/customization/hooks)
  - The cloud (coding) agent also supports hooks, but "only the bash field is honored", and the docs warn against assuming identical events across surfaces. Command preToolUse errors deny the call; timeouts fall through. — [GitHub docs: about hooks (cloud agent)](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-hooks), [hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
  - VS Code hooks shipped in 1.110 on 2026-03-06. — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
- **Windsurf Cascade** (docs now hosted at Devin Desktop):
  - Cascade Hooks shipped 2025-11-13 (v1.12.31). — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
  - Events: `pre_/post_read_code`, `pre_/post_write_code`, `pre_/post_run_command`, `pre_/post_mcp_tool_use`. Only pre-hooks can block (exit 2). `post_write_code` is documented for running linters and tests. — [Windsurf/Devin hooks docs](https://docs.devin.ai/desktop/cascade/hooks); full event list from a third-party package, [pkg.go.dev assistantkit](https://pkg.go.dev/github.com/plexusone/assistantkit/hooks/windsurf)
  - I found no Windsurf stop/completion hook.
- **Cline**:
  - Hooks arrived in v3.36. Events include PreToolUse, PostToolUse, TaskComplete and TaskCancel. PostToolUse can cancel the task but not undo the tool. Scripts live in `.clinerules/hooks/` or `~/Documents/Cline/Hooks/`.
  - The v3.36 post said macOS/Linux only; current docs describe Windows `.ps1` hooks. — [Cline hooks docs](https://docs.cline.bot/features/hooks), [Cline v3.36 blog](https://cline.bot/blog/cline-v3-36-hooks)
- **Kiro**: five triggers (AgentSpawn, Stop, UserPromptSubmit, PreToolUse, PostToolUse); PreToolUse is vetoed with exit 2; no file-event hooks. — [wal.sh, 2026-04-18, corrected 2026-10-15](https://wal.sh/research/2026-q2-cli-coding-agents/)
- **OpenCode**:
  - In-process JS/TS plugins with `tool.execute.before` (can rewrite args or throw to block) and `tool.execute.after`. `session.idle` is a generic event usable as a completion signal. — [OpenCode plugins docs](https://opencode.ai/docs/plugins) (seen via search excerpts and mirrors; not opened directly)
  - wal.sh's April table said "No hooks", which predates or ignores the plugin API. Treat that as outdated.
- **Amp**: the Plugin API (in-process TS/JS) shipped 2026-05-06. It can intercept `tool.call` and return a result without running the tool. — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception) (secondary; no official Amp doc fetched)
- **Others with hooks**: Factory Droid (CLI 0.24.0, 2025-11-12) and Augment (post-tool output is read-only) both have pre-tool hooks. — [digitalapplied](https://www.digitalapplied.com/blog/ai-coding-agent-hooks-compared-tool-interception)
- **Aider** has no hook or plugin API. It offers `--test-cmd`, `--auto-test` (runs tests after each AI edit) and `--lint-cmd`. — [Aider docs: lint and test](https://aider.chat/docs/usage/lint-test.html)
- **Zed**:
  - A feature request dated 2026-03-29 says Zed's first-party agent has "no hooks or events to observe tool use". A linked commit adds them, but I could not confirm it was merged. — [zed-industries/zed#52688](https://github.com/zed-industries/zed/issues/52688)
  - Zed and JetBrains host external agents via the Agent Client Protocol (ACP). The ACP Registry (January 2026) lists Claude Code, Codex CLI, Copilot CLI, OpenCode, Gemini CLI and others. — [Zed ACP](https://zed.dev/acp), [ACP registry blog](https://zed.dev/blog/acp-registry), [JetBrains on ACP](https://zed.dev/blog/jetbrains-on-acp)
- **JetBrains Junie**: no hook documentation found. Junie runs in the terminal, in JetBrains Air, and from GitHub/GitLab issues and merge requests (secondary). — [search summary of agenticindex/paralect pages](https://agenticindex.io/rankings/coding-agents)
- **Roo Code**: reportedly shut down on 2026-05-15, with the repository archived and roocode.com redirecting to roomote.dev. Sources conflict. — [Morph comparison](https://www.morphllm.com/ai-coding-agent) (secondary)

### Inferences
- The Copilot harness is now shared across CLI, VS Code and the Copilot app. If live verification bears that out, ElevenPowers' existing Copilot CLI adapter could, with modest work, also cover VS Code agent mode, the largest-install surface. Today the guide explicitly does not certify it.
- ACP means the existing Claude, Codex, Gemini and Copilot adapters already reach Zed and JetBrains users who run those agents through ACP, because hooks run in the agent process, not the editor. This is a cheap reach expansion that needs one validation run per path.
- Candidate new hosts, ordered by ease and value:
  - Windsurf/Devin and Cline: shell hooks, close to the existing adapters. Windsurf lacks a completion hook.
  - Kiro: has a Stop hook.
  - OpenCode and Amp: need a small JS/TS plugin shim that forwards events to the Python runtime.
  - Aider and Junie: no hook surface; the only route is wrapping the test command or CI-side delivery.

### Gaps
- No official Amp, Kiro or Junie documentation was fetched; their capabilities rest on secondary comparisons.
- Exact Stop/completion semantics, including whether a hook can block completion, are unverified for Windsurf, Amp and OpenCode.
- Cursor CLI and Cursor cloud agent hook parity were not researched.

## Q5. What adoption and market-share signals exist for 2025–2026?

### Takeaway
Claude Code and GitHub Copilot are the two most-used coding agents in the 2025 and 2026 Stack Overflow data. Gemini and ChatGPT/Codex follow, and Cursor is a large IDE base whose growth was reported slowing. Agent use roughly doubled from 2025 to 2026. Trust is conditional on easy verification, which is ElevenPowers' pitch.

### Cited Findings
- **Stack Overflow 2025** (survey April–June 2025; primary):
  - 14.1% of respondents use AI agents at work daily and 9% weekly; 37.9% "don't plan to" (n=31,877).
  - Among the 8,323 agent users: ChatGPT 81.7%, GitHub Copilot 67.9%, Google Gemini 47.4%, Claude Code 40.8%, Roo Code 3.4%.
  - Cursor, Codex, Windsurf, Cline and Aider were not listed on that question.
  - 46% distrust AI accuracy versus 33% who trust it.
  — [SO 2025 AI section](https://survey.stackoverflow.co/2025/ai)
- **Stack Overflow 2026** (results post dated 2026-10-06; primary):
  - More than 30,000 respondents.
  - "73% of respondents who indicate using AI coding assistants/agents use them daily."
  - 66% of AI users work in coding agents.
  - Coding agent tools: Claude Code 66%, GitHub Copilot 59%. The base population is not stated in the post. Cursor, Codex and Gemini CLI figures were not given there.
  - 93% say source attribution is needed to trust AI output.
  — [SO blog, 2026-10-06](https://stackoverflow.blog/2026/10/06/the-results-of-the-2026-developer-survey-are-here/)
- **Stack Overflow April 2026 pulse survey**: 59% use agents at work, versus 31% in 2025, and "nearly half trust its output only when they can easily verify the output". — [SO blog, 2026-05-27](https://stackoverflow.blog/2026/05/27/agents-on-a-leash-agentic-ai-remains-mostly-monitored-at-work/), as summarised in search results
- **JetBrains State of Developer Ecosystem 2025** (fieldwork April–June 2025, 24,534 developers):
  - 85% regularly use AI for coding and 62% rely on at least one AI coding assistant, agent or editor.
  - 11% already used coding agents and 49% planned to try them.
  — [JetBrains blog, 2025-10](https://blog.jetbrains.com/research/2025/10/state-of-developer-ecosystem-2025/)
- **JetBrains AI Pulse** (secondary summary, not the main report): Claude Code's at-work share grew about 6x from roughly 3% in April–June 2025, reaching 24% in the US/Canada, and "Cursor's growth has slowed down". — [via search summary of JetBrains materials](https://www.jetbrains.com/lp/annualreport-2026/) (not verified on a primary page)
- **Secondary work-tool shares for 2025**: Cursor 17.9%, Claude Code 9.7%, Windsurf 4.9%. The base is unclear. — [The New Stack](https://thenewstack.io/23-of-devs-regularly-use-ai-agents-per-stack-overflow-survey/)
- **Junie**: 343,000 users from 2025-03-26 to year end. A secondary figure. — search summary (unverified)

### Inferences
- An adoption-weighted host priority would be Claude Code (done), then the Copilot harness (CLI, VS Code, cloud agent), then Cursor, Codex and Gemini CLI. That is the existing five, so the priority is live-verifying them rather than adding breadth. Windsurf, Cline, Kiro, OpenCode and Amp are long-tail.

### Gaps
- No 2026 primary figures were found for Cursor, Codex CLI, Gemini CLI, Windsurf or Cline usage shares.
- The base for the 2026 "Claude Code 66% / Copilot 59%" figures is unclear.

## Q6. Which delivery integrations do comparable verification and code-quality tools use?

### Takeaway
The standard for CI-side evidence on GitHub is SARIF 2.1.0 uploaded to code scanning, which produces in-file annotations, plus Check Runs and status checks for gating. MCP and ACP are the agent-side standards. ElevenPowers uses none of them yet.

### Cited Findings
- **GitHub code scanning and SARIF**:
  - It accepts SARIF 2.1.0 from third-party tools via Actions or the API. The limit is 10 MB gzip-compressed per upload.
  - SARIF location data drives in-file annotations. A second upload for the same commit replaces the first unless the category or `runAutomationDetails.id` differs.
  - Private repositories need GitHub Code Security enabled, and the uploader needs write access.
  — [GitHub docs: upload SARIF](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file)
- MCP is a near-universal agent-side tool protocol in 2026: supported by Claude Code, Codex (which can also run as an MCP server), Gemini CLI, Cursor, Copilot, Windsurf, Cline and OpenCode. — [RockB capability matrix, 2026-04-13](https://baeseokjae.github.io/posts/ai-coding-agent-capability-matrix-2026/), [wal.sh](https://wal.sh/research/2026-q2-cli-coding-agents/)
- Agent-governance vendors deliver through host hooks across many agents, for example Endor Labs' hook-based governance for Claude Code and Cursor. — [Endor Labs](https://www.endorlabs.com/learn/introducing-agent-governance-using-hooks-to-bring-visibility-to-ai-coding-agents)
- ElevenPowers' current GitHub surface is a job summary plus an artifact only, with no Check Run or PR comment, and GHES is unsupported. — [the-guide/patchproof-github.md](the-guide/patchproof-github.md)

### Inferences
- An MCP server exposing `ep_review`, `ep_testminer`, `ep_strength` and `ep_status` as tools would reach every MCP-capable host, including Windsurf, Junie, Zed's native agent and Aider-adjacent setups. It works without per-host hook adapters, but as pull rather than observe: the agent must choose to call it. It would complement the hook adapters, not replace them.
- SARIF fits "functions no test checks" and "mutation survivors" as file and line findings. Check Runs fit PINNED / NOT PINNED verdicts. GitLab's equivalent would be merge-request widgets or code-quality reports (not researched).

### Gaps
- I did not research the Checks API annotation limits, GitLab code-quality or MR integration formats, or what Stryker's dashboard and comparable mutation-testing SaaS publish to PRs. Those need a follow-up search.

## Q7. Which languages should be prioritised, and what mutation and per-test coverage tooling exists for each?

### Takeaway
TypeScript is now GitHub's most-used language and is explicitly tied to AI and agent use. Python and JavaScript follow, then Java, C# and C++. The six together account for about 80% of new repositories. Mature mutation engines exist for every candidate: Stryker (JS/TS and .NET), PIT (Java), cargo-mutants (Rust), Infection (PHP), mutmut and Cosmic Ray (Python). Go's engines are less established. That ranking points to TS/JS function-level evidence first, then Java (PIT), then C# (Stryker.NET), then Go and Rust.

### Cited Findings
- **Octoverse 2025** (published 2025-10-28; data September 2024–August 2025):
  - TypeScript became GitHub's most-used language by contributors in August 2025, overtaking Python and JavaScript, after adding more than 1M contributors (+66% year on year).
  - Nearly 80% of new repositories use six languages: Python, JavaScript, TypeScript, Java, C++ and C#.
  - GitHub attributes the shift partly to typed languages working well with agents and Copilot.
  — [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- **Stack Overflow 2026**: JavaScript 62%; SQL, HTML/CSS and Python 58% each; Rust moved up to 12th. — [SO blog, 2026-10-06](https://stackoverflow.blog/2026/10/06/the-results-of-the-2026-developer-survey-are-here/)
- **Mutation engines by language** (secondary 2026 guides; maintenance status not verified):
  - PIT is the de facto JVM standard, with Maven and Gradle integration.
  - Stryker covers JS/TS, C# (Stryker.NET) and Scala.
  - mutmut is the simple pytest-native Python choice; Cosmic Ray scales to larger suites.
  - Infection is the PHP standard, integrating with PHPUnit.
  - cargo-mutants is a Cargo subcommand for Rust.
  - Go engines (gremlins, go-mutesting) did not surface.
  — [gitnux 2026 list](https://gitnux.org/best/mutation-testing-software/), [Augment guide](https://www.augmentcode.com/guides/mutation-testing-ai-generated-code), [mutating.tech digest, 2026-06](https://mutating.tech/blog/the-mutation-testing-digest-for-june-2026/)
- **Per-test coverage**:
  - coverage.py's `dynamic_context = test_function` is what ElevenPowers already uses for Python. — [core/testminer/coverage_run.py](core/testminer/coverage_run.py)
  - cargo-llvm-cov has no per-test breakdown; the documented route is running tests separately with `--no-report` and merging. — [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov)
  - One comparison lists OpenClover, not JaCoCo, as offering per-test coverage for Java, and lists Istanbul without per-test coverage. — [itechguides 2026](https://www.itechguides.com/best/test-coverage-tools/) (secondary)
  - ElevenPowers already ingests V8 coverage for Node. — [the-guide/commands.md](the-guide/commands.md)

### Inferences
- **TS/JS**: mutation and impact support exist, but there is no TestMiner equivalent. Building one from V8 or Istanbul coverage, either per test file or by running tests one at a time, would bring the most-used language up to Python's level.
- **Java**: `ep_review` works through exit codes, but Maven/Gradle counts are not parsed and there is no discovery. Adding Surefire/Gradle summary parsing and discovery is cheap. PIT is the obvious mutation borrow, under the project's "borrow first" rule.
- **C#**: `dotnet test` counts are already parsed, so Stryker.NET reuses Stryker concepts.
- **Go and Rust**: parse support exists. cargo-mutants is a mature borrow for Rust; for Go, the engine choice needs verification.

### Gaps
- Maintenance status and recent releases of PIT, Stryker.NET, cargo-mutants, Infection, gremlins and go-mutesting were not checked on their repositories.
- Per-test coverage support in JaCoCo (session or per-test listeners), Istanbul/V8 and Go (`-coverprofile` per test run) was not confirmed from primary docs.
- I found no data on which languages agent-written code specifically is in, as opposed to all GitHub activity.
