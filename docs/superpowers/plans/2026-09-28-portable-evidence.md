# Portable repository evidence implementation plan

**Goal:** Implement the user's approved repository-aware scanning and declared-command recognition for any project, with Snag as a read-only compatibility check.

**Architecture:** Extend the existing evidence and parser boundaries. Git supplies tracked and non-ignored candidates; a bounded filesystem fallback supports non-Git projects. Scan limitations travel with evidence and prevent a fresh/verified claim. Configured commands are trusted only by exact declaration, with runner counts retained when available and incomplete execution explicitly recorded.

**Constraints:** Python 3.11+, standard library runtime, backward-compatible saved ledgers and configuration. No Snag paths or command names in runtime logic. No deployment or edits to Snag. Preserve passive mode behavior.

- [x] Add failing scan tests: ignored data, untracked source, hidden CI configuration, nested repositories/symlinks, truncation and unreadable files.
- [x] Implement scan metadata, configurable exclusions/budgets, freshness and report integration in existing modules.
- [x] Add failing declared-command tests: exact match, unrelated command, passing/failing/empty output, timeout/interruption and hook collection.
- [x] Implement declaration-aware parsing and automatic-verification error records.
- [x] Update configuration documentation and architecture graph; run targeted tests and the full suite after review fixes.
- [x] Measure Snag scan coverage/performance and representative output recognition without installing the plugin there.

Review especially: a tracked file matching an ignore rule; a failing sub-run masked by exit zero; a previously green command interrupted later; an empty source scan; an unreadable or oversized input. No partial evidence may silently turn into a fresh successful receipt.
