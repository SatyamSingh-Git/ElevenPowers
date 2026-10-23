from tinyroute import App, Client, Response


def test_two_cookies_give_two_set_cookie_headers():
    response = Response('ok')
    response.set_cookie('session', 'abc')
    response.set_cookie('theme', 'dark', max_age=60)
    assert response.header_values('Set-Cookie') == [
        'session=abc; Path=/; HttpOnly', 'theme=dark; Path=/; Max-Age=60; HttpOnly']
    assert response.header('Set-Cookie') == 'session=abc; Path=/; HttpOnly'


def test_delete_cookie_adds_rather_than_replaces():
    response = Response()
    response.set_cookie('session', 'new')
    response.delete_cookie('old')
    assert response.header_values('set-cookie') == [
        'session=new; Path=/; HttpOnly', 'old=; Path=/; Max-Age=0; HttpOnly']


def test_headers_are_a_list_of_pairs_in_order():
    response = Response('x')
    response.add_header('Link', '<a>')
    response.add_header('Link', '<b>')
    assert isinstance(response.headers, list)
    pairs = [(name.lower(), value) for name, value in response.headers]
    assert ('content-type', 'text/plain; charset=utf-8') in pairs
    assert [pair for pair in pairs if pair[0] == 'link'] == [('link', '<a>'), ('link', '<b>')]


def test_cookies_survive_dispatch():
    app = App()

    @app.route('/login')
    def login(request):
        response = Response('welcome')
        response.set_cookie('session', 'abc')
        response.set_cookie('csrf', 'xyz')
        return response

    response = Client(app).get('/login')
    assert response.header_values('Set-Cookie') == ['session=abc; Path=/; HttpOnly', 'csrf=xyz; Path=/; HttpOnly']
