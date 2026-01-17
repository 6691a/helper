from . import assistant, auth, voice

routers = [
    assistant.router,
    auth.router,
    voice.router,
]

__all__ = [
    "routers",
]
