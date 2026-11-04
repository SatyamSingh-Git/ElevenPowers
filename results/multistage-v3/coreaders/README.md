# Co-readers: does reading the same inputs find left-behind copies? ($0)

PLAN §13 B, open problem 1.

20 of the ElevenPowers arm's 31 v3 losses were copies: the rule the stage
changed was worked out a second time in another file. Every copy's recorded
discovery path in `case.json` is the same shape. The other file reads the
same inputs as the rule that changed:

- "TAX_RATES is read in two modules";
- "who else calls `daily_fine` or reads `max_fine`";
- "searching for uses of the overtime threshold".

The shared-rare-token ranking ([convention spike](../convention-spike/README.md))
put a dependent in its top 3 in 17 of 31 losses, but as a standing warning
it was noise. It mixes every identifier, literal and number.

## Plan, written before `coreaders.py` exists

**Query.** From the functions the stage's edit touched, before and after, take
only the inputs they read:

- names in `ALL_CAPS` (module constants);
- attribute names read off an object (`settings.daily_threshold` gives
  `daily_threshold`);
- string constants used as a subscript key or as the first argument of a
  `get`-style call (`row['qty']`, `config.getint('fine_grace_days')`).

**Documents.** The same three kinds of input, read anywhere in each other
non-test source file. Rarity weighting (IDF) and ranking are as in the
token spike, so only the query and documents change.

**Measured on the same ground as the token spike**, with the same controls:

1. the 31 losses, top 1/3/5, against another stage's edit as the control;
2. the held-out dependents (`heldout.py`'s 17 rankings);
3. noise over all 960 stages: warn rate on the 33 self-contained stages, and
   dependents named, at the same share thresholds.

**Decided in advance:**

- **Worth building as an on-demand question** ("which other files read what
  this edit reads?") if both hold:
  - held-out top 3 beats the token ranking's 4 of 17, and beats its own
    control;
  - in-sample top 3 is at least 14 of 31, which is no more than 3 below the
    token ranking.
- **Worth a standing warning** only if some threshold warns on at most 25% of
  self-contained stages while naming at least a third of the dependents the
  agent left unedited.
- Otherwise it is recorded as tried, and nothing is built.

**Bounds known in advance:**

- The 31 losses are where the paths above were read, so (1) is in-sample.
  (2) is the out-of-sample test.
- Copies are 20 of 31 losses. Contracts (9) and data (2) need not read the
  same inputs, so the result is also reported by kind.
