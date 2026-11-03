# Spike: ordering the brief's importers (open problem 3, $0)

The import brief (`core/atlas.neighbourhood`) lists at most four importers
of the file about to be edited, alphabetically, then "+N more". In 5 of the
31 v3 losses the broken dependent imported an edited file but sat behind that
cutoff ([diagnosis](../README.md#why-elevenpowers-did-not-help-diagnosis-of-its-31-losses-0)).

[`replay.py`](replay.py) replays the brief on every v3 stage of all 120
conversations, both arms. Each unedited declared dependent that imports an
edited file is checked under four orderings of the same importers:

- **alphabetical:** what ships;
- **uses:** importers that name a function or class the edit touched come
  first (find-references, cut down to a token match);
- **tokens:** importers ranked by the rare tokens they share with the edited
  functions (the [convention spike](../convention-spike/README.md)'s score);
- **control:** the same token score, taken from another stage's edit of the
  same conversation. An importer that comes first for *any* edit is central,
  not pointed at.

Reordering adds no names, so it cannot raise false alarms. It can push out a
dependent the alphabetical brief showed, which is why every stage is
replayed, not only the losses.

## Result

33 rankings reach a dependent through imports: 9 are ElevenPowers losses and
7 are distinct dependents.

| shown in the first four | alphabetical | uses | tokens | control |
|---|---|---|---|---|
| the 9 losses | 4 | 4 | **8** | 4 |
| all 33 | 18 | 18 | 24 | 23 |
| the 21 at stages the spike was designed from (5 dependents) | 16 | | 19 | 16 |
| the 12 at other stages (2 dependents) | 2 | | 5 | **7** |

- **`uses` changes nothing.** The hidden dependents do not name the touched
  functions any more often than the importers listed before them.
- **The edit's own tokens look good only where the method was designed.**
  They give 8 of 9 losses against the control's 4. On the stages the spike
  was not designed from, the control does better: 7 of 12 against 5 of 12.
  Most of the overall gain is any token ordering pulling large, central
  importers forward, not this edit pointing at them.
- **Moved one out.** Token ordering pushed out 1 dependent the alphabetical
  brief showed, and newly showed 7.

## Bounds and decision

- **Small.** 7 distinct dependents in all, and 2 outside the designed-from
  stages.
- **Proxy.** The stage's whole change stands in for the single edit a
  PreToolUse hook would see.
- **Shown is not acted on.** The 4 dependents the shipped brief did show were
  delivered and ignored (open problem 2).

**No change to `neighbourhood`.** Nothing here shows an ordering that tracks
the edit rather than the file's size. The cutoff accounts for at most 5 of 31
losses, and fixing it would not reach the 22 dependents that import nothing
the agent edited.
