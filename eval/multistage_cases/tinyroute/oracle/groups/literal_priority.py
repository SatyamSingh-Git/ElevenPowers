from tinyroute import App, Client


def make_app():
    app = App()

    @app.route('/users/<name>', methods=['GET', 'POST'])
    def by_name(request, name):
        return f'user {name}'

    @app.route('/users/me')
    def me(request):
        return 'me'

    @app.route('/teams/<int:team>/members/<name>')
    def member(request, team, name):
        return f'member {team} {name}'

    @app.route('/teams/<int:team>/members/lead')
    def lead(request, team):
        return f'lead {team}'

    return app


def test_fixed_segment_wins_over_an_earlier_parameter():
    client = Client(make_app())
    assert client.get('/users/me').text == 'me'
    assert client.get('/users/ada').text == 'user ada'


def test_fixed_segment_wins_deeper_in_the_path():
    client = Client(make_app())
    assert client.get('/teams/4/members/lead').text == 'lead 4'
    assert client.get('/teams/4/members/bob').text == 'member 4 bob'


def test_method_still_falls_through_to_a_route_that_accepts_it():
    assert Client(make_app()).post('/users/me').text == 'user me'
