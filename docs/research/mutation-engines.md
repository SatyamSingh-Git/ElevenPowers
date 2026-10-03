# Mutation engine provenance

On 2026-10-03, a real baseline/attempt probe exposed that mutation restoration
bytes overwrote the original-project path passed to the Python read/import guard.
The baseline retained its proper guard; attempts did not. The path now remains
separate from restoration bytes. Both the forbidden-original-read and legitimate
private-input controls pass, with all 45 existing strength controls. Historical
analysis does not prove that original-project reads were excluded; earlier
observations remain recorded rather than being relabeled after this fix.

Cosmic Ray 8.7.0 (MIT), https://github.com/sixty-north/cosmic-ray, supplies Python
operators, AST traversal and source mutation. Enumeration follows its
`commands/init.py`; the optional child imports its installed library. ElevenPowers
adds changed-file selection, isolated copies, hard attempt/time caps, contained
test execution, exact-input reuse and qualified human reports. Argument-requiring
operators are omitted. Missing/unsupported versions are explicitly unavailable.

The 2026-10-03 adapter retains the installed Cosmic Ray parser/operator positions
and original occurrence indices, then filters before materializing a mutation.
Python's standard-library AST supplies function/async-function/decorator spans.
Git's zero-context diff supplies current changed lines. ElevenPowers adds the
relationship between those positions and the actual edit: partition broad hunks,
choose the smallest containing function, retain module-only segments and require
complete mutation-span containment. Targeted enumeration is capped at 100,000
eligible descriptors; source is capped at 1 MiB. File/function rotation and
changed-line priority narrow the sample without claiming semantic coverage.

Copyright (c) 2015-2017 Sixty North AS

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Native Windows producer probe: Python 3.13.2 / Cosmic Ray 8.7.0 generated seven
mutations for a comparison function, including `> 0` → `>= 0`. This establishes
producer compatibility, not universal language syntax or project setup support.

StrykerJS instrumenter 9.5.1 (Apache-2.0),
https://github.com/stryker-mutator/stryker-js/tree/master/packages/instrumenter,
supplies JavaScript/TypeScript mutations and replacement ranges. The optional
worker calls its installed public instrumenter and applies one generated
replacement to original source at a time. No engine code is vendored. ElevenPowers
adds the same isolation, selection, budgets and reports as the Python adapter;
Stryker's coverage optimization, dashboard, runner plugins and incremental cache
are not used. The project's command must execute or rebuild changed source.

Function attribution also uses the installed instrumenter's
`dist/src/parsers/index.js` `createParser`, with its Babel/TypeScript AST locations.
This is a pinned **internal API**, not a promised stable interface; other versions
remain unsupported. Source inspection and actual JavaScript/TypeScript/TSX
producer tests establish the observed node/location contract. Function, arrow,
object/class method and nested spans are considered. Unselected ancestor spans
are rejected; multiple functions on one line remain ambiguous. Descriptors are
bounded and selected before full replacement source is materialized.

The shared runner allocates attempts across language producers by selected file
counts, then each producer rotates files and functions. Exhausted time/attempts,
unavailable engines and removed behavior retain incomplete qualifications. Schema
2 adds bounded source ranges/context and recorded-command-only coverage; schema
1 remains readable as a legacy sample. A focused survivor can be covered by
another command, and equivalence is not established by survival. The read/import
guard is diagnostic and a private filesystem copy is not an OS sandbox.

Native Windows producer: Node 22.17.1 / instrumenter 9.5.1 emitted zero-based line
and column ranges, operator names and replacement strings, including `> 0` →
`>= 0`. The adapter converts human report lines to one-based numbering. Runtime
never invokes npm to install missing packages. Pin the instrumenter package to
9.5.1; its Node requirement is >=20.
