import argparse
import sys

from .compaction import compact
from .errors import EventLogError
from .log import Log
from .stats import format_stats, stats


def _show(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.hex()


def _dump(args, out):
    with Log.open(args.directory) as log:
        for record in log.replay(args.from_offset):
            value = '<deleted>' if record.tombstone else _show(record.value)
            print(f'{record.offset}\t{record.timestamp}\t{_show(record.key)}\t{value}', file=out)


def _stats(args, out):
    print(format_stats(stats(args.directory)), file=out)


def _compact(args, out):
    with Log.open(args.directory) as log:
        result = compact(log)
    print(f'rewrote {result.segments_rewritten} and removed {result.segments_removed} segments, '
          f'dropping {result.records_removed} records ({result.bytes_before} -> {result.bytes_after} bytes)',
          file=out)


def main(argv=None, out=sys.stdout, err=sys.stderr):
    parser = argparse.ArgumentParser(prog='eventlog')
    commands = parser.add_subparsers(dest='command', required=True)
    dump = commands.add_parser('dump', help='print records as tab-separated lines')
    dump.add_argument('directory')
    dump.add_argument('--from', dest='from_offset', type=int)
    dump.set_defaults(run=_dump)
    summary = commands.add_parser('stats', help='summarise a log without opening it')
    summary.add_argument('directory')
    summary.set_defaults(run=_stats)
    shrink = commands.add_parser('compact', help='keep only the latest record of each key')
    shrink.add_argument('directory')
    shrink.set_defaults(run=_compact)

    args = parser.parse_args(argv)
    try:
        args.run(args, out)
    except EventLogError as error:
        print(f'eventlog: {error}', file=err)
        return 1
    return 0
