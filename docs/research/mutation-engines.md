# Mutation engine provenance

Cosmic Ray 8.7.0 (MIT), https://github.com/sixty-north/cosmic-ray, supplies Python
operators, AST traversal and source mutation. Enumeration follows its
`commands/init.py`; the optional child imports its installed library. ElevenPowers
adds changed-file selection, isolated copies, hard attempt/time caps, contained
test execution, exact-input reuse and qualified human reports. Argument-requiring
operators are omitted. Missing/unsupported versions are explicitly unavailable.

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
