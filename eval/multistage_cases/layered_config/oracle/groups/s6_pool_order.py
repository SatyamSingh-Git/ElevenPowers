import io

import pytest

from layercfg import ValidationError, load
from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def test_minimum_above_maximum_is_rejected(tmp_path):
    path = tmp_path / 'app.ini'
    path.write_text('[pool]\nmin_size = 5\nmax_size = 3\n', encoding='utf-8')
    code, _, err = run('check', '--config', str(path))
    assert code == 1
    assert 'app.ini line 2: pool.min_size: must not exceed pool.max_size' in err


def test_reported_where_the_minimum_was_set():
    with pytest.raises(ValidationError) as caught:
        load(files=[('app.ini', '[pool]\nmax_size = 4\n')], env={'LAYERCFG_POOL_MIN_SIZE': '9'})
    assert str(caught.value) == 'env LAYERCFG_POOL_MIN_SIZE: pool.min_size: must not exceed pool.max_size'


def test_equal_sizes_are_fine():
    config = load(env={'LAYERCFG_POOL_MIN_SIZE': '6', 'LAYERCFG_POOL_MAX_SIZE': '6'})
    assert (config['pool.min_size'], config['pool.max_size']) == (6, 6)
