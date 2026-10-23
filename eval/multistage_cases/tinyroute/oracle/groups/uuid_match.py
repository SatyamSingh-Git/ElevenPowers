import uuid

from tinyroute import App, Client

TEXT = '12345678-90ab-cdef-1234-567890abcdef'


def make_app():
    app = App()

    @app.route('/things/<uuid:id>')
    def thing(request, id):
        return {'type': type(id).__name__, 'value': str(id), 'same': id == uuid.UUID(TEXT)}

    return app


def test_canonical_uuid_matches_and_is_converted():
    response = Client(make_app()).get('/things/' + TEXT)
    assert response.json() == {'type': 'UUID', 'value': TEXT, 'same': True}


def test_other_forms_do_not_match():
    client = Client(make_app())
    for text in (TEXT.upper(), TEXT.replace('-', ''), TEXT[:-1], TEXT + '0', 'not-a-uuid'):
        assert client.get('/things/' + text).status == 404, text
