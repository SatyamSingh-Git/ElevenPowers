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
change "doesn't touch the filename". The experiment's description was a
neutral template, deliberately worse than a person's. The product's own
proposal asks for the rule in words, and now the guide says why.

## What it is not

It is not evidence that ElevenPowers as shipped helps. The control arm
*is* ElevenPowers as shipped, and it lost 70%.

- **Certification was simulated as perfect.** The pairs accepted were
  exactly those a stage breaks.
- **Coverage is limited.** Proposals reach 20 of 51 never-read
  dependents, and the 31 others are untouched.
- **The stages were chosen for their losses.** The result says the note
  works where a loss is likely, not how often that is.

The next questions are the person's half: does someone reviewing fifty
proposals keep the right ones, and describe them well enough?
