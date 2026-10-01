# Project onboarding and live diagnostics

Approved scope: automatic project onboarding, activation diagnostics, native edit attribution, and an actionable readiness report, generalized to all supported hosts. Snag is the acceptance project.

Setup uses the existing ownership-preserving hook merger. Claude Code joins the four native adapters in project setup; auto selection succeeds only with one available host. Multiple candidates require an explicit host choice. Setup discovers commands without executing them, checks interpreters and project coverage, and prints the next action. Host trust stays under the host's control.

Activation records distinguish configured/waiting, callbacks received, startup processed, and processing errors. Only launcher ingress records activation; in-process adapter fixtures and doctor replay do not. Receiving a callback is diagnostic evidence, not authentication of its sender. Records contain event names, timestamps and counters, never prompts, outputs or raw session identifiers. Changed wiring starts a new activation generation. State is atomic, bounded and protected by the existing short project lock.

Native patch attribution compares targeted content before and after a call. Paths come from explicit tool inputs or the documented apply_patch header grammar, never result prose. Call and session identities scope pending baselines. Missing identity/baseline, unreadable content, unsafe paths and budget exhaustion remain explicit coverage gaps. Content comparisons work without Git and on already-dirty files. This observes declared patch targets; it cannot prove absence of unrelated side effects.

Readiness combines configuration validation, live activation, discovered commands, scan coverage, environment diagnostics, latest declared-command execution, and next actions. Receipt freshness is not inferred from a stored passing result. Startup runs essential discovery/health automatically; completion retains the existing profile-dependent verification policy. No model inference or paid evaluation is started as part of setup.

Acceptance includes a disposable non-Git project with preexisting edits, all five setup/remove paths, launcher callbacks and replay separation, failed and incomplete commands, and Snag discovery/coverage plus actual local CI where its environment permits. Actual installed-host sessions are labeled separately from contract and launcher tests.
