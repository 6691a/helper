from . import assistant, auth, reminder, voice

routers = [
    assistant.router,
    auth.router,
    reminder.router,
    voice.router,
]

__all__ = [
    "routers",
]
