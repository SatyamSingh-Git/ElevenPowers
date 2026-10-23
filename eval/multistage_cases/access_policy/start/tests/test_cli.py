from warden.cli import main

POLICY = "role viewer\nrole guest\nallow viewer read reports/**\n"


def test_check_lint_and_report(tmp_path, capsys):
    policy, log = tmp_path / "p.policy", tmp_path / "audit.jsonl"
    policy.write_text(POLICY, encoding="utf-8")

    assert main(["check", str(policy), "alice", "read", "reports/q1", "--role", "viewer", "--log", str(log)]) == 0
    assert main(["check", str(policy), "bob", "read", "reports/q1", "--log", str(log)]) == 1
    assert capsys.readouterr().out.splitlines()[0] == "ALLOW alice read reports/q1: allowed by rule 1"

    assert main(["lint", str(policy)]) == 1
    assert capsys.readouterr().out == "unused-role: role guest is never used\n"

    assert main(["report", str(log)]) == 0
    assert capsys.readouterr().out.startswith("2 decisions: 1 allowed, 1 denied\n")


def test_errors_exit_2(tmp_path, capsys):
    policy = tmp_path / "p.policy"
    policy.write_text("role viewer\nallow viewer fly x\n", encoding="utf-8")
    assert main(["lint", str(policy)]) == 2
    assert capsys.readouterr().err == "warden: line 2: unknown action: fly\n"
