"""tabreport FILE --group-by region --measure sum:amount"""
import argparse
import dataclasses
from pathlib import Path
import sys

from ._generated import VERSION
from .aggregate import parse_measure
from .dialect import named, unescape
from .errors import ReportError
from .filters import keep, parse_filter
from .profile import render_profile
from .reader import read_csv
from .report import build_report, render_report
from .table import FORMATS


def _parser():
    parser = argparse.ArgumentParser(prog="tabreport", description="Summarise a CSV export as a grouped table.")
    parser.add_argument("file", help="CSV file to read")
    parser.add_argument("-g", "--group-by", default="", help="comma-separated columns to group by")
    parser.add_argument("-m", "--measure", action="append",
                        help="func:column, repeatable; sum, count, mean, min or max (default: count)")
    parser.add_argument("-w", "--where", action="append", default=[],
                        help="keep rows matching column=value, column>number and so on; repeatable")
    parser.add_argument("--currency", default="USD", help="ISO code for money columns, or none")
    parser.add_argument("-f", "--format", default="plain", choices=FORMATS)
    parser.add_argument("--dialect", default="comma", help="comma, semicolon, tab or pipe")
    parser.add_argument("--delimiter", help="override the dialect's delimiter; \\t for tab")
    parser.add_argument("--quotechar", help="override the dialect's quote character")
    parser.add_argument("--encoding", help="override the dialect's encoding")
    parser.add_argument("--sort", help="column to order groups by; prefix - for descending")
    parser.add_argument("--no-totals", action="store_true", help="leave out the TOTAL row")
    parser.add_argument("--profile", action="store_true", help="describe the columns instead of reporting")
    parser.add_argument("-o", "--output", help="write the report here instead of standard output")
    parser.add_argument("--version", action="version", version=f"tabreport {VERSION}")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    by = [name.strip() for name in args.group_by.split(",") if name.strip()]
    currency = None if args.currency.lower() == "none" else args.currency
    try:
        measures = [parse_measure(spec) for spec in args.measure or ["count"]]
        filters = [parse_filter(text) for text in args.where]
        required = by + [m.column for m in measures if m.column] + [f.column for f in filters]
        rows = read_csv(args.file, _dialect(args), required=required)
        if filters:
            rows = keep(rows, filters)
        if args.profile:
            text = render_profile(rows, args.format)
        else:
            report = build_report(rows, by, measures, currency=currency,
                                  totals=not args.no_totals, sort=args.sort)
            text = render_report(report, args.format)
    except ReportError as error:
        return _fail(str(error))
    except OSError as error:
        return _fail(f"cannot read {args.file}: {error.strerror}")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


def _dialect(args):
    changes = {}
    if args.delimiter is not None:
        changes["delimiter"] = unescape(args.delimiter)
    if args.quotechar is not None:
        changes["quotechar"] = args.quotechar
    if args.encoding is not None:
        changes["encoding"] = args.encoding
    return dataclasses.replace(named(args.dialect), **changes)


def _fail(message):
    print(f"tabreport: error: {message}", file=sys.stderr)
    return 2
