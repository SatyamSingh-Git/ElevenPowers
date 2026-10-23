import io
import json

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def debug_from_file(tmp_path, raw):
    path = tmp_path / 'app.ini'
    path.write_text(f'[app]\ndebug = {raw}\n', encoding='utf-8')
    code, out, err = run('dump', '--format', 'json', '--config', str(path))
    assert code == 0, err
    return json.loads(out)['app.debug']


def test_capitalised_booleans_in_the_file(tmp_path):
    for raw, expected in [('True', True), ('TRUE', True), ('Yes', True), ('ON', True),
                          ('False', False), ('NO', False), ('Off', False), ('fAlSe', False)]:
        assert debug_from_file(tmp_path, raw) is expected, raw


def test_capitalised_booleans_in_the_environment():
    assert run('get', 'app.debug', env={'LAYERCFG_APP_DEBUG': 'YES'}) == (0, 'true\n', '')
    assert run('get', 'app.debug', env={'LAYERCFG_APP_DEV_MODE': 'True'}) == (0, 'true\n', '')


def test_lower_case_still_works(tmp_path):
    assert debug_from_file(tmp_path, 'on') is True
    assert debug_from_file(tmp_path, '0') is False
