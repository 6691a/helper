from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class TimezoneMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.timezone = request.headers.get("X-Timezone", "Asia/Seoul")
        response = await call_next(request)
        return response
