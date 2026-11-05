# Track B: coding-agent products and practices that work in the field

2026-11-05. Grades: **(read)** = I read the page itself; **(snippet)** = search summary only, so don't quote it as read. "Vendor" = the seller is reporting on its own product. I read 38 pages directly.

## 1. Findings, ranked by strength of evidence × relevance

**F1. The verification loop that works is "give the agent a pass/fail check it runs itself", and the host now ships it.**
- **Claude Code best-practices doc** (read, vendor, 2026), https://code.claude.com/docs/en/best-practices.
  - It tells users to "Give Claude something it can run that comes back pass or fail".
  - It offers enforcement at increasing strictness: prompt, `/goal`, Stop hook (exit 2 blocks), and `/code-review` in a fresh subagent.
  - It says to "ask Claude for *evidence*: the command it ran and its output".
  - It also says to keep the enforced set of hooks and rules small; at forty, most are probably preferences.
- **The gap in `/goal`** (read), https://code.claude.com/docs/en/goal. The evaluator "doesn't run commands or read files independently… can only judge what Claude has already surfaced in the conversation."
- **Practitioners say the same thing:**
  - Hashimoto (read, 2026-02-05, https://mitchellh.com/writing/my-ai-adoption-journey): "If you give an agent a way to verify its work, it more often than not fixes its own mistakes."
  - Anthropic's long-running-harness post (read, 2025-11-26, https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): Claude marked features done after unit tests or `curl`, and browser automation "substantially improved" results.
  - Boris Cherny's "2-3x quality" claim is anecdote (snippet).
- **Limit:** this is consensus among practitioners and vendors. Nobody has run a controlled measurement.

**F2. The bottleneck has moved downstream to review and QA, and that is where the money is going.**
- **Faros AI Engineering Report 2026** (read, vendor telemetry, 22,000 developers, 4,000+ teams, 2026-04-12), https://www.faros.ai/blog/ai-acceleration-whiplash-takeaways. Under high AI adoption:
  - median time in review +441.5%
  - incidents per PR +242.7%
  - churn +861%
  - PRs merged with no review at all +31.3%
  - *Limit:* this compares each organization's low- and high-adoption periods. It shows correlation, not cause.
- **He et al., MSR '26** (read, independent difference-in-differences study of Cursor adoption), https://arxiv.org/html/2511.04427v3.
  - Lines added rose 281% in the first month, and the velocity gain was gone after two months.
  - Static-analysis warnings rose a persistent +30.3%.
  - Complexity rose +41.6% (the text says 25% elsewhere, so the paper is inconsistent).
  - *Limit:* open-source JS/TS/Python projects, intent-to-treat.
- **Anthropic Code Review** (read, vendor, 2026-03-09), https://claude.com/blog/code-review.
  - Code output per engineer is up 200%.
  - Substantive review comments rose from 16% to 54%.
  - Reviews cost $15–25 each.
- **Where the money went:**
  - Cursor bought Graphite to "own review" (snippet, 2025-12-19).
  - CodeRabbit is estimated at about $40M ARR (snippet, an estimate).
  - Qodo raised $70M for "code verification" (snippet).
- **Merged agent PRs often get no human review** (amplifying.ai, read, sample of 268 merged PRs, 2026-07/08), https://amplifying.ai/coding-agents/autonomy. 56% of merged agent PRs in significant repos had no human reviewer.

**F3. First-party, host-integrated agents win distribution, and IDE add-ons are being absorbed or shut down.**
- **PR volume** (amplifying.ai, read, week ending 2026-11-01), https://amplifying.ai/coding-agents/trends: Claude Code 1.6M PRs, Codex 318K, Cursor 119K, Copilot agent 12K, Devin 10.6K. On 2026-11-03, 20.2% of public PRs were marked as made with Claude.
- **Use at work** (JetBrains survey, April–May 2026, 15,000+ developers; read via https://www.i-programmer.info/news/99-professional/19118-jetbrains-reveals-widespread-adoption-of-ai-coding-agents-.html): Claude Code rose from 3% to 39%, and Copilot fell from 29% to 21%.
- **Stack Overflow 2026** (read), https://survey.stackoverflow.co/2026/ai: among coding agents, Claude Code is used by 66% and Copilot by 59%.
- **Exits:**
  - Roo Code had about 3M installs and shut its extension on 2026-05-15 to go cloud-only (snippet).
  - Amp discontinued its VS Code extension (snippet).
  - Jules winds down on 2026-12-31 (snippet).
  - Aider is in maintenance mode (read, secondary, https://rywalker.com/research/aider).
  - Supermaven, Aide and Void are gone. The analysis's lesson: single-feature tools get built or bought by larger ones (read, https://codemyspec.com/blog/dead-ai-coding-tools-supermaven-aide-void).
- **Limit:** the counts depend on attribution. Claude Code marks its PRs by default, which inflates its share.

**F4. The most-adopted add-on is a process pack that optimises speed and cost. Standalone "receipt" checkers get almost no traction.**
- **Superpowers:**
  - 313k stars (read, https://github.com/obra/superpowers) and listed second on claude.com/plugins (read; the sort criterion is unstated). About 752k installs (snippet).
  - The README publishes no outcome measurements.
  - Its v6 work (read, 2026-06-15, https://blog.fsck.com/2026/06/15/Superpowers-6/) targeted "50% faster, 60% cheaper" on its own evals. Its planted-defect gates passed 2 of 3.
  - On Reddit, users say they disable it because "vanilla Claude has caught up" and it adds token bloat (snippet).
- **Hook-based enforcement and receipt checkers:**
  - TDD Guard: 2.4k stars (read, https://github.com/nizos/tdd-guard).
  - Probity, its multi-host successor: about 32 stars (snippet).
  - groundtruth, a Stop-hook receipt checker: 0 stars (read).
  - cngx: 10 upvotes (read). A commenter asked whether it catches "trivially passing tests". Nobody answered.
- **Limit:** stars and installs are not usage.

**F5. Heavy spec-first process has weak field support.**
- **Böckeler** (read, 2025-10-15, https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html):
  - Kiro was "way too verbose" for a small bug.
  - spec-kit "created a LOT of markdown files".
  - "I frequently saw the agent ultimately not follow all the instructions."
- **Market signals:**
  - Kiro had a pricing backlash (snippet).
  - Tessl pivoted from specs to a skills registry (snippet).
- **Claude Code's "stop doing" list** (read) includes describing your architecture in CLAUDE.md.
- **Limit:** Spec Kit has about 72k stars (snippet). The idea is popular even though nobody has measured outcomes.

**F6. Behaviour verification and test adequacy are the open problem the field names. ElevenPowers has a measured result there.**
- **Böckeler, "Harness engineering"** (read, 2026-04-02), https://martinfowler.com/articles/harness-engineering.html:
  - Behaviour is "the elephant in the room".
  - Relying on AI-generated tests is "not good enough yet".
  - Open question: does a silent sensor mean high quality or weak detection?
- **Tests in agent PRs:**
  - The share of agent PRs with tests rose from 31% to 52% (read, https://arxiv.org/html/2601.03556v1).
  - A comparison with human PRs found no difference in test smells (read, https://arxiv.org/html/2601.21194v1).
  - Neither paper measures fault detection, and both list it as future work.
- **Meta's mutation-guided test generation (ACH):** engineers accepted 73% of the tests it generated (snippet, arXiv 2501.12862).
- **Limit:** I found no evidence of anyone buying test adequacy as a product.

**F7. The working practices are concrete, mechanical and small.**
- **Practices reported:**
  - one feature per session
  - a progress file plus git
  - `init.sh` and a smoke end-to-end test first (Anthropic harness post)
  - add an AGENTS.md line only after a bad agent behaviour
  - scripted tools for screenshots and filtered tests (Hashimoto)
  - linters and structural tests that enforce dependency layers (OpenAI, via InfoQ, read: https://www.infoq.com/news/2026/02/openai-harness-engineering-codex)
  - prefer computational controls over inferential ones (Böckeler)
  - a type checker is mandatory, and no Ralph loops on existing codebases (Huntley, read, https://ghuntley.com/ralph/)
  - small PRs that carry proof of manual testing and screenshots (Willison, read, https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/)
  - Showboat `exec` records real output (read)
- **Typed languages:** Octoverse (read, https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/) ties TypeScript reaching #1 to typed languages making agent work more reliable.
- **Devin** (read, vendor, https://cognition.com/blog/devin-annual-performance-review-2025):
  - PR merge rate rose from 34% to 67%.
  - It succeeds with "clear, upfront requirements", "verifiable outcomes" and 4–8 hour tasks.

**F8. Trust follows verifiability.**
- **Stack Overflow 2026** (read): 48% trust AI when they "can easily validate".
- **Anthropic internal study** (read, n=132, 2025-12-02, https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic):
  - engineers delegate "easily verifiable" tasks
  - most can fully delegate only 0–20% of their work
- **Cursor Bugbot** (read, vendor, 2026-01-15, https://cursor.com/blog/building-bugbot):
  - Its success metric is resolution rate, meaning flagged bugs fixed by merge. It rose from 52% to over 70%.
  - It runs on more than 2M PRs a month.
  - It hill-climbed on that one online metric.

## 2. What is working that ElevenPowers does not do

- **Review at the PR, where teams already work,** with a published outcome metric (Bugbot, CodeRabbit, Claude Code Review). *(F2, F8)*
- **Visual and browser checks:** Playwright and Chrome DevTools rank high on claude.com/plugins, and Claude Code has `/verify`. *(F1)*
- **Mechanical architecture sensors:** dependency-layer lints, structural tests, LSP diagnostics. *(F7)*
- **Human-readable proof in the PR,** such as Showboat output or screenshots. *(F7)*
- **Session provenance:** Entire Checkpoints has 4.1k stars and a $60M seed (snippet).
- **Mutation-guided test generation** (Meta ACH). *(F6)*
- **Background and cloud agents that open PRs.** *(F3)*

## 3. What contradicts or undercuts the current approach

- **The host now ships the receipts layer.** Stop hooks, `/goal`, `/verify` and `/code-review` cover "asks for the receipts". Inside the loop, ElevenPowers is a second copy of a first-party feature. *(F1, F3)*
- **The overhead runs against what the market pays for.** ElevenPowers costs 1.4x and takes 3.1x model time, while the leading add-on just cut cost and time by half, and users drop packs over token bloat. *(F4)*
- **"Did the tests run" is commoditised.** At least four checkers exist, and the ones with visible numbers have almost no adoption. *(F4)*
- **The brief before edits and the milestone injection look like context files.** The project's own AGENTS.md entries are null, its v3 result is null, and Claude Code's own doc says to stop doing this. *(F5)*
- **Practitioners guard earlier behaviour with tests, types, structural lints and CI, not briefs.** That matches v3's null result and the declared-rules result. *(F7)*
- **ElevenPowers sits in the solo developer's loop across five hosts.** The pain and the budgets are in team review. *(F2, F3)*

## 4. Lessons

**Borrow**
1. **Bugbot's discipline:** one online outcome metric to hill-climb, for example "vacuous patches caught and fixed before merge". *(F8)*
2. **Mutation-guided adequacy:** mutmut, Stryker or PIT, and Meta ACH's approach for the discriminating test. Then add only the patch-versus-base check. *(F6)*
3. **Feed the host's own gates.** Expose hash-bound evidence as a Stop-hook or `/goal` signal, because the `/goal` evaluator cannot run anything. *(F1)*
4. **Showboat-style evidence blocks** in PR descriptions. *(F7, F8)*

**Stop**
1. **Default-on briefs and milestone injection.** *(F5, v3)*
2. **Automatic discovery of co-change rules.** Ship declared rules (LINT.IfChange) as a computational check in CI. *(F7, the declared-rules result)*
3. **Positioning as a process framework or a "did tests run" checker.** *(F4)*
4. **Five host integrations as the main surface.** *(F3)*

**Try**
1. **A CI/PR check (a GitHub Action) for agent PRs.** It runs the changed tests on base and on the patch. It flags patches that no test can tell apart from base, and tests that pass both ways. It posts an *applicable* generated discriminating test as the fix, because the earlier review-comment study found an applicable suggestion is the strongest predictor of action. *(F2, F6)*
   - CI time replaces model time, which removes the 3.1x objection.
   - The buyer is the team, with a free tier for open source, as CodeRabbit does.
2. **A no-agent demand and size test first.** Measure vacuity on a sample of public merged agent PRs from AIDev or amplifying.ai. That gives a publishable in-the-wild rate cheaply, and it tells you whether the problem is big enough. *(F2, F6)*
