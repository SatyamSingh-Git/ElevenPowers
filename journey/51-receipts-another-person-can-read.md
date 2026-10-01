# 51 — Receipts another person can read

2026-10-01. The user asked to finish onboarding, publish it in ten separate
pushes, then build the next most important thing. The ten onboarding pushes
advanced the feature branch separately and the final atomic push advanced main.
The next delivery was a local report a reviewer could read without the session.
The user then requested fifteen separate pushes for that new report work. The
unpublished implementation was preserved in a local backup branch and divided
into runtime, CLI, controls, guides, architecture, journey and validation parts.
The final part advances main; earlier parts remain on the delivery branch.

It had to work for any project. Snag remained an acceptance case, with no path,
command or special rule in runtime logic. The report borrows the shared ledger's
obligations and verdicts rather than creating another verification engine. What
it adds is a bounded, freshly observed, portable evidence surface.

## A receipt is useful only if its qualifications travel with it

`core/export.py` and `plugin/bin/ep_report.py` export Markdown and schema-version-1
JSON. They carry computed claims, qualified obligations, latest execution
receipts, current freshness, edited targets, revision, coverage and next actions.
No claim means UNVERIFIED; a passing command is not a claim that work is complete.
Prompts, transcripts, captured outputs and receipt details are omitted. Known
credentials are scrubbed and project-root text is substituted. Output defaults
to stdout; explicit files are atomic and refuse overwrite unless forced.

The first implementation shared one fresh source scan with the verdict engine.
A fresh review found six ways the export still failed its own contract:

1. An explicit README receipt could stay fresh after a same-size edit with its
   old timestamp restored. The source scan did not include Markdown, and that
   receipt fell through to the ordinary digest cache.
2. HTML escaped correctly, but supplied Markdown images, links and emphasis
   still rendered as Markdown.
3. Revision lookup reused a helper that wrote to an active verification journal,
   even when the report selected another project.
4. Latest receipts used append order while the verdict engine used timestamps.
   An out-of-order older failure could appear beside a verified state.
5. Markdown discarded obligation caveats that JSON preserved, including the
   qualification that suite-grain reproduction is not a separate named-test
   finding.
6. The deadline covered the source scan, while duplicated verdict computation
   and independent revision lookup could continue without reporting exhaustion.

Failing controls reproduced all six. Explicit receipts now read fresh bytes in
the scoped report view and share the file/byte budgets. Unsafe inputs and failed
reads leave coverage incomplete. Markdown keeps supplied text literal and retains
caveats. Revision reads Git metadata directly without verification jobs. Receipt
selection uses timestamp and later-entry ties. Verdicts are computed once; the
operation shares a cooperative deadline and reports exhaustion after in-flight
work returns. A nested-view control found one more cache leak and flipped after
the inner snapshot was isolated from the outer one.

## The real acceptance artifact stayed red

Exporting Snag's recorded state took no project command or model call. Under the
same account and ignore policy as the earlier relay, the report selected 4,417
files / 81,841,184 bytes and recorded revision
`1906da4576f29b02131ff50a29204529b8bcbb5e`. Its actual `npm run ci` receipt remained
fresh, complete and failed. The report's task state was UNVERIFIED because no
active claim existed. The earlier CI had passed 14/15 checks and failed the
production dependency audit; exporting it did not change that outcome.

This is a basic receipt report. PLAN §5.17's mutation findings remain unbuilt,
and no improved patch outcome is claimed. Four added hosts still need versioned
native-session acceptance. Those boundaries belong beside the delivery, not in
a future footnote. Exact checks are in the [validation record](../docs/validation/2026-10-01-portable-report.md).
