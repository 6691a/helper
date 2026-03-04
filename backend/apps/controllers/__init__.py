from . import assistant, auth, device, reminder, voice

routers = [
    assistant.router,
    auth.router,
    device.router,
    reminder.router,
    voice.router,
]

__all__ = [
    "routers",
]
