from warden import Evaluator, Request, User, format_summary, parse_policy, summarize_file, write_log


def test_ten_most_denied_by_count_then_name(tmp_path):
    evaluator = Evaluator(parse_policy("role viewer\nallow viewer read open/**\n"))
    user = User("u", ("viewer",))
    names = [f"r{i:02d}" for i in range(12, 0, -1)] + ["r12", "r07"]
    log = tmp_path / "audit.jsonl"
    write_log([evaluator.decide(Request(user, "read", f"locked/{name}")) for name in names], log)
    lines = format_summary(summarize_file(log)).splitlines()
    listed = lines[lines.index("most denied:") + 1:]
    assert [line.split() for line in listed] == (
        [["locked/r07", "2"], ["locked/r12", "2"]]
        + [[f"locked/r{i:02d}", "1"] for i in (1, 2, 3, 4, 5, 6, 8, 9)])
