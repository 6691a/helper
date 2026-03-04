import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from apps.i18n import _
from apps.models.memory import Memory
from apps.models.reminder import Reminder
from apps.repositories.memory import MemoryRepository
from apps.repositories.reminder import ReminderRepository
from apps.schemas.assistant import (
    AssistantQueryResponse,
    AssistantResponse,
    AssistantSaveResponse,
)
from apps.schemas.memory import MemoryResponse, MemorySearchResult
from apps.schemas.reminder import ReminderResponse
from apps.types.ai_log import AILogStep
from apps.types.assistant import (
    AssistantConfig,
    IntentClassification,
    IntentType,
    ParsedMemory,
    ReminderInfo,
)
from apps.utils.log import ai_log
from apps.utils.reminder_calculator import ReminderCalculator

logger = logging.getLogger(__name__)


class AssistantService:
    """AI Assistant 서비스 (LangChain + Gemini)"""

    INTENT_SYSTEM_PROMPT = """당신은 사용자의 입력을 분류하는 AI입니다.
사용자의 입력이 다음 중 어떤 의도인지 판단하세요:

1. "save" - 나중에 유용할 수 있는 정보를 포함한 경우:
   - 명시적 요청: "~기억해", "~저장해", "~에 뒀어"
   - 장소/위치 정보: "~병원은 ~역에서", "~가게는 ~에 있어"
   - 물건 보관: "~을 ~에 넣었어", "~은 ~에 있어"
   - 일정/약속: "~일에 ~예정", "~시에 만나기로"
   - 연락처/인물: "~전화번호는", "~이메일은"
   - 팁/노하우: "~하려면 ~해", "~방법은"
   - 기타 기억해둘 만한 정보

2. "query" - 기억한 정보를 물어보는 질문:
   - "~어디 있어?", "~어디야?"
   - "~어떻게 가?", "~어떻게 해?"
   - "~뭐였지?", "~알려줘"
   - 의문사(어디, 뭐, 어떻게, 언제, 누구)가 포함된 질문

3. "unknown" - 단순 인사, 잡담, 또는 저장/질문과 무관한 경우

중요: 유용한 정보가 포함되어 있으면 "save"로 분류하세요.
의문문이나 질문 형식이면 "query"로 분류하세요."""

    PARSE_SYSTEM_PROMPT = """당신은 사용자의 입력에서 정보를 추출하는 AI입니다.
입력된 텍스트에서 핵심 정보를 추출하세요.

type 설명:
- item: 물건 위치/보관 정보 (예: "안경 서랍에 뒀어")
- place: 장소/가는 방법 정보 (예: "자생한방병원은 서대문역 6번 출구")
- schedule: 일정/약속 정보 (예: "내일 3시에 치과")
- person: 인물 정보 (예: "김과장 전화번호 010-1234-5678")
- memo: 기타 메모 (예: "비밀번호 1234")

metadata 예시:
- item: {"location": "위치", "quantity": 수량}
- place: {"place": "장소명", "method": "가는 방법", "purpose": "목적"}
- schedule: {"datetime": "일시", "place": "장소", "with_whom": "누구와"}
- person: {"name": "이름", "phone": "전화번호", "relation": "관계"}
- memo: {"category": "분류"}

reminder 추출:
다음 중 하나라도 해당하면 reminder를 추출하세요.
1. 명시적 요청: "알려줘", "리마인드", "잊지 않게" 등
2. 날짜/시간 + 할 일: "내일 아침에 고구마 먹기", "3시에 약 먹기", "다음 주 월요일 회의" 등
   → 특정 시점에 할 행동이 언급되면 자동으로 알림을 설정하세요.

frequency 값:
- once: 1회성 (특정 날짜, 예: "1월 25일에 알려줘", "내일 아침에")
- daily: 매일 (예: "매일 아침 알려줘")
- weekly: 매주 (예: "매주 월요일 알려줘")
- monthly: 매월 (예: "매달 1일에 알려줘")

weekday 값 (frequency=weekly일 때):
- monday, tuesday, wednesday, thursday, friday, saturday, sunday

아침/저녁 시간 기준:
- "아침" → 08:00
- "점심" → 12:00
- "저녁" → 19:00
- "밤" → 21:00
- 시간 언급 없으면 → 09:00

예시:
- "내일 아침에 고구마 먹기" → frequency: once, specific_date: "YYYY-MM-DD"(내일), time: "08:00"
- "3시에 약 먹기" → frequency: once, specific_date: "YYYY-MM-DD"(오늘), time: "15:00"
- "매주 월요일 알려줘" → frequency: weekly, weekdays: ["monday"]
- "매주 화요일 11시에 알려줘" → frequency: weekly, weekdays: ["tuesday"], time: "11:00"
- "매달 15일에 알려줘" → frequency: monthly, day_of_month: 15
- "매달 15일 오전 9시에 알려줘" → frequency: monthly, day_of_month: 15, time: "09:00"
- "2025-02-14에 알려줘" → frequency: once, specific_date: "2025-02-14"
- "매일 오전 9시에 알려줘" → frequency: daily, time: "09:00"
- "다음 주 금요일 3시에" → frequency: once, specific_date: "YYYY-MM-DD", time: "15:00"
- "매주 월화목에 알려줘" → frequency: weekly, weekdays: ["monday", "tuesday", "thursday"]
- "매주 월요일 3시, 화목 17시에 알려줘" → 시간이 여러 개이면 가장 먼저 언급된 시간 하나만 사용:
  time: "15:00", weekdays: ["monday", "tuesday", "thursday"]

중요: 여러 요일은 weekdays 배열에 모두 담으세요. 하나의 reminder로 여러 요일을 지원합니다.
시간은 단일 값만 저장합니다. 여러 시간이 언급되면 첫 번째 시간을 사용하세요.
날짜/시간 언급이 전혀 없으면 reminder는 null로 두세요."""

    ANSWER_SYSTEM_PROMPT = """당신은 친절한 AI 비서입니다.
사용자의 질문에 대해 검색된 관련 정보를 바탕으로 자연스럽게 답변하세요.

검색된 정보가 없거나 관련이 없으면 "죄송합니다, 관련 정보를 찾지 못했습니다."라고 답변하세요.
답변은 간결하고 친근하게 해주세요."""

    def __init__(
        self,
        config: AssistantConfig,
        memory_repository: MemoryRepository,
        reminder_repository: ReminderRepository,
    ):
        self.config = config
        self.memory_repository = memory_repository
        self.reminder_repository = reminder_repository
        self._llm: ChatGoogleGenerativeAI | None = None
        self._embeddings: GoogleGenerativeAIEmbeddings | None = None

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        """LLM 지연 로딩"""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self.config.model,
                google_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
        return self._llm

    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Embeddings 지연 로딩"""
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=f"models/{self.config.embedding_model}",
                api_key=SecretStr(self.config.api_key),
            )
        return self._embeddings

    async def process(self, text: str, user_id: int, timezone: str = "Asia/Seoul") -> AssistantResponse:
        """
        사용자 입력을 처리합니다.

        1. 의도 분류 (save/query/unknown)
        2. save면 파싱 후 저장
        3. query면 벡터 검색 후 답변 생성
        """
        intent_result = await self._classify_intent(text, user_id)

        if intent_result.intent == IntentType.SAVE:
            save_result = await self._handle_save(text, user_id, timezone)
            return AssistantResponse(
                intent=IntentType.SAVE,
                save_result=save_result,
            )
        elif intent_result.intent == IntentType.QUERY:
            query_result = await self._handle_query(text, user_id)
            return AssistantResponse(
                intent=IntentType.QUERY,
                query_result=query_result,
            )
        else:
            return AssistantResponse(
                intent=IntentType.UNKNOWN,
                error_message=_(
                    "Sorry, I didn't understand your request. Please remember information or ask a question."
                ),
            )

    @ai_log(step=AILogStep.INTENT_CLASSIFICATION)
    async def _classify_intent(self, text: str, user_id: int) -> IntentClassification:
        """의도를 분류합니다 (with_structured_output 사용)."""
        structured_llm = self.llm.with_structured_output(IntentClassification)

        messages = [
            SystemMessage(content=self.INTENT_SYSTEM_PROMPT),
            HumanMessage(content=text),
        ]

        try:
            result = await structured_llm.ainvoke(messages)
            if isinstance(result, IntentClassification):
                return result
        except ValueError as e:
            logger.warning(f"Intent classification parsing failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during intent classification: {e}", exc_info=True)

        return IntentClassification(intent=IntentType.UNKNOWN, reason=_("Classification failed"))

    async def _handle_save(self, text: str, user_id: int, timezone: str = "Asia/Seoul") -> AssistantSaveResponse:
        """정보를 파싱하고 저장합니다."""
        parsed = await self._parse_text(text, user_id, timezone)
        embedding = await self.embeddings.aembed_query(text)
        saved_memory = await self._save_memory(parsed, text, embedding, user_id)

        memory_id = saved_memory.id
        if memory_id is None:
            raise ValueError("Memory ID should not be None after creation")

        saved_reminder = await self._save_reminder(parsed.reminder, memory_id, user_id, timezone)
        message = self._build_save_message(parsed)

        return AssistantSaveResponse(
            message=message,
            memory=MemoryResponse.model_validate(saved_memory),
            reminder=self._to_reminder_response(saved_reminder),
        )

    async def _save_memory(
        self,
        parsed: ParsedMemory,
        original_text: str,
        embedding: list[float],
        user_id: int,
    ) -> Memory:
        """Memory를 저장합니다."""
        memory = Memory(
            type=parsed.type,
            keywords=parsed.keywords,
            content=parsed.content,
            metadata_=parsed.metadata,
            original_text=original_text,
            embedding=embedding,
            user_id=user_id,
        )
        return await self.memory_repository.create(memory)

    def _to_reminder_response(self, reminder: Reminder | None) -> ReminderResponse | None:
        """Reminder를 ReminderResponse로 변환합니다."""
        if reminder is None:
            return None
        return ReminderResponse.model_validate(reminder)

    async def _save_reminder(
        self,
        reminder_info: ReminderInfo | None,
        memory_id: int,
        user_id: int,
        timezone: str = "Asia/Seoul",
    ) -> Reminder | None:
        """Reminder를 저장합니다."""
        if reminder_info is None:
            return None

        reminder = Reminder(
            memory_id=memory_id,
            frequency=reminder_info.frequency,
            weekdays=reminder_info.weekdays,
            day_of_month=reminder_info.day_of_month,
            specific_date=reminder_info.specific_date,
            time=reminder_info.time,
            next_run_at=ReminderCalculator.calculate_next_run(
                frequency=reminder_info.frequency,
                time=reminder_info.time,
                weekdays=reminder_info.weekdays,
                day_of_month=reminder_info.day_of_month,
                specific_date=reminder_info.specific_date,
                timezone=timezone,
            ),
            user_id=user_id,
        )
        return await self.reminder_repository.create(reminder)

    def _build_save_message(self, parsed: ParsedMemory) -> str:
        """저장 응답 메시지를 생성합니다."""
        message = _("'{}' information has been saved.").format(parsed.type.value)
        if parsed.reminder:
            message += " " + _("Reminder has also been set.")
        return message

    @ai_log(step=AILogStep.TEXT_PARSING)
    async def _parse_text(self, text: str, user_id: int, timezone: str = "Asia/Seoul") -> ParsedMemory:
        """텍스트에서 정보를 추출합니다 (with_structured_output 사용)."""
        structured_llm = self.llm.with_structured_output(ParsedMemory)

        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        current_datetime_str = now.strftime("%Y-%m-%d %H:%M (%A)")
        system_prompt = self.PARSE_SYSTEM_PROMPT + f"\n\n현재 날짜/시간: {current_datetime_str}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=text),
        ]

        try:
            result = await structured_llm.ainvoke(messages)
            if isinstance(result, ParsedMemory):
                return result
        except ValueError as e:
            logger.warning(f"Text parsing failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during text parsing: {e}", exc_info=True)

        # 파싱 실패시 기본값
        from apps.types.assistant import MemoryType

        return ParsedMemory(
            type=MemoryType.MEMO,
            keywords="",
            content=text,
            metadata=None,
        )

    async def _handle_query(self, text: str, user_id: int) -> AssistantQueryResponse:
        """질문에 답변합니다."""
        # 1. 쿼리 임베딩 생성
        embedding = await self.embeddings.aembed_query(text)

        # 2. 벡터 검색
        results = await self.memory_repository.search_by_vector(
            embedding=embedding,
            user_id=user_id,
            limit=self.config.vector_search_limit,
            threshold=self.config.vector_search_threshold,
        )

        # 3. 검색 결과로 답변 생성
        related_memories = [
            MemorySearchResult(
                memory=MemoryResponse.model_validate(memory),
                similarity=similarity,
            )
            for memory, similarity in results
        ]

        # 4. LLM으로 답변 생성
        if results:
            context = "\n".join([f"- {memory.content} (관련도: {similarity:.2f})" for memory, similarity in results])
            answer_prompt = f"""사용자 질문: {text}

관련 정보:
{context}

위 정보를 바탕으로 사용자의 질문에 답변해주세요."""
        else:
            answer_prompt = f"""사용자 질문: {text}

관련 정보가 없습니다. 적절히 답변해주세요."""

        messages = [
            SystemMessage(content=self.ANSWER_SYSTEM_PROMPT),
            HumanMessage(content=answer_prompt),
        ]
        response = await self.llm.ainvoke(messages)
        answer = response.content if isinstance(response.content, str) else str(response.content)

        return AssistantQueryResponse(
            answer=answer,
            related_memories=related_memories,
        )
