"""Conservative pytest positional scope; stdlib only, never execute a command.

Built-in option forms checked against installed pytest's --help. Unknown plugin
options retain an explicit qualification instead of guessing their arity/scope.
"""
from dataclasses import dataclass
import re
import shlex


VALUES = frozenset('''-W --pythonwarnings -o --override-ini -c --config-file -k -m
--maxfail --pdbcls --capture --lfnf --last-failed-no-failures --durations
--durations-min --verbosity -r --report-chars --tb --show-capture --color
--code-highlight --pastebin --junitxml --junit-xml --junitprefix --junit-prefix
--max-warnings --ignore --ignore-glob --deselect --confcutdir --import-mode
--doctest-report --doctest-glob --rootdir --basetemp -p --log-level --log-format
--log-date-format --log-cli-level --log-cli-format --log-cli-date-format
--log-file --log-file-mode --log-file-level --log-file-format --log-file-date-format
--log-disable --assert'''.split())
FLAGS = frozenset('''-x --exitfirst --strict-config --strict-markers --strict
--fixtures --funcargs --fixtures-per-test --pdb --trace -s --runxfail --lf
--last-failed --ff --failed-first --nf --new-first --cache-show --cache-clear
--sw --stepwise --sw-skip --stepwise-skip --sw-reset --stepwise-reset -v --verbose
--no-header --no-summary --no-fold-skipped --force-short-summary -q --quiet -l
--showlocals --no-showlocals --xfail-tb --full-trace --disable-warnings
--disable-pytest-warnings --collect-only --co --pyargs --noconftest
--keep-duplicates --collect-in-virtualenv --continue-on-collection-errors
--doctest-modules --doctest-ignore-import-errors --doctest-continue-on-failure
-V --version -h --help --debug --trace-config'''.split())
SELECTORS = frozenset(('-k', '-m', '--deselect', '--lf', '--last-failed', '--sw', '--stepwise',
                       '--sw-skip', '--stepwise-skip'))
OPTIONAL_VALUES = frozenset(('--debug', '--cache-show'))


@dataclass(frozen=True)
class Scope:
    identity: str
    narrowed: bool
    issue: str = ''


def inspect(command):
    lexer = shlex.shlex(command, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ''
    lexer.escape = ''  # Quoted Windows paths retain their literal backslashes.
    try:
        words = list(lexer)
    except ValueError:
        return Scope('pytest', False, 'pytest option scope unavailable: malformed quoting') if re.search(r'\bpytest\b', command) else None
    index = next((i for i, word in enumerate(words)
                  if word.replace('\\', '/').rsplit('/', 1)[-1] in ('pytest', 'pytest.exe')), None)
    if index is None:
        return None
    targets, narrowed, issue = [], False, ''
    args = words[index + 1:]
    position, literal = 0, False
    while position < len(args):
        word = args[position]
        position += 1
        if not literal and (word in ('|', '||', '&&', ';') or re.match(r'^\d*[<>]', word)):
            break  # Output shaping is not a pytest positional argument.
        if not literal and word == '--':
            literal = True
            continue
        if literal or not word.startswith('-'):
            targets.append(word.replace('\\', '/'))
            continue
        option, attached, _ = word.partition('=')
        # argparse reads clusters left to right; the first value-taking short
        # option consumes the rest, or the following argument (-qra / -qk one).
        if word.startswith('-') and not word.startswith('--') and len(word) > 2:
            cluster = word[1:]
            for offset, letter in enumerate(cluster):
                short = '-' + letter
                if short in VALUES:
                    option, attached = short, bool(cluster[offset + 1:])
                    break
                if short not in FLAGS:
                    break
            else:
                continue
        narrowed = narrowed or option in SELECTORS
        if option in OPTIONAL_VALUES:
            if not attached and position < len(args) and not args[position].startswith('-'):
                position += 1
        elif option in VALUES:
            if not attached:
                if position == len(args) or args[position].startswith('-'):
                    issue = 'pytest option scope unavailable: missing value for ' + option
                    break
                position += 1
        elif option in FLAGS or (word.startswith('-') and not word.startswith('--') and set(word[1:]) <= set('qvlsx')):
            continue
        else:
            issue = 'pytest option scope unavailable: unsupported option ' + option
            break
    narrowed = narrowed or any('::' in target or target.endswith('.py') for target in targets)
    fallback = 'python pytest' if index and '-m' in words[:index] else 'pytest'
    return Scope(targets[-1] if targets else fallback, narrowed, issue)
