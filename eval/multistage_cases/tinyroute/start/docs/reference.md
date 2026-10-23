# tinyroute reference

## Path parameter types

A parameter is written `<type:name>`, or `<name>` for the default type. The
pattern column is what the raw, still percent-encoded segment must match.

| Type | Pattern | Python value |
|---|---|---|
| `str` | `[^/]+` | `str`, percent-decoded |
| `int` | `[0-9]+` | `int` |
| `slug` | `[a-z0-9]+(?:-[a-z0-9]+)*` | `str` |
| `path` | `.+` | `str`, slashes included |
| `default_type` | `str` | type used by `<name>` |

## Routing

| Setting | Value | Meaning |
|---|---|---|
| `default_methods` | `GET` | methods of a route added without `methods` |
| `route_name` | `handler.__name__` | name of a route added without `name`; lambdas get none |
| `match_order` | `registration order` | the first route that matches path and method wins |
| `url_for_extra_values` | `query string` | values that are not path parameters are appended as `?key=value` |

## Errors

| Error | Value | Meaning |
|---|---|---|
| `BadRequest` | `400` | status |
| `NotFound` | `404` | status |
| `MethodNotAllowed` | `405` | status; the response carries an `Allow` header |
| `InternalError` | `500` | status of any unexpected exception when `debug` is off |
| `HTTPError.message` | `status reason in lower case` | default message, e.g. `gone` for 410 |
| `error_body` | `{"error": message, "status": status}` | JSON body of every error response |
| `Allow` | `sorted, comma-separated` | methods listed on a 405 |
| `debug` | `False` | when true, unexpected exceptions propagate from `App.handle` |

## Messages

| Message | Text | Raised by |
|---|---|---|
| `not_found` | `no route matches '{path}'` | `NotFound` |
| `method_not_allowed` | `method '{method}' not allowed for '{path}'` | `MethodNotAllowed` |
| `invalid_json` | `invalid JSON body` | `Request.json()`, as `BadRequest` |
| `not_utf8` | `request body is not UTF-8` | `Request.text`, as `BadRequest` |
| `internal_error` | `internal server error` | `InternalError` |
| `unknown_type` | `unknown parameter type '{type}'` | `RouteError` |
| `duplicate_name` | `duplicate route name '{name}'` | `RouteError` |
| `unknown_route` | `no route named '{name}'` | `BuildError` |
| `missing_parameter` | `missing parameter '{name}' for route '{route}'` | `BuildError` |
| `invalid_value` | `invalid value {value!r} for parameter '{name}' of route '{route}'` | `BuildError` |
| `bad_page` | `{name} must be a positive integer` | `paginate()`, as `BadRequest` |
| `redirect_loop` | `more than {max} redirects from '{url}'` | `TooManyRedirects` |
| `ClientError` | `{status} {reason}: {message}` | `ClientError` |

## Requests and responses

| Field | Value | Meaning |
|---|---|---|
| `Request.query` | `dict of str` | one value per name; blank values kept; a repeated name keeps its last value |
| `Request.headers` | `lower-case names` | look up with `request.header(name)` |
| `Response.headers` | `dict` | header name to value |
| `Response.content_type` | `text/plain; charset=utf-8` | default content type |
| `json_response.content_type` | `application/json` | content type of JSON responses |
| `None` | `204` | status when a handler returns None |
| `redirect.status` | `302` | default status of `redirect()` |
| `set_cookie.path` | `/` | default cookie path |
| `set_cookie.http_only` | `True` | cookies are HttpOnly by default |

## Pagination

| Setting | Value | Meaning |
|---|---|---|
| `per_page` | `10` | default page size |
| `max_per_page` | `100` | larger `per_page` values are capped |
| `page_param` | `page` | query name of the page number |
| `per_page_param` | `per_page` | query name of the page size; kept in links when not the default |

## Middleware and client

| Setting | Value | Meaning |
|---|---|---|
| `cors.methods` | `GET, POST, PUT, PATCH, DELETE` | preflight `Access-Control-Allow-Methods` |
| `cors.max_age` | `600` | preflight `Access-Control-Max-Age`, seconds |
| `request_id.header` | `X-Request-Id` | header read and written |
| `request_id.start` | `1` | first generated id |
| `access_log.line` | `{method} {path} {status}` | one line per request |
| `max_redirects` | `5` | redirects the client follows before giving up |
