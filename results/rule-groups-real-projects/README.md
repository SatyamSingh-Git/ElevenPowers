# Rule-group proposals on real projects

*Plan written 2026-11-05, before the measurements below were taken. $0, no model.*

Every measurement of `ep_milestones --propose` so far is on the twelve v3
cases, which were written for the experiment. The project's standing rule
is to check portable behaviour on unrelated projects. One run on `click`,
made only to read the output's shape, showed its top three proposals were
two `__repr__` methods, two `__getattr__` methods and two `writelines`
methods. That is boilerplate no one would certify. This check asks how
typical that is.

## Projects

Copied as they are installed, `git init`-ed, and run with the defaults
(`--limit 50`, 30 seconds):

- `attr` (13 Python files), `click` (17), `_pytest` (78), `rich` (100),
  `sqlalchemy` (258), from site-packages;
- ElevenPowers itself at `HEAD`, as a user would run it.

## Measures

1. **Runs:** exit status, wall time, whether coverage is complete, and the
   gaps it names. Pass: every project exits 0 within the deadline plus
   5 seconds, and any gap is named.
2. **What fills the top 50**, sorted into three kinds by the two function
   names:
   - **dunder:** both are `__x__` methods;
   - **same name:** both have one ordinary name, such as an override or a
     copied helper;
   - **different names.**
3. **The same sort on the v3 cases,** for all top-50 proposals and for the
   27 certified pairs, the pairs some stage breaks.
4. **Co-change, on ElevenPowers only,** because it has history. For each
   top-50 pair: has any commit modified both files, neither being added?
   The base rate is the same question over every pair of files that both
   define functions.

## What follows

- **If dunder pairs fill a real share of real projects' top 50 and none of
  the 27 v3 truth pairs is one,** excluding them is a candidate. It is
  adopted only if, re-run on v3, it loses none of the 20 never-read
  dependents the proposals cover, and on the real projects it frees slots
  for pairs of the other kinds.
- **Same-name pairs are not a candidate for exclusion,** whatever they
  show. A rule copied under one name, such as `parcelpost`'s two `vat`
  functions, is the case the method exists for.
- Otherwise the findings are recorded as they are.
