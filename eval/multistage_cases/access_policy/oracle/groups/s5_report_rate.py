from warden import Evaluator, Request, User, format_summary, parse_policy, summarize_file, write_log


def test_user_lines_end_with_denial_rate(tmp_path):
    evaluator = Evaluator(parse_policy("role viewer\nallow viewer read open/**\n"))
    alice, bob, cy = User("alice", ("viewer",)), User("bob", ("viewer",)), User("cy", ("viewer",))
    requests = ([Request(alice, "read", "open/a")] * 3 + [Request(alice, "read", "shut/a")]
                + [Request(bob, "read", "shut/b")] * 2
                + [Request(cy, "read", "open/c")] * 2 + [Request(cy, "read", "shut/c")])
    log = tmp_path / "audit.jsonl"
    write_log([evaluator.decide(request) for request in requests], log)
    lines = format_summary(summarize_file(log)).splitlines()
    assert lines[:5] == [
        "9 decisions: 5 allowed, 4 denied",
        "by user:",
        "  alice  3 allowed  1 denied  25%",
        "  bob    0 allowed  2 denied  100%",
        "  cy     2 allowed  1 denied  33%",
    ]
