"""AI 처리 로그 데코레이터"""

import inspect
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from apps.types.ai_log import AILogStep


def ai_log[**P, R](
    step: AILogStep,
    input_param: str = "text",
    user_id_param: str = "user_id",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    AI 처리 결과를 자동으로 로깅하는 데코레이터.

    Repository는 DI 컨테이너에서 자동 주입됩니다.

    Args:
        step: 처리 단계 (AILogStep Enum)
        input_param: 입력 텍스트 파라미터명 (기본: "text")
        user_id_param: 사용자 ID 파라미터명 (기본: "user_id")

    사용 예:
        from apps.types.ai_log import AILogStep

        class AssistantService:
            @ai_log(step=AILogStep.INTENT_CLASSIFICATION)
            async def _classify_intent(self, text: str, user_id: int) -> IntentClassification:
                ...

            @ai_log(step=AILogStep.TEXT_PARSING)
            async def _parse_text(self, text: str, user_id: int) -> ParsedMemory:
                ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        @wraps(func)
        @inject
        async def wrapper(  # type: ignore[valid-type]
            *args: P.args,
            ai_log_repository: Any = Provide["ai_log_repository"],
            **kwargs: P.kwargs,
        ) -> R:
            # 파라미터 바인딩
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            # self 추출 (메서드인 경우)
            self_obj = arguments.get("self")

            # 입력 텍스트 및 user_id 추출
            input_text = arguments.get(input_param)
            user_id = arguments.get(user_id_param)

            # 모델명 추출
            model_name = _get_model_name(self_obj)

            # 실행 및 시간 측정
            start_time = time.monotonic()
            result = await func(*args, **kwargs)  # type: ignore[misc]
            processing_time_ms = int((time.monotonic() - start_time) * 1000)

            # 결과를 dict로 변환
            output_data = _to_dict(result)

            # 로그 저장
            if ai_log_repository and input_text:
                try:
                    await ai_log_repository.create_log(
                        step=step.value,
                        input_text=str(input_text),
                        output_data=output_data,
                        user_id=user_id if isinstance(user_id, int) else None,
                        model_name=model_name,
                        processing_time_ms=processing_time_ms,
                    )
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).warning(f"Failed to save AI log: {e}")

            return result  # type: ignore[no-any-return]

        return wrapper  # type: ignore[return-value]

    return decorator


def _get_model_name(self_obj: Any) -> str | None:
    """객체에서 모델명을 추출합니다."""
    if self_obj is None:
        return None

    config = getattr(self_obj, "config", None)
    if config:
        return getattr(config, "model", None)

    return None


def _to_dict(result: Any) -> dict[str, Any]:
    """결과를 dict로 변환합니다."""
    if result is None:
        return {}

    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")

    if isinstance(result, dict):
        return result

    return {"result": str(result)}
