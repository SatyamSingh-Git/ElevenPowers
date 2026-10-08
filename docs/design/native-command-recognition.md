# Native declared-command invocation qualification

The installed staged comparison exposed an exact-match gap: an observed
`cd PROJECT && python -m unittest discover -s tests -v` did not bind to the
declared command. This milestone repairs that generalized capture seam, without
claiming fresh installed acceptance or coding improvement from a replay.

## Contract

Use the standard-library `shlex` literal token reader, with a narrower explicit
grammar than a general shell parser. Add qualification, not shell execution or
command rewriting. Keep exact configured invocations compatible.

- Recognize one `cd LITERAL && EXACT_DECLARED_COMMAND` prefix. Preserve the
  leaf command byte-for-byte apart from existing outer whitespace handling.
- Resolve literal directories against the project/tool directory and require
  an existing directory with the same resolved identity as the project root.
  Double-quoted spaces and forward-slash paths work across the portable subset.
  Single quotes, UNC paths, drive-relative paths, Windows rooted paths without
  a drive and parent-traversal components are excluded because shell semantics
  differ. Scope classification uses the qualified identity, never the raw prefix.
- Reject interpolation, globbing, control characters, unsupported setup,
  command aliases, extra arguments, pipelines, output redirection, multiple
  directory changes and trailing commands as automatic equivalences. A project
  may still explicitly declare its full aggregate command.
- Tool directory metadata must qualify for the project. An invalid/mismatched
  directory cannot provide passing project evidence. Retain an incomplete
  attempted receipt when the declared leaf identity is known.
- Preserve `Evidence.command` as the scrubbed observed invocation, and use the
  existing `declared_command` field for the exact scrubbed configured identity.
  Use that identity consistently for freshness, history and fresh-result reuse.
- Keep success, failure, interrupted/missing status and counted-failure outcomes
  distinct. A wrapper is not evidence that individual assertions ran.
- All five host adapters share this runtime behavior. No project names, paths,
  special npm scripts, dependencies, model calls or default-on advice are added.

## Evidence and limits

Forward controls run real project commands through installed local shells;
wrong directory, shell chains, failure and interruption are separate controls.
Replay callbacks qualify capture plumbing and do not establish an installed
model session, advice consumption or improved coding outcomes. Preserve the
earlier four-session experiment unchanged. Shell-specific setup forms beyond
the portable literal subset remain explicit limitations.
