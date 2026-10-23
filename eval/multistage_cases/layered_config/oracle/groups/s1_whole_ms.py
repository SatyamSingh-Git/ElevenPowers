import io

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def check(tmp_path, text):
    path = tmp_path / 'app.ini'
    path.write_text(text, encoding='utf-8')
    return run('check', '--config', str(path))


def test_sub_millisecond_durations_are_rejected(tmp_path):
    for raw in ['0.5ms', '1.0005s', '1.5ms', '0.0001']:
        code, _, err = check(tmp_path, f'[server]\nport = 9000\n[pool]\nidle_timeout = {raw}\n')
        assert code == 1, raw
        assert 'app.ini line 4: pool.idle_timeout: duration must be a whole number of milliseconds' in err, raw


def test_whole_millisecond_durations_are_accepted(tmp_path):
    for raw in ['1.001s', '1500ms', '2.5']:
        assert check(tmp_path, f'[server]\ntimeout = {raw}\n')[:2] == (0, 'ok\n'), raw


def test_every_problem_is_still_reported(tmp_path):
    code, _, err = check(tmp_path, '[server]\ntimeout = 2.0001s\n[pool]\nidle_timeout = 0.5ms\n')
    assert code == 1
    assert 'server.timeout: duration must be a whole number of milliseconds' in err
    assert 'app.ini line 4: pool.idle_timeout: duration must be a whole number of milliseconds' in err
