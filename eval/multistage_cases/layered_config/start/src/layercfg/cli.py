"""Command line: inspect and check the effective configuration.

    python -m layercfg.cli get server.port --config app.ini
    python -m layercfg.cli dump --format sources --config app.ini
    python -m layercfg.cli check --config app.ini
"""
import argparse
import json
import os
from pathlib import Path
import sys

from ._generated import VERSION
from .dump import FORMATS, MASK, RENDERERS, explain, shown
from .envsource import ENV_PREFIX
from .errors import ConfigError
from .loader import load

EXIT_OK, EXIT_INVALID, EXIT_USAGE = 0, 1, 2
_MISSING = object()


class _Usage(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    # argparse would print to the real stderr and exit; main() reports usage errors itself.
    def error(self, message):
        raise _Usage(message)


def _parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--config', metavar='PATH', help='INI file to layer over the defaults')
    common.add_argument('--env-prefix', default=ENV_PREFIX, help='prefix of the variables to read')
    parser = _Parser(prog='layercfg')
    commands = parser.add_subparsers(dest='command', required=True, parser_class=_Parser)
    get = commands.add_parser('get', parents=[common], help='print one value')
    get.add_argument('key')
    get.add_argument('--json', action='store_true', help='print the typed value as JSON')
    get.add_argument('--reveal', action='store_true', help='show secrets')
    dump = commands.add_parser('dump', parents=[common], help='print the effective configuration')
    dump.add_argument('--format', choices=FORMATS, default='ini')
    dump.add_argument('--reveal', action='store_true', help='show secrets')
    commands.add_parser('check', parents=[common], help='load and report every problem')
    explain_ = commands.add_parser('explain', parents=[common], help='describe one option')
    explain_.add_argument('key')
    commands.add_parser('keys', parents=[common], help='list every option')
    commands.add_parser('version', help='print the version')
    return parser


def _load(args, env):
    text = Path(args.config).read_text(encoding='utf-8') if args.config else None
    return load(text, env, file_name=args.config or 'config.ini', env_prefix=args.env_prefix)


def _get(args, config, out, err):
    value = config.get(args.key, _MISSING)
    if value is _MISSING:
        print(f"unknown key '{args.key}'", file=err)
        return EXIT_USAGE
    option = config.schema.resolve(args.key)
    if not args.json:
        print(shown(option, value, args.reveal), file=out)
    elif option.secret and value is not None and not args.reveal:
        print(json.dumps(MASK), file=out)
    else:
        print(json.dumps(value), file=out)
    return EXIT_OK


def _dump(args, config, out, err):
    out.write(RENDERERS[args.format](config, args.reveal))
    return EXIT_OK


def _check(args, config, out, err):
    print('ok', file=out)
    return EXIT_OK


def _explain(args, config, out, err):
    option = config.schema.resolve(args.key)
    if option is None:
        print(f"unknown key '{args.key}'", file=err)
        return EXIT_USAGE
    out.write(explain(config, option))
    return EXIT_OK


def _keys(args, config, out, err):
    for option in config.schema:
        print(f'{option.key}  ({option.type})  {option.help}'.rstrip(), file=out)
    return EXIT_OK


HANDLERS = {'get': _get, 'dump': _dump, 'check': _check, 'explain': _explain, 'keys': _keys}


def main(argv=None, env=None, stdout=None, stderr=None):
    """Run one command. `env` is the environment to layer; nothing is read from os.environ."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        args = _parser().parse_args(argv)
    except _Usage as error:
        print(f'layercfg: {error}', file=err)
        return EXIT_USAGE
    if args.command == 'version':
        print(VERSION, file=out)
        return EXIT_OK
    try:
        config = _load(args, env or {})
    except OSError as error:
        print(f'cannot read {args.config}: {error.strerror}', file=err)
        return EXIT_USAGE
    except ConfigError as error:
        print(error, file=err)
        return EXIT_INVALID
    return HANDLERS[args.command](args, config, out, err)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:], dict(os.environ)))
