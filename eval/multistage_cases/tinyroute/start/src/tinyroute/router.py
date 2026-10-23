"""The route table: matching a method and path, and building URLs back from names."""
from urllib.parse import urlencode

from .errors import BuildError, MethodNotAllowed, NotFound, RouteError
from .patterns import Pattern

DEFAULT_METHODS = ('GET',)


class Route:
    def __init__(self, pattern, handler, methods=DEFAULT_METHODS, name=None):
        self.pattern = pattern if isinstance(pattern, Pattern) else Pattern(pattern)
        self.handler = handler
        self.methods = frozenset(method.upper() for method in methods)
        if not self.methods:
            raise RouteError(f'route {self.pattern.text!r} accepts no methods')
        if name is None:
            name = getattr(handler, '__name__', None)
        self.name = None if name == '<lambda>' else name

    def __repr__(self):
        return f'Route({self.pattern.text!r}, methods={sorted(self.methods)}, name={self.name!r})'


class Router:
    def __init__(self):
        self.routes = []
        self.named = {}

    def add(self, pattern, handler, methods=DEFAULT_METHODS, name=None):
        route = Route(pattern, handler, methods, name)
        if route.name is not None:
            if route.name in self.named:
                raise RouteError(f"duplicate route name '{route.name}'")
            self.named[route.name] = route
        self.routes.append(route)
        return route

    def route(self, pattern, methods=DEFAULT_METHODS, name=None):
        """Decorator form of ``add``; the handler is returned unchanged."""
        def register(handler):
            self.add(pattern, handler, methods, name)
            return handler
        return register

    def include(self, prefix, other):
        """Copy every route of ``other`` under ``prefix``, keeping names."""
        if not prefix.startswith('/') or prefix.endswith('/'):
            raise RouteError(f"prefix must start with '/' and not end with one: {prefix!r}")
        for route in other.routes:
            self.add(prefix + route.pattern.text, route.handler, route.methods, route.name)

    def match(self, method, path):
        """The first route that matches ``path`` and accepts ``method``, with its parameters.

        Raises NotFound when no route matches the path and MethodNotAllowed
        when some do but none of them accepts the method.
        """
        method = method.upper()
        allowed = set()
        for route in self.routes:
            params = route.pattern.match(path)
            if params is None:
                continue
            if method in route.methods:
                return route, params
            allowed |= route.methods
        if allowed:
            raise MethodNotAllowed(method, path, allowed)
        raise NotFound(path)

    def url_for(self, name, **values):
        """The path of route ``name``; values that are not parameters go in the query string."""
        route = self.named.get(name)
        if route is None:
            raise BuildError(f"no route named '{name}'")
        path = route.pattern.build(values, name)
        extra = {key: value for key, value in values.items() if key not in route.pattern.names}
        if extra:
            path += '?' + urlencode(extra, doseq=True)
        return path
