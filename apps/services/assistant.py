from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from apps.models.memory import Memory
from apps.repositories.memory import MemoryRepository
from apps.schemas.assistant import (
    AssistantQueryResponse,
    AssistantResponse,
    AssistantSaveResponse,
)
from apps.schemas.memory import MemoryResponse, MemorySearchResult
from apps.types.assistant import (
    AssistantConfig,
    IntentClassification,
    IntentType,
    ParsedMemory,
)


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

reminder 추출 (알림 요청이 있을 때만):
"알려줘", "리마인드", "잊지 않게" 등 알림 요청이 있으면 reminder를 추출하세요.

frequency 값:
- once: 1회성 (특정 날짜, 예: "1월 25일에 알려줘")
- daily: 매일 (예: "매일 아침 알려줘")
- weekly: 매주 (예: "매주 월요일 알려줘")
- monthly: 매월 (예: "매달 1일에 알려줘")

weekday 값 (frequency=weekly일 때):
- monday, tuesday, wednesday, thursday, friday, saturday, sunday

예시:
- "매주 월요일 알려줘" → frequency: weekly, weekday: monday
- "매달 15일에 알려줘" → frequency: monthly, day_of_month: 15
- "2025-02-14에 알려줘" → frequency: once, specific_date: "2025-02-14"
- "매일 오전 9시에 알려줘" → frequency: daily, time: "09:00"
- "다음 주 금요일 3시에" → frequency: once, specific_date: "YYYY-MM-DD", time: "15:00"

알림 요청이 없으면 reminder는 null로 두세요."""

    ANSWER_SYSTEM_PROMPT = """당신은 친절한 AI 비서입니다.
사용자의 질문에 대해 검색된 관련 정보를 바탕으로 자연스럽게 답변하세요.

검색된 정보가 없거나 관련이 없으면 "죄송합니다, 관련 정보를 찾지 못했습니다."라고 답변하세요.
답변은 간결하고 친근하게 해주세요."""

    def __init__(
        self,
        config: AssistantConfig,
        memory_repository: MemoryRepository,
    ):
        self.config = config
        self.memory_repository = memory_repository
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

    async def process(self, text: str, user_id: int | None = None) -> AssistantResponse:
        """
        사용자 입력을 처리합니다.

        1. 의도 분류 (save/query/unknown)
        2. save면 파싱 후 저장
        3. query면 벡터 검색 후 답변 생성
        """
        intent_result = await self._classify_intent(text)

        if intent_result.intent == IntentType.SAVE:
            save_result = await self._handle_save(text, user_id)
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
                error_message="죄송합니다, 요청을 이해하지 못했습니다. 정보를 기억하거나 질문해주세요.",
            )

    async def _classify_intent(self, text: str) -> IntentClassification:
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
        except Exception:
            pass

        return IntentClassification(intent=IntentType.UNKNOWN, reason="분류 실패")

    async def _handle_save(
        self, text: str, user_id: int | None
    ) -> AssistantSaveResponse:
        """정보를 파싱하고 저장합니다."""
        # 1. 텍스트 파싱 (with_structured_output 사용)
        parsed = await self._parse_text(text)

        # 2. 임베딩 생성
        embedding = await self.embeddings.aembed_query(text)

        # 3. Memory 저장
        memory = Memory(
            type=parsed.type,
            keywords=parsed.keywords,
            content=parsed.content,
            metadata_=parsed.metadata,
            original_text=text,
            embedding=embedding,
            user_id=user_id,
        )
        saved_memory = await self.memory_repository.create(memory)

        # 4. 응답 메시지 생성
        message = f"'{parsed.type.value}' 정보를 저장했습니다."
        if parsed.reminder:
            message += " 알림도 설정되었습니다."

        return AssistantSaveResponse(
            message=message,
            memory=MemoryResponse.model_validate(saved_memory),
            reminder=parsed.reminder,
        )

    async def _parse_text(self, text: str) -> ParsedMemory:
        """텍스트에서 정보를 추출합니다 (with_structured_output 사용)."""
        structured_llm = self.llm.with_structured_output(ParsedMemory)

        messages = [
            SystemMessage(content=self.PARSE_SYSTEM_PROMPT),
            HumanMessage(content=text),
        ]

        try:
            result = await structured_llm.ainvoke(messages)
            if isinstance(result, ParsedMemory):
                return result
        except Exception:
            pass

        # 파싱 실패시 기본값
        from apps.types.assistant import MemoryType

        return ParsedMemory(
            type=MemoryType.MEMO,
            keywords="",
            content=text,
            metadata=None,
        )

    async def _handle_query(
        self, text: str, user_id: int | None
    ) -> AssistantQueryResponse:
        """질문에 답변합니다."""
        # 1. 쿼리 임베딩 생성
        embedding = await self.embeddings.aembed_query(text)

        # 2. 벡터 검색
        results = await self.memory_repository.search_by_vector(
            embedding=embedding,
            user_id=user_id,
            limit=5,
            threshold=0.3,
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
            context = "\n".join(
                [
                    f"- {memory.content} (관련도: {similarity:.2f})"
                    for memory, similarity in results
                ]
            )
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
        answer = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        return AssistantQueryResponse(
            answer=answer,
            related_memories=related_memories,
        )
