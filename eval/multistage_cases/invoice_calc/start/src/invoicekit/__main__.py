import argparse
import json
import sys

from .export import read_records, to_record, write_records
from .invoice import invoice_from_dict
from .ledger import render_ledger, summarize
from .render import DEFAULT_WIDTH, render_text


def _load(path):
    with open(path, encoding="utf-8") as source:
        return invoice_from_dict(json.load(source))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="invoicekit")
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("render", help="print an invoice read from a JSON file")
    show.add_argument("invoice")
    show.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    export = commands.add_parser("export", help="write invoices to a JSON lines file of records")
    export.add_argument("records")
    export.add_argument("invoices", nargs="+")
    ledger = commands.add_parser("ledger", help="sum a JSON lines file of records by region and currency")
    ledger.add_argument("records")
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            sys.stdout.write(render_text(_load(args.invoice), width=args.width))
        elif args.command == "export":
            write_records(args.records, [to_record(_load(path)) for path in args.invoices])
        else:
            sys.stdout.write(render_ledger(summarize(read_records(args.records))))
    except (OSError, ValueError) as error:
        print(f"invoicekit: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
