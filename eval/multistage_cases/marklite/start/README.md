# marklite

A small markdown subset rendered to HTML, with heading anchors and a table of
contents. Standard library only.

```python
from marklite import Options, render, toc

html = render(open("guide.md").read(), Options(toc_max_level=2))
```

```
marklite guide.md -o guide.html
```

Put `[TOC]` on a line of its own where the table of contents should go.
See `docs/reference.md` for options, limits and messages.
