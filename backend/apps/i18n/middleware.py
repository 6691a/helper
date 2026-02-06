from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.i18n import parse_accept_language, set_locale

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        accept_language = request.headers.get("Accept-Language")
        locale = parse_accept_language(accept_language)
        set_locale(locale)
        response = await call_next(request)
        return response
