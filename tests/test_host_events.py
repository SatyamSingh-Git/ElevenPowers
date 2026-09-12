"""Whole hook payloads, read exactly as they arrive.

Separate from `test_payload.py` on purpose. That file's fixtures are tool
*results* lifted from a session transcript, and it builds a hook payload around
each one before reading it. That is a useful test of the reader and it is not a
test of the contract: a payload this project assembles cannot contain a shape
this project did not know about, which is how the documented failure form —
no result object, the message in a top-level `error` — went unread while a
replay score of 174 out of 174 sat in the README.

So these fixtures are payloads, not results, and nothing here wraps or adapts
them. Each records where its shape came from: the documented contract, a
captured session, or invented deliberately to be unrecognisable.
"""

import json
from pathlib import Path

import pytest

from core.payload import read_result

EVENTS = json.loads(
    (Path(__file__).parent / "fixtures" / "host_events.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", EVENTS, ids=[c["name"] for c in EVENTS])
def test_the_payload_is_read_as_it_arrives(case):
    result = read_result(case["payload"])
    expect = case["expect"]
    assert result.readable is expect["readable"]
    assert result.skip == expect["skip"]
    if not result.skip:
        assert result.exit_code == expect["exit_code"]
    if expect["output_has"]:
        assert expect["output_has"] in result.output


def test_every_fixture_says_where_its_shape_came_from():
    """A fixture whose provenance is unrecorded is a fixture somebody invented.

    That is what went wrong the first time: payloads written to match what the
    contract was assumed to be, passing every test while being wrong about it.
    """
    allowed = {"documented contract", "captured session", "invented on purpose"}
    assert {c["source"] for c in EVENTS} <= allowed
    assert {"documented contract", "invented on purpose"} <= {c["source"] for c in EVENTS}
