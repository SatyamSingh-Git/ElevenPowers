"""pytest plugin: record what project functions return while each test runs."""
import hashlib
import json
import os
import re
import sys

import pytest

SOURCE = os.path.normcase(os.path.abspath(os.environ['BEHAVIOUR_SOURCE']))
OUT = os.environ['BEHAVIOUR_OUT']
ADDRESS = re.compile(r' at 0x[0-9A-Fa-f]+')
seen = {}


def _digest(value):
    try:
        text = repr(value)
    except Exception as error:  # a broken __repr__ is still behaviour
        text = f'<repr failed: {type(error).__name__}>'
    return hashlib.sha1(ADDRESS.sub('', text).encode('utf-8', 'replace')).hexdigest()[:12]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    calls = {}

    def profile(frame, event, arg):
        if event != 'return':
            return
        path = os.path.normcase(frame.f_code.co_filename)
        if not path.startswith(SOURCE):
            return
        key = os.path.relpath(path, os.path.dirname(SOURCE)).replace('\\', '/') + '::' + frame.f_code.co_qualname
        calls.setdefault(key, []).append(_digest(arg))

    sys.setprofile(profile)
    try:
        yield
    finally:
        sys.setprofile(None)
        seen[item.nodeid] = calls


def pytest_sessionfinish(session):
    with open(OUT, 'w', encoding='utf-8') as handle:
        json.dump(seen, handle)
