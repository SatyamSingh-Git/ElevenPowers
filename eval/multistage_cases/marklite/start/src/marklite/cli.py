import argparse
import json
from pathlib import Path
import sys

from ._generated import VERSION
from .errors import MarkliteError
from .options import Options
from .render import render, toc


def main(argv=None):
    parser = argparse.ArgumentParser(prog="marklite", description="Render a markdown file to HTML.")
    parser.add_argument("path", help="markdown file to render, or - for standard input")
    parser.add_argument("-o", "--output", help="write the result here instead of standard output")
    parser.add_argument("--toc-level", type=int, default=3,
                        help="deepest heading level the table of contents lists")
    parser.add_argument("--json-toc", action="store_true", help="print the table of contents as JSON")
    parser.add_argument("--no-ids", action="store_true", help="leave id attributes off headings")
    parser.add_argument("--unsafe-links", action="store_true", help="keep link URLs with any scheme")
    parser.add_argument("--hard-breaks", action="store_true", help="turn every line break into <br />")
    parser.add_argument("--version", action="version", version=f"marklite {VERSION}")
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
    except OSError:
        return _fail(f"cannot read {args.path}")
    try:
        options = Options(toc_max_level=args.toc_level, heading_ids=not args.no_ids,
                          safe_links=not args.unsafe_links, hard_breaks=args.hard_breaks)
        if args.json_toc:
            entries = [{"level": entry.level, "title": entry.title, "anchor": entry.anchor}
                       for entry in toc(text, options)]
            output = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
        else:
            output = render(text, options)
    except MarkliteError as error:
        return _fail(str(error))

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8", newline="")
    else:
        sys.stdout.write(output)
    return 0


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 1
