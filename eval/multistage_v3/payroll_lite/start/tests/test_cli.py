from payroll.cli import main


def run(data, capsys, *args):
    code = main(["--data", str(data.root), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_employees_add_and_list(data, capsys):
    code, out, _ = run(data, capsys, "employees", "add", "--id", "E001", "--name", "Ana Lima",
                       "--pay-type", "hourly", "--rate", "25", "--bank-account", "11-1111-0000001-00")
    assert code == 0
    _, out, _ = run(data, capsys, "employees", "list")
    assert out.splitlines()[1].split() == ["E001", "Ana", "Lima", "hourly", "yes"]


def test_errors_go_to_stderr_with_status_1(data, capsys):
    code, out, err = run(data, capsys, "payslip", "--period", "2026-W09", "--employee", "E001")
    assert (code, out, err) == (1, "", "error: no pay run for 2026-W09\n")


def test_periods_of_a_year(data, capsys):
    _, out, _ = run(data, capsys, "periods", "--year", "2026")
    lines = out.splitlines()
    assert lines[1].split() == ["2026-W01", "2026-01-05", "2026-01-11", "2026-01-14"]
    assert len(lines) == 1 + 52


def test_tax_on_a_gross_amount(data, capsys):
    _, out, _ = run(data, capsys, "tax", "--gross", "1000")
    assert out == "Tax on 1,000.00 paid weekly: 135.58\n"
