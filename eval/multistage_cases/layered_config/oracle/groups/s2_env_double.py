import io

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def test_double_underscore_is_an_unknown_variable():
    code, _, err = run('check', env={'LAYERCFG_SERVER__PORT': '9001'})
    assert code == 1
    assert 'env LAYERCFG_SERVER__PORT: unknown variable' in err


def test_double_underscore_is_reported_with_valid_variables():
    env = {'LAYERCFG_POOL__MAX_SIZE': '7', 'LAYERCFG_POOL_MIN_SIZE': '2', 'LAYERCFG_LOG__VERBOSITY': 'debug'}
    code, _, err = run('check', env=env)
    assert code == 1
    assert 'env LAYERCFG_POOL__MAX_SIZE: unknown variable' in err
    assert 'env LAYERCFG_LOG__VERBOSITY: unknown variable' in err
    assert 'POOL_MIN_SIZE' not in err
