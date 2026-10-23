"""tinyroute: URL routing for a tiny web framework, with no network attached."""
from .app import App
from .client import Client, ClientError, TooManyRedirects
from .converters import register as register_converter
from .errors import (BadRequest, BuildError, HTTPError, InternalError, MethodNotAllowed,
                     NotFound, RouteError)
from .http import Request, Response, json_response, redirect
from .pagination import paginate
from .router import Route, Router

__version__ = '0.4.0'

__all__ = [
    'App', 'BadRequest', 'BuildError', 'Client', 'ClientError', 'HTTPError', 'InternalError',
    'MethodNotAllowed', 'NotFound', 'Request', 'Response', 'Route', 'RouteError', 'Router',
    'TooManyRedirects', 'json_response', 'paginate', 'redirect', 'register_converter',
]
