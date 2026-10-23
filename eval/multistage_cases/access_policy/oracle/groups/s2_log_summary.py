from warden import format_summary, summarize_file

LINES = [
    '{"action": "read", "decision": "deny", "reason": "no rule matched; default is deny", "resource": "a/b", "rule": null, "user": "dan"}',
    '{"action": "read", "decision": "allow", "reason": "allowed by rule 1", "resource": "c", "rule": 1, "user": "dan"}',
    '{"action": "write", "decision": "deny", "reason": "denied by rule 2", "resource": "a/b", "rule": 2, "user": "eve"}',
]


def test_summary_of_a_log_using_decision_words(tmp_path):
    log = tmp_path / "audit.jsonl"
    log.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    summary = summarize_file(log)
    assert (summary.total, summary.allowed, summary.denied) == (3, 1, 2)
    assert summary.users == {"dan": (1, 1), "eve": (0, 1)}
    assert dict(summary.denied_resources) == {"a/b": 2}
    assert format_summary(summary).splitlines()[0] == "3 decisions: 1 allowed, 2 denied"
