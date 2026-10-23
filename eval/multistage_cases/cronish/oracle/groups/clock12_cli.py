from cronish.cli import main


def test_describe_command(capsys):
    assert main(["describe", "15 14 * * mon-fri"]) == 0
    assert capsys.readouterr().out == "at 2:15 PM, on Monday, Tuesday, Wednesday, Thursday and Friday\n"


def test_list_command(capsys, tmp_path):
    path = tmp_path / "jobs.txt"
    path.write_text("backup 0 10 * * sun\nlate 59 23 * * *\n", encoding="utf-8")
    assert main(["list", str(path)]) == 0
    assert capsys.readouterr().out == "backup: at 10:00 AM, on Sunday\nlate: at 11:59 PM, every day\n"


def test_run_listings_keep_the_24_hour_clock(capsys):
    assert main(["next", "59 23 * * *", "--now", "2024-03-06T09:00", "-n", "1"]) == 0
    assert capsys.readouterr().out == "2024-03-06 23:59 Wed\n"
