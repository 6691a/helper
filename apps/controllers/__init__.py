from . import auth

routers = [
    auth.router,
]

__all__ = [
    "routers",
]
