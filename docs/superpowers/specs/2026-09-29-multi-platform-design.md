# Five-platform ElevenPowers design

2026-09-29. **Design approved; implementation authorized.** Claude Code is the
existing host. The user confirmed Codex, Gemini CLI, Cursor and GitHub Copilot
CLI as the four additions, revised to eight detailed pushes per addition. The previous
six-part durable-runner delivery ends at `086e90c` and is separate from these
thirty-two pushes.

## Intended outcome

Install ElevenPowers into a supported host once, enable it through that host's
normal trust/settings flow, and have essential behavior run automatically in
ordinary projects: startup health, repository selection, declared-command
discovery, command evidence, completion verification and recovery. No project
name, Snag path or language-specific assumption belongs in an adapter.

The engine's existing Python 3.11+ standard-library runtime, project boundaries,
coverage reporting, receipt freshness and off/guide/strict modes remain the
shared contract. A host's missing capability must be visible. Installation is
not itself proof that a live host delivered the required events.

## Approach and alternatives

**Recommended: native hooks around one shared engine.** Small adapters translate
events and responses; native packaging or project hook configuration makes
activation automatic. This keeps verification semantics consistent while
allowing each host to retain its own permission and completion behavior.

An MCP-only integration would expose callable verification tools but would
depend on the agent choosing to call them. It cannot meet the automatic lifecycle
requirement by itself. Four separate copies of the runtime would simplify the
first wiring work but multiply fixes and allow evidence semantics to diverge.

## Runtime boundary

Extract host-neutral dispatch and responses from `core/hook.py`, preserving the
existing Claude launcher and its tested wire contract. Keep translation in a
small host package rather than scattering platform branches through verification,
scanning, parsing and ledger code. Generated subscriptions and adapter handling
must use the same event definitions so an implemented handler cannot silently
remain unsubscribed.

A normalized event carries host identity, native event, canonical phase, project
root, session/turn/tool identity when available, prompt or final message when
available, and typed tool input/outcome. Canonical phases are startup, prompt,
before-tool, after-tool and completion. Unsupported native events are ignored
with an explicit diagnostic when their absence reduces coverage.

Command outcomes distinguish completed success, completed failure, interrupted,
still running and unknown. A successful tool transport is insufficient to prove
the command exited successfully. Adapters may establish success from an explicit
exit status or a documented and producer-validated completion contract; absent
either, the outcome stays incomplete. A timeout or permission denial must never
become a reproduced test failure. Duplicate delivery of the same completed tool
call must not duplicate receipts; intermediate polls must not finalize them.

Core responses express context, user-visible status, permission intent and
completion continuation separately. Each adapter serializes only fields that
its host supports and emits one valid JSON response. Diagnostic logs use stderr.
Recording an observation never rewrites the host's original tool result.

## Platform mapping

These mappings are based on current official documentation, not live-session
certification. Exact installed-version behavior is an acceptance check.

| Host | Native lifecycle | Main integration concern |
|---|---|---|
| Claude Code | Existing SessionStart, UserPromptSubmit, tool events and Stop | Preserve current behavior and entry points through the extraction |
| Codex | SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop | Nonzero shell exits also reach PostToolUse; a later execution poll may deliver the final result |
| Gemini CLI | SessionStart, BeforeAgent, BeforeTool, AfterTool, AfterAgent | Tool response envelopes differ; hook timeouts are milliseconds |
| Cursor Agent | sessionStart, beforeSubmitPrompt, tool events, stop | Multiple workspace roots, asynchronous startup and follow-up based completion |
| GitHub Copilot CLI | sessionStart, userPromptSubmitted, tool events, agentStop | Native camelCase envelopes and result text; success transport is not assumed to be exit zero |

Codex completion continuation uses its supported Stop decision. Gemini uses its
AfterAgent retry decision. Cursor uses stop follow-up messages only after normal
completion, never after an abort/error. Copilot uses agentStop decisions.
ElevenPowers' existing bounded continuation policy applies in addition to host
limits. Automatically generated continuation prompts retain the current task
and cannot reset its retry counter as if a new user request arrived.

Some hosts cannot enforce every permission intent. If an `ask` response is
unsupported, the adapter must not silently turn it into `allow`: prevent the
questioned operation using the supported decision, explain how the user can
authorize/retry it, and report the capability difference. Ordinary observational
failures remain visible and never produce a verified result.

No unsupported transcript scraping is required. If a host omits final assistant
text, completion uses existing task obligations and observed edits, and records
that claim-text coverage is unavailable. Cursor CLI, Copilot cloud/VS Code and
other surfaces are not implicitly covered by their similarly named products.

