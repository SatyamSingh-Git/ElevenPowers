# 9. What a real prompt looks like

## A second question the corpus could answer

Replaying 241 sessions was built to check one thing: whether the runtime reads
tool results correctly. Having 3,557 real turns sitting there made a second
question cheap, and it was a question the project had been unable to ask.

Claim inference decides whether the runtime engages at all. Infer a claim and
the gate will demand proof; infer none and the layer sits out the task. It had
never been measured against anything except scenarios written by the person who
wrote it.

There is no host-recorded ground truth for a claim the way there is for a
command's exit status. There is the next best thing: **what the turn did**. A
turn that changed no file did not add a feature, whatever its prompt sounded
like. That signal is a proxy and wrong at the edges, but it covers 3,557 turns,
which no amount of hand labelling would reach.

## The first result

```
turns              3557  (1945 changed code, 1612 did not)
claim, no work     51%
no claim, work      5%
```

More than half of all turns that changed nothing had obligations attached to
them. The gate would have demanded a test for "analyze what this repo does".

On the 46 constructed scenarios the false-block rate was 0 percent. The two
numbers are not in conflict; they measure different populations. Every scenario
in that suite was a piece of work. **The suite contained no conversations at
all**, and real sessions are mostly conversation.

The cause was one line:

```python
if not found:
    return [Claim.FEATURE_ADDED] if len(text.split()) > 2 else []
```

Any sentence longer than two words that was not a question claimed a feature.

## The worse finding

Looking at the turns that changed code but got no claim surfaced something the
over-claim number had hidden. In `on_prompt`:

```python
claims = infer(request)
if not claims:
    ledger.claims = []      # <-
```

A prompt with no claim in it **cleared the claims of work already in progress**.
So the gate switched itself off the moment the user typed "continue", which is
the single most common thing a person types mid-task. In the corpus, 64 prompts
were bare continuations and 53 of them changed code.

That is the same defect class again: not a wrong answer, but a component quietly
declining to participate.

## What real prompts are actually like

The corpus is blunt about this.

- One prompt in five is **four words or fewer**.
- 300 of those still changed code.
- "continue", "go on", "yes do it", "see this", "ok now the other one" carry
  their subject in the conversation, not in the message.

A classifier reading the prompt alone cannot do this job, and no amount of
pattern tuning changes that. The intent is not in the text being classified.

## Deriving the claim from the work

The answer is the one the scope guard already arrived at: stop trying to know up
front, and read what the task does.

- A prompt that states a subject sets the claim, as before.
- A prompt that states no subject leaves an open claim alone.
- A prompt that explicitly asks for something else, a question or a request to
  read or review, clears it.
- **The first edit to a source file opens a claim if none is open**, unless the
  prompt explicitly asked for something that is not a change.

That last rule is what makes short prompts work. "make the sidebar collapsible"
names no claim pattern and gets none; the edit that follows opens one. And
"explain the auth flow" stays quiet even if a file gets touched along the way,
because the prompt said what it wanted.

## Two smaller things the corpus exposed

**Agents write files through the shell.** `cat > file` appeared 1,431 times in
36,000 commands, and 637 turns changed the repository without touching an edit
tool at all. A runtime watching only `Edit` and `Write` is blind to every one of
them. Redirect targets are now read from the command, narrowly: a target needs a
file extension, which rules out `>&2`, `> /dev/null` and most of the ways a
redirect is not a file.

**A pasted stack trace was classified as a request to go and read something.**
The no-claim rule matched the bare word `read` anywhere in the message, and
"TypeError: cannot read property id of undefined" contains it. Those verbs are
imperatives, so the rule is now anchored to the front of the message.

## Where it ended up

```
over-claim rate    51% -> 21%
miss rate          68% -> 25%   (11% on turns whose change the runtime can see)
labelled prompts   31/31
```

Unchanged alongside it: 0 percent false blocks and 0 percent misses on the 46
gate scenarios, 0 and 0 on the 25 scope cases, 225 tests green.

## What these numbers do not say

The proxy conflates two different things inside that 21 percent. A claim
inferred where the prompt was not asking for work is an error. A claim inferred
correctly on "fix the login bug", followed by an agent that investigated and
changed nothing, is the gate doing its job: the right response there is to
discharge the obligations or record `cannot_complete`. The residual contains
both and the proxy cannot separate them.

The remaining misses are mostly turns that changed the repository in ways that
name no file at all: `mkdir`, `npm install`, `git checkout`. Whether those
deserve a claim is a real question and not one this measurement settles.

## A note on the corpus

The 241 sessions are one person's real work across thirty of their own projects,
and they contain resumes, business detail, server names and private
correspondence. Nothing from them is committed. The replay tools read from the
machine they run on; `eval/claim_cases.py` holds 31 prompts **written** to match
the shapes observed, not copied from them. What the repository takes from the
corpus is what real prompts are like, not what they said.
