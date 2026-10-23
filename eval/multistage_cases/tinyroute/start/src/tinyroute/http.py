"""Request and response objects, and the conversions between them and handler results."""
import json
from urllib.parse import parse_qsl, urlsplit

from ._generated import STATUS_REASONS
from .errors import BadRequest

TEXT = 'text/plain; charset=utf-8'
JSON = 'application/json'


def parse_query(text):
    """``a=1&b=&a=2`` -> ``{'a': '2', 'b': ''}``: blank values kept, the last repeat wins."""
    return dict(parse_qsl(text, keep_blank_values=True))


class Request:
    def __init__(self, method, path, query=None, headers=None, body=b''):
        self.method = method.upper()
        self.path = path
        self.query = dict(query or {})
        self.headers = {name.lower(): value for name, value in (headers or {}).items()}
        self.body = body.encode('utf-8') if isinstance(body, str) else bytes(body)
        # Filled in by the application while it dispatches.
        self.app = None
        self.route = None
        self.params = {}

    @classmethod
    def from_url(cls, method, url, headers=None, body=b''):
        parts = urlsplit(url)
        return cls(method, parts.path or '/', parse_query(parts.query), headers, body)

    def header(self, name, default=None):
        return self.headers.get(name.lower(), default)

    @property
    def text(self):
        try:
            return self.body.decode('utf-8')
        except UnicodeDecodeError:
            raise BadRequest('request body is not UTF-8') from None

    def json(self):
        try:
            return json.loads(self.body)
        except ValueError:
            raise BadRequest('invalid JSON body') from None

    def __repr__(self):
        return f'<Request {self.method} {self.path}>'


class Response:
    def __init__(self, body=b'', status=200, headers=None, content_type=TEXT):
        self.body = body.encode('utf-8') if isinstance(body, str) else bytes(body)
        self.status = status
        self.headers = {'Content-Type': content_type}
        self.headers.update(headers or {})

    @property
    def reason(self):
        return STATUS_REASONS.get(self.status, 'Unknown')

    @property
    def status_line(self):
        return f'{self.status} {self.reason}'

    @property
    def content_type(self):
        return self.header('Content-Type')

    @property
    def text(self):
        return self.body.decode('utf-8')

    def json(self):
        return json.loads(self.body)

    def header(self, name, default=None):
        """A header's value, whatever the case of ``name``."""
        name = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name:
                return value
        return default

    def set_cookie(self, name, value, max_age=None, path='/', http_only=True):
        attributes = [f'{name}={value}', f'Path={path}']
        if max_age is not None:
            attributes.append(f'Max-Age={max_age}')
        if http_only:
            attributes.append('HttpOnly')
        self.headers['Set-Cookie'] = '; '.join(attributes)

    def delete_cookie(self, name, path='/'):
        self.set_cookie(name, '', max_age=0, path=path)

    def __repr__(self):
        return f'<Response {self.status_line}>'


def json_response(data, status=200, headers=None):
    return Response(json.dumps(data), status, headers, JSON)


def redirect(location, status=302):
    return Response(status=status, headers={'Location': location})


def error_response(error):
    """The response for an ``HTTPError``: its status, its headers and a JSON body."""
    return json_response({'error': error.message, 'status': error.status}, error.status, error.headers)


def to_response(value):
    """Turn what a handler returned into a ``Response``."""
    if isinstance(value, Response):
        return value
    if value is None:
        return Response(status=204)
    if isinstance(value, (dict, list)):
        return json_response(value)
    if isinstance(value, (str, bytes)):
        return Response(value)
    raise TypeError(f'a handler returned {type(value).__name__}, which is not a response')
