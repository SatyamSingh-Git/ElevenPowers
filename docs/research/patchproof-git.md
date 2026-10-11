# Git provenance for PatchProof v1

Read 2026-10-11. Git is invoked as an installed executable, not vendored or linked
into the Python runtime. Git supplies object/tree identities and native raw
comparison; its GPL-2.0 license is separate from this repository's runtime license.

The local producer is `git version 2.45.1.windows.1`. NUL raw changes and binary
numstat were observed in disposable repositories before parsing. The runner
retains binary output; a digest binds the commit pair and another binds the full
tree pair, independently of formatted diff output.

The independent review found real worktree-configured filter execution and lazy
promisor retrieval during supposedly read-only Git collection. The implemented
policy enumerates effective permitted filter config, prohibits lazy fetching and
transport protocols, and requires Git 2.45+ rather than silently relying on an
environment variable an older executable might ignore.

Git documents [`GIT_NO_LAZY_FETCH`](https://git-scm.com/docs/git) as disabling
on-demand retrieval of missing promisor objects. The pinned
[Git v2.45.1 implementation](https://github.com/git/git/blob/v2.45.1/promisor-remote.c#L25)
checks the setting before launching the fetch child. This source establishes the
minimum used here; real missing-object controls establish the local behavior.
Git's [partial-clone design](https://git-scm.com/docs/partial-clone) explains why
commands that need missing object contents may otherwise retrieve them.

Before/after collection is still not atomic, and a trusted installed Git binary
and object-store integrity remain assumptions. Missing objects produce explicit
incomplete identity instead of automatic retrieval. No helper, transport,
model or project command is needed to export an already available patch.
