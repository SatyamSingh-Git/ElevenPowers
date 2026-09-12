"""Check that the runtime is actually seeing what its host sends.

    ep-doctor [--cwd DIR] [--host]

`--host` additionally drives the launcher as a process with a payload on its
stdin — success, failure and stop — rather than calling the reader in this one.
Unrecognised flags are refused rather than ignored: this script used to accept
`--host` silently and print six green lines about something else entirely, which
is a passing check that means nothing.

Exits non-zero when something is wrong, so it works in continuous integration
as well as by hand.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.doctor import report  # noqa: E402


KNOWN = {"--cwd", "--host"}


def main(argv: list[str]) -> int:
    unknown = [a for a in argv[1:] if a.startswith("-") and a not in KNOWN]
    if unknown:
        print(f"unknown option(s): {', '.join(unknown)}\n{__doc__}")
        return 2
    where = Path(argv[argv.index("--cwd") + 1] if "--cwd" in argv else ".").resolve()
    body, ok = report(where, host="--host" in argv)
    print(body)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
