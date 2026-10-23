"""Command-line front end: `unitconv convert|list|info|batch`."""
import argparse
import json
import sys

from . import _generated
from .batch import convert_file
from .convert import convert
from .dimensions import NAMED, Dimension
from .errors import UnitError
from .formatting import format_number, format_quantity, result_record
from .mixed import format_mixed, split_quantity
from .quantity import parse_quantity
from .registry import REGISTRY
from .rounding import MODES
from .settings import STYLES, Settings, load_settings, overridden


def _parser():
    parser = argparse.ArgumentParser(prog='unitconv', description='Convert between units of measurement.')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s (unit table {_generated.TABLE_VERSION})')
    commands = parser.add_subparsers(dest='command', required=True)

    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--precision', type=int, help='decimal places in results')
    options.add_argument('--rounding', choices=list(MODES))
    options.add_argument('--style', choices=STYLES, help='write units as symbols or names')
    options.add_argument('--settings', metavar='FILE', help='read defaults from a settings file')

    convert_command = commands.add_parser('convert', parents=[options], help='convert one quantity')
    convert_command.add_argument('quantity', help="for example '12.5 km/h'")
    convert_command.add_argument('target', help='unit to convert to')
    convert_command.add_argument('--json', action='store_true', help='print a JSON record')

    list_command = commands.add_parser('list', help='list the known units')
    list_command.add_argument('--dimension', help='only units of this dimension, such as length')

    commands.add_parser('dimensions', help='list the named dimensions')

    info_command = commands.add_parser('info', help='describe one unit')
    info_command.add_argument('unit')

    batch_command = commands.add_parser('batch', parents=[options], help='convert every row of a CSV file')
    batch_command.add_argument('source')
    batch_command.add_argument('destination')
    return parser


def _settings(args):
    settings = load_settings(args.settings) if args.settings else Settings()
    return overridden(settings, precision=args.precision, rounding=args.rounding, style=args.style)


def _convert(args):
    settings = _settings(args)
    quantity = parse_quantity(args.quantity)
    if '+' in args.target:
        if args.json:
            raise UnitError('JSON output needs a single target unit')
        parts = split_quantity(quantity, args.target.split('+'),
                               precision=settings.precision, rounding=settings.rounding)
        print(format_mixed(parts, style=settings.style))
        return 0
    result = convert(quantity, args.target, precision=settings.precision, rounding=settings.rounding)
    if args.json:
        print(json.dumps(result_record(args.quantity, result, style=settings.style)))
    else:
        print(format_quantity(result, style=settings.style))
    return 0


def _list(args):
    dimension = Dimension.named(args.dimension) if args.dimension else None
    for unit in REGISTRY.units(dimension):
        print(f'{unit.symbol:<6} {unit.name:<24} {unit.dimension.name}')
    return 0


def _dimensions(args):
    for name, powers in NAMED.items():
        print(f'{name:<14} {Dimension.of(powers).formula}')
    return 0


def _info(args):
    unit = REGISTRY.lookup(args.unit)
    rows = [('symbol', unit.symbol), ('name', unit.name), ('plural', unit.plural),
            ('dimension', unit.dimension.name), ('factor', format_number(unit.factor)),
            ('offset', format_number(unit.offset))]
    for label, value in rows:
        print(f'{label:<10} {value}')
    return 0


def _batch(args):
    converted, failed = convert_file(args.source, args.destination, _settings(args))
    print(f'converted {converted} rows, {failed} failed')
    return 1 if failed else 0


COMMANDS = {'convert': _convert, 'list': _list, 'dimensions': _dimensions, 'info': _info, 'batch': _batch}


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except UnitError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
