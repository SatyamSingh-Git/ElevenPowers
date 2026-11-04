# 97 — The first note an agent acted on

*2026-11-04. PLAN §13 B, open problem 2.*

In v3, import briefs reached the agent and were not acted on: the
ElevenPowers arm still left a dependent behind 31 times. The question
handed on by [96](96-a-rule-a-person-certifies.md) was whether a note a
person had certified would fare any better.

It did. Over 100 one-stage runs on the five v3 stages that lost most, with
superpowers and ElevenPowers in both arms and only the declarations file
different:

- the dependent was left behind in 35 of 50 runs without declared rules,
  and in 4 of 50 with them;
- the pre-registered exact one-sided stratified test gives p = 8.6 × 10⁻¹³;
- no other behaviour was lost in either arm;
- the cost was 8.5% higher.

## What nearly made it a different result

The pilot ran first, 12 runs, and was read for delivery rather than
effect. Half the rules-arm agents never touched the Edit tool. They wrote
every file by running Python in Bash, and the note was gated on an Edit, so
those agents never saw it. The $0 rehearsal had replayed only the Edit
path, and it passed.

The full run would have measured a note that reached half its arm. In the
full run, 21 of 50 rules agents edited only through the shell. With the
repair, all 21 kept the dependent. Without the note, 13 of 19 such agents
lost it.

The repair was rehearsed again with a shell write, going from 0 of 5 to
5 of 5. A probe on the real host, run both ways, then had the agent quote
the note word for word in one arm and say NONE in the other. The design
was amended before the run was sealed, never after.

## Why this note and not the import brief

Both are a sentence before an edit. The import brief says what imports a
file. Agents already know that, or can read it, and the dependents v3 lost
were mostly not import-reachable. The certified note names a file the
agent has no other reason to open. It also says what a person decided:
these files keep one rule. Then it gives two ways out, "change them
together, or say why one should differ".

The four losses took the second way, or simply missed it. Three named the
file and gave a reason for leaving it. On `parcelpost`, two reasoned from
the description's own words, "manifest_filename, day, isoformat": the
change "doesn't touch the filename".

That first read as a weak description, and this entry said so. The next
morning a blind stand-in reviewer, given only the pair's two files,
described the filename rule as well. The coupling the stage broke was
another one between the same files: billing's `groupby` relies on the
manifest's line order. The note named one tie of two, and the agents
checked that one correctly. The lead is withdrawn in PLAN §10
([record](../results/rule-groups-described/README.md)).

## What it is not

It is not evidence that ElevenPowers as shipped helps. The control arm
*is* ElevenPowers as shipped, and it lost 70%.

- **Certification was simulated as perfect.** The pairs accepted were
  exactly those a stage breaks.
- **Coverage is limited.** Proposals reach 20 of 51 never-read
  dependents, and the 31 others are untouched.
- **The stages were chosen for their losses.** The result says the note
  works where a loss is likely, not how often that is.

## And where no one needs it

A note that says "change them together" could make agents edit files a
stage never needed. So the same evening, the 53 stages the run had left out
were run once per arm, with a design and an analysis committed first:

- 20 covered stages, not chosen for their losses;
- 33 self-contained stages.

Nothing beyond a declared dependent was lost in either arm (0 of 53 each),
and no declared file was edited that the stage did not need (0 of 28
each). The covered dependent was lost in 2 of 20 runs in each arm: where
v3 never lost, there was nothing to gain.

One run per arm rules out a large harm, not a small one
([results](../results/rule-groups-harm/README.md)). Its mean time looked
25% worse. That was one run whose own command hung for the Bash tool's
120 seconds. Timing the hook itself took a minute at $0: 66 ms a shell
command.

The next questions are the person's half: does someone reviewing fifty
proposals keep the right ones, and describe them well enough?
