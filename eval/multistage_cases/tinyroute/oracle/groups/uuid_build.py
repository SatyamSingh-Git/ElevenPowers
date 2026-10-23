import uuid

import pytest

from tinyroute import App, BuildError

TEXT = '12345678-90ab-cdef-1234-567890abcdef'


def make_app():
    app = App()
    app.add_route('/things/<uuid:id>/parts/<int:n>', lambda request, id, n: 'ok', name='part')
    return app


def test_build_from_a_uuid():
    assert make_app().url_for('part', id=uuid.UUID(TEXT), n=2) == f'/things/{TEXT}/parts/2'


def test_build_from_other_string_forms_is_canonical():
    app = make_app()
    for text in (TEXT.upper(), TEXT.replace('-', ''), '{' + TEXT + '}'):
        assert app.url_for('part', id=text, n=1) == f'/things/{TEXT}/parts/1'


def test_build_refuses_what_is_not_a_uuid():
    with pytest.raises(BuildError):
        make_app().url_for('part', id='not-a-uuid', n=1)
