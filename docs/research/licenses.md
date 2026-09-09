# License and attribution register

Read from each clone's LICENSE file on 2026-09-09 at the commits recorded in `cards/`. Obligations listed are those that apply if code, prompts, templates, or documentation are reused; ideas and abstractions carry no obligation.

| System | Commit | License (SPDX) | Copyright holder | Reuse obligations | Caveats found in source |
|---|---|---|---|---|---|
| obra/superpowers | b36e0829 | MIT | Jesse Vincent, 2025 | Keep copyright and license notice | `skills/writing-skills/anthropic-best-practices.md` reproduces Anthropic guidance and is not clearly under the repo's MIT grant; do not redistribute it |
| affaan-m/ECC | 5064474d | MIT | Affaan Mustafa, 2026 | Keep copyright and license notice | `gateguard-fact-force.js` credits an upstream `zunoworks/gateguard` package; check its terms before porting the classifier wholesale |
| github/spec-kit | 0c8e31ff | MIT | GitHub, Inc. | Keep copyright and license notice | Bundled extensions and presets declare MIT in their manifests |
| garrytan/gstack | caba78fe | MIT | Garry Tan, 2026 | Keep copyright and license notice | `CLAUDE.md` asks contributors not to edit `ETHOS.md`; a norm, not a license term. Repo embeds a Supabase key and a `curl bun.sh/install \| bash` line in skill text; do not copy either |
| bmad-code-org/BMAD-METHOD | abe4eb1b | MIT | BMad Code, LLC, 2025 | Keep copyright and license notice | `TRADEMARK.md` restricts use of the BMad and BMAD-METHOD names and marks; persona names are product identity |
| Aider-AI/aider | 5dc9490b | Apache-2.0 | Aider contributors | Keep license notice; preserve NOTICE if present (none seen); state changes | Patent grant included. `repomap.py` depends on `grep_ast`, `networkx`, `diskcache`; check their licenses when vendoring |
| anomalyco/opencode | 830d5eb5 | MIT | opencode, 2025 | Keep copyright and license notice | Provider system prompts read as derivatives of Claude Code prompts; do not ship verbatim. Auth plugins reverse-engineer third-party OAuth flows; the third parties' terms govern use |
| cline/cline | b18de090 | Apache-2.0 | Cline contributors | Keep license notice; preserve NOTICE if present; state changes | Patent grant included. Branding, "You are Cline" prompts, account and telemetry code are not to be reused |
| continuedev/continue | 5522c6f4 | Apache-2.0 | Continue contributors | Keep license notice; preserve NOTICE if present; state changes | Patent grant included. `core/vendor` grammars carry their own licenses; check before vendoring the chunker |
| SWE-agent/SWE-agent | 3ea751c0 | MIT | SWE-agent contributors | Keep copyright and license notice | `str_replace_editor` docstring credits OpenHands (also MIT) |
| SWE-agent/mini-swe-agent | 04d809ce | MIT | SWE-agent contributors | Keep copyright and license notice | |
| OpenHands/software-agent-sdk | 6a1e4d0 | MIT | OpenHands contributors | Keep copyright and license notice | Prompt text references the OpenHands brand; do not reuse prompt text |
| OpenAutoCoder/Agentless | 5ce5888 | MIT | Agentless authors | Keep copyright and license notice | Hard-wired to SWE-bench loaders |
| nus-apr/auto-code-rover | 585d3e6 | Sonar Source-Available License v1.0 (no SPDX id) | SonarSource | Not open source. Non-competitive-purpose clause; literal reading forbids use with external AI tooling | Ideas only. No code, prompt, or data reuse |
| openai/codex | b4d4205 | Apache-2.0 | OpenAI | Keep license notice; preserve NOTICE if present | Host only; nothing reused |
| google-gemini/gemini-cli | ed2ac40 | Apache-2.0 | Google LLC | Keep license notice; preserve NOTICE if present | Host only; nothing reused |

Project license decision (ADR-005, pending): Apache-2.0 is compatible with reuse from every system above. MIT-licensed material can be included in an Apache-2.0 project with its notice preserved. A `NOTICE` file will list every reused file with its origin, commit, and license, and every reused file will carry a provenance header.
