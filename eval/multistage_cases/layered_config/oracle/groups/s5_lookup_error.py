import pytest

from layercfg import load

SUGGESTED = "unknown key 'server.prot' (did you mean 'server.port'?)"


def test_get_raises_for_unknown_keys():
    config = load(files=[])
    with pytest.raises(KeyError) as caught:
        config.get('server.prot')
    assert SUGGESTED in str(caught.value)
    with pytest.raises(KeyError) as caught:
        config.get('server.prot', 7)
    assert SUGGESTED in str(caught.value)


def test_indexing_and_source_raise_the_same_way():
    config = load(files=[])
    with pytest.raises(KeyError) as caught:
        config['pool.max_sise']
    assert "unknown key 'pool.max_sise' (did you mean 'pool.max_size'?)" in str(caught.value)
    with pytest.raises(KeyError) as caught:
        config.source('server.prot')
    assert SUGGESTED in str(caught.value)


def test_no_suggestion_when_nothing_is_close():
    config = load(files=[])
    with pytest.raises(KeyError) as caught:
        config.get('zzz')
    assert "unknown key 'zzz'" in str(caught.value)
    assert 'did you mean' not in str(caught.value)


def test_aliases_are_still_found():
    config = load(files=[], env={'LAYERCFG_SERVER_PORT': '9000'})
    assert config.get('server.listen_port') == 9000
    assert config['log.verbosity'] == 'info'
