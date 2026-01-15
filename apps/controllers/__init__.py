from . import auth, voice

routers = [
    auth.router,
    voice.router,
]

__all__ = [
    "routers",
]
