from celery import Celery

from settings import Settings

_redis = Settings.redis
_celery = Settings.celery


def _build_redis_url(db: int) -> str:
    """Redis URL 생성 (보안: password가 있을 때만 인증 정보 추가)"""
    if _redis.password:
        auth = f":{_redis.password}@"
    else:
        auth = ""
    return f"redis://{auth}{_redis.host}:{_redis.port}/{db}"


celery_app = Celery(
    "helper",
    broker=_build_redis_url(_celery.broker_db),
    backend=_build_redis_url(_celery.result_db),
    include=["apps.tasks.reminder"],
)

celery_app.conf.update(
    timezone=_celery.timezone,
    enable_utc=True,
    task_track_started=_celery.task_track_started,
    task_serializer=_celery.task_serializer,
    result_serializer=_celery.result_serializer,
    accept_content=_celery.accept_content,
    result_expires=_celery.result_expires,
    beat_schedule={},
)
