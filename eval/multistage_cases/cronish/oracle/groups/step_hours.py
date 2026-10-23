import pytest

from cronish import describe, parse
from cronish.cli import main


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("0 */6 * * *", "every 6 hours, every day"),
        ("0 */2 * * sat", "every 2 hours, on Saturday"),
        ("0 0,12 * * *", "every 12 hours, every day"),
    ],
)
def test_hour_intervals(text, words):
    assert describe(parse(text)) == words


def test_describe_command(capsys):
    assert main(["describe", "0 */4 * * *"]) == 0
    assert capsys.readouterr().out == "every 4 hours, every day\n"
