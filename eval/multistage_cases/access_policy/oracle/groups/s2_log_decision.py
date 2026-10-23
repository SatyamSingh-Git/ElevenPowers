import json

from warden import Evaluator, Request, User, parse_policy, read_log, write_log

POLICY = "role viewer\nallow viewer read reports/**\n"


def decide(roles, action, resource):
    return Evaluator(parse_policy(POLICY)).decide(Request(User("alice", tuple(roles)), action, resource))


def test_records_carry_a_decision_word(tmp_path):
    log = tmp_path / "audit.jsonl"
    write_log([decide(["viewer"], "read", "reports/q1"), decide(["viewer"], "write", "reports/q1")], log)
    raw = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [item["decision"] for item in raw] == ["allow", "deny"]
    for item in raw:
        assert "allowed" not in item
        assert set(item) == {"action", "decision", "reason", "resource", "rule", "user"}
    assert raw[0]["rule"] == 1 and raw[1]["rule"] is None
    assert read_log(log) == raw
