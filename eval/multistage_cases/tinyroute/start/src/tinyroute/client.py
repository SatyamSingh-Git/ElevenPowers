"""An in-process client: calls an ``App`` the way a browser or API consumer would."""
import json

from .http import JSON, Request

MAX_REDIRECTS = 5
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class ClientError(Exception):
    """A 4xx or 5xx response, raised when the caller asked for errors to raise."""

    def __init__(self, response):
        self.response = response
        self.status = response.status
        self.message = error_message(response)
        super().__init__(f'{response.status_line}: {self.message}')


class TooManyRedirects(Exception):
    pass


def error_message(response):
    """The message of an error response: from the JSON error body, else the whole text."""
    if response.content_type == JSON:
        body = response.json()
        if isinstance(body, dict) and 'error' in body:
            return body['error']
    return response.text


class Client:
    def __init__(self, app, headers=None, raise_for_status=False):
        self.app = app
        self.headers = dict(headers or {})
        self.raise_for_status = raise_for_status

    def request(self, method, url, *, body=b'', json_body=None, headers=None,
                follow_redirects=False, raise_for_status=None):
        sent = {**self.headers, **(headers or {})}
        if json_body is not None:
            body = json.dumps(json_body)
            sent.setdefault('Content-Type', JSON)
        response = self.app.handle(Request.from_url(method, url, sent, body))
        hops = 0
        while follow_redirects and response.status in REDIRECT_STATUSES:
            hops += 1
            if hops > MAX_REDIRECTS:
                raise TooManyRedirects(f"more than {MAX_REDIRECTS} redirects from '{url}'")
            # 307 and 308 repeat the request as it was; the others turn it into a GET.
            if response.status in (307, 308):
                again = Request.from_url(method, response.header('Location'), sent, body)
            else:
                again = Request.from_url('GET', response.header('Location'), self.headers)
            response = self.app.handle(again)
        if raise_for_status is None:
            raise_for_status = self.raise_for_status
        if raise_for_status and response.status >= 400:
            raise ClientError(response)
        return response

    def get(self, url, **options):
        return self.request('GET', url, **options)

    def post(self, url, **options):
        return self.request('POST', url, **options)

    def put(self, url, **options):
        return self.request('PUT', url, **options)

    def patch(self, url, **options):
        return self.request('PATCH', url, **options)

    def delete(self, url, **options):
        return self.request('DELETE', url, **options)

    def options(self, url, **options):
        return self.request('OPTIONS', url, **options)
