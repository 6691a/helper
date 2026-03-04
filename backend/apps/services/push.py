import logging

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


class PushService:
    """FCM 푸시 알림 서비스"""

    def __init__(self, credentials_path: str) -> None:
        cred = credentials.Certificate(credentials_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

    def send(self, token: str, title: str, body: str) -> None:
        """단일 기기에 FCM 푸시 알림을 전송합니다."""
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={"title": title, "body": body},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="helper_channel",
                ),
            ),
            token=token,
        )
        try:
            messaging.send(message)
        except Exception as e:
            logger.error("FCM 단일 전송 실패 token=%s: %s", token, e)

    def send_multicast(self, tokens: list[str], title: str, body: str) -> None:
        """여러 기기에 FCM 푸시 알림을 일괄 전송합니다 (최대 500개)."""
        if not tokens:
            return

        # FCM 멀티캐스트는 한 번에 최대 500개
        chunk_size = 500
        for i in range(0, len(tokens), chunk_size):
            chunk = tokens[i : i + chunk_size]
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={"title": title, "body": body},
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="helper_channel",
                    ),
                ),
                tokens=chunk,
            )
            try:
                response = messaging.send_each_for_multicast(message)
                if response.failure_count > 0:
                    logger.warning(
                        "FCM 멀티캐스트 일부 실패: success=%d, failure=%d",
                        response.success_count,
                        response.failure_count,
                    )
            except Exception as e:
                logger.error("FCM 멀티캐스트 전송 실패: %s", e)
