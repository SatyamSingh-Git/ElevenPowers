import io

import pytest

from layercfg import ValidationError, load
from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def test_message_lists_the_accepted_words(tmp_path):
    path = tmp_path / 'app.ini'
    path.write_text('[app]\ndebug = maybe\n', encoding='utf-8')
    code, _, err = run('check', '--config', str(path))
    assert code == 1
    assert "app.ini line 2: app.debug: expected bool (true/false, yes/no, on/off, 1/0), got 'maybe'" in err


def test_message_keeps_the_value_as_written():
    with pytest.raises(ValidationError) as caught:
        load(files=[], env={'LAYERCFG_APP_DEBUG': 'Perhaps'})
    assert str(caught.value) == (
        "env LAYERCFG_APP_DEBUG: app.debug: expected bool (true/false, yes/no, on/off, 1/0), got 'Perhaps'")
