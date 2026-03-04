from pydantic import BaseModel, Field


class FirebaseConfig(BaseModel):
    """Firebase 설정"""

    credentials_path: str = Field(
        default="env/firebase-service-account.json",
        description="Firebase 서비스 계정 키 파일 경로",
    )