## Project, installation and automatic behavior

Resolve the project from explicit host working-directory information and the
existing repository-boundary policy. The plugin's own directory is never the
fallback target for host evidence. An ambiguous multi-root event must not scan or
write into an arbitrarily chosen first workspace. Report ambiguity and leave
evidence unverified until the root is known.

Ship native packaging where supported and a project-scoped configuration path
where required. A common setup command identifies the requested host and project,
checks the Python executable, generates platform-correct launch commands, and
merges only ElevenPowers-owned entries. Running setup twice produces no duplicate
hooks. Updating or removing an integration preserves unrelated hooks/settings;
invalid existing configuration produces an actionable error before any write.
Configuration updates are atomic. Paths with spaces and Windows quoting are
explicit acceptance cases.

Host trust and enablement remain normal user installation steps. Setup must not
disable host approvals or bypass workspace trust. Once enabled, essential
startup and verification work requires no repeated command invocation. Startup
must be idempotent, and required initialization must also work when the first
delivered event is not startup. This matters when startup is asynchronous or a
host resumes an existing conversation.

The shared runner retains its 480-second work budget within a 600-second
completion-hook allowance when supported. Adapter configuration converts units
explicitly. If a host/version enforces a shorter allowance, use a correspondingly
smaller runner budget with cleanup margin and report deferred work; do not claim
the full allowance or repeatedly restart successful commands.

Add platform-aware doctor checks for installation, subscriptions, root resolution,
result interpretation and supported response fields. Report configuration
validation, launcher replay and real installed-host observation as separate
evidence levels. Installation alone must not display a live-session pass.

## Validation and readiness

Before coding output-shape recognition, run the real producer or inspect a
versioned real-host capture. Keep scrubbed captures with host version and
provenance. Official schema examples remain labeled examples; invented fixtures
do not become real-host evidence. Read-only discovery on this machine found
`codex-cli 0.158.0-alpha.2.1`; Gemini, Cursor/agent and Copilot were not on PATH.
That PATH result does not prove the corresponding applications are absent.

For each adapter, cover legitimate and adversarial cases: success, nonzero exit,
timeout, cancellation, unknown/malformed results, duplicate calls, edits through
native tools and shell, missing/multiple roots, continuation loops and config
merge preservation. Exercise generated wiring through the shipped launcher with
a disposable project. Reuse the real durable-runner interruption test rather
than reproducing the entire runner test suite per adapter.

Run focused checks as each part lands, then the integration matrix at the
platform boundary. Broaden testing only for changes, failures or unresolved
risks. Preserve Claude compatibility throughout. Render all four architecture
views after interface/data-flow changes. Do not launch paid agent experiments
without the separately required authorization.

A platform is installed-session validated only after a real host loads its
configuration and delivers startup, a passing and failing declared command, an
interruption, an edit invalidating evidence and completion. When a host cannot
be run in the available environment, publish its exact tested boundary and open
acceptance item rather than calling fixture replay a live integration.

## Publication boundaries

Deliver platforms in the confirmed order: Codex, Gemini CLI, Cursor, GitHub
Copilot CLI. Each receives eight substantive pushes, thirty-two total:

1. Event and root adapter with regression tests. Codex's first part also
   introduces the shared host boundary while retaining Claude compatibility.
2. Command outcome interpretation and failure/incomplete regressions.
3. Response translation and engine dispatch.
4. Generated native subscriptions and distributable packaging.
5. Idempotent project setup and removal with configuration preservation.
6. Platform doctor and launcher integration checks.
7. Lifecycle hardening and integration corrections.
8. Documentation, installation journey, capability/readiness record and rendered
   architecture, with exact checks and limitations.

The shared design can accompany the first platform part. Later platforms reuse
the established interface. No empty commits or artificial splits are needed.
The user approved this design and directed immediate execution on 2026-09-29.

## Sources checked on 2026-09-29

- [Codex hooks](https://learn.chatgpt.com/docs/hooks): lifecycle, tool coverage,
  completion decisions and trust requirements.
- [Gemini CLI hooks](https://geminicli.com/docs/hooks/reference/): event envelopes,
  retry semantics and timeout units.
- [Cursor hooks](https://prod.cursor.com/docs/hooks): workspace inputs, tool
  events, asynchronous startup and completion follow-ups.
- [GitHub Copilot hooks](https://docs.github.com/en/copilot/reference/hooks-reference):
  native CLI envelopes, failure events and completion decisions.

These sources define the integration targets; they do not establish a minimum
supported host version until producer checks validate that version.
