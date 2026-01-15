# 음성 스트리밍 인식 구현 계획

## 현재 상태

### 완료된 작업
- [x] 기본 음성 인식 API (`POST /api/v1/voice/transcribe`)
- [x] Google Cloud Speech-to-Text v2 연동
- [x] 파일 업로드 방식 음성 인식
- [x] `StreamingTranscribeResponse` 스키마 추가

### 미완료 작업
- [ ] VoiceService에 스트리밍 메서드 추가
- [ ] WebSocket 엔드포인트 추가
- [ ] 앱 연동 테스트

---

## 아키텍처

```
┌─────────┐     WebSocket      ┌─────────┐      gRPC       ┌─────────────┐
│   앱    │ ───────────────→   │  서버   │ ─────────────→  │ Google STT  │
│ (클라이언트) │   오디오 청크     │ (FastAPI) │   스트리밍      │   (v1 API)  │
│         │ ←───────────────   │         │ ←─────────────  │             │
└─────────┘   인식 결과 JSON    └─────────┘   인식 결과      └─────────────┘
```

### 왜 이 구조인가?
- Google STT 스트리밍은 **gRPC만 지원** (WebSocket 미지원)
- 앱에서는 WebSocket이 더 사용하기 쉬움
- 서버가 중간에서 프로토콜 변환 역할

---

## 오디오 포맷 요구사항

앱에서 서버로 전송할 오디오 형식:

| 항목 | 값 |
|------|-----|
| 인코딩 | LINEAR16 (PCM) |
| 샘플레이트 | 16000 Hz |
| 채널 | 1 (모노) |
| 청크 크기 | 3200 bytes (100ms) 권장 |

---

## 구현 상세

### 1. VoiceService 스트리밍 메서드 추가

**파일**: `apps/services/voice.py`

```python
from collections.abc import Generator
from queue import Queue

from google.cloud import speech  # v1 API for streaming


class VoiceService:
    # 기존 코드 유지...

    _streaming_client: speech.SpeechClient | None = None

    @property
    def streaming_client(self) -> speech.SpeechClient:
        """Speech v1 클라이언트 (스트리밍용)"""
        if self._streaming_client is None:
            if self.config.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_path
                )
                self._streaming_client = speech.SpeechClient(credentials=credentials)
            else:
                self._streaming_client = speech.SpeechClient()
        return self._streaming_client

    def streaming_transcribe(
        self,
        audio_queue: Queue[bytes | None],
        language: str | None = None,
    ) -> Generator[StreamingTranscribeResponse, None, None]:
        """
        스트리밍 음성 인식을 수행합니다.

        Args:
            audio_queue: 오디오 청크를 받는 큐 (None이면 종료)
            language: 언어 코드

        Yields:
            StreamingTranscribeResponse: 인식 결과 (중간/최종)
        """
        language_code = language or self.config.language

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,  # 중간 결과 활성화
        )

        def request_generator():
            # 첫 번째 요청: 설정만
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)

            # 이후 요청: 오디오 데이터
            while True:
                chunk = audio_queue.get()
                if chunk is None:  # 종료 신호
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        responses = self.streaming_client.streaming_recognize(requests=request_generator())

        for response in responses:
            for result in response.results:
                if result.alternatives:
                    alt = result.alternatives[0]
                    yield StreamingTranscribeResponse(
                        text=alt.transcript,
                        is_final=result.is_final,
                        confidence=alt.confidence if result.is_final else None,
                    )
```

### 2. WebSocket 엔드포인트 추가

**파일**: `apps/controllers/voice.py`

```python
import asyncio
import json
from queue import Queue
from threading import Thread

from fastapi import WebSocket, WebSocketDisconnect


@router.websocket("/stream")
async def stream_transcribe(
    websocket: WebSocket,
    voice_service: VoiceService = Depends(Provide[Container.voice_service]),
):
    """
    WebSocket 스트리밍 음성 인식

    연결 후:
    1. 클라이언트 → 서버: 오디오 청크 (bytes, LINEAR16, 16kHz, mono)
    2. 서버 → 클라이언트: JSON {"text": "...", "is_final": true/false}
    3. 종료: 클라이언트가 연결 끊기
    """
    await websocket.accept()

    # 오디오 청크를 담을 큐
    audio_queue: Queue[bytes | None] = Queue()

    # 결과를 WebSocket으로 전송하는 함수
    async def send_results():
        try:
            for result in voice_service.streaming_transcribe(audio_queue):
                await websocket.send_json(result.model_dump())
        except Exception as e:
            await websocket.send_json({"error": str(e)})

    # 백그라운드에서 결과 전송 시작
    result_task = asyncio.create_task(send_results())

    try:
        while True:
            # 오디오 청크 수신
            data = await websocket.receive_bytes()
            audio_queue.put(data)
    except WebSocketDisconnect:
        # 연결 종료 시 큐에 종료 신호
        audio_queue.put(None)
        await result_task
```

### 3. 스키마 (이미 완료)

**파일**: `apps/schemas/voice.py`

```python
class StreamingTranscribeResponse(BaseModel):
    """스트리밍 음성 인식 응답 (WebSocket)"""

    text: str = Field(description="인식된 텍스트")
    is_final: bool = Field(description="최종 결과 여부")
    confidence: float | None = Field(default=None, description="인식 신뢰도")
```

---

## 앱 클라이언트 구현 예시

### iOS (Swift)

```swift
import Foundation

class SpeechStreamingClient {
    private var webSocket: URLSessionWebSocketTask?

    func connect() {
        let url = URL(string: "ws://your-server/api/v1/voice/stream")!
        webSocket = URLSession.shared.webSocketTask(with: url)
        webSocket?.resume()
        receiveResults()
    }

    func sendAudioChunk(_ data: Data) {
        webSocket?.send(.data(data)) { error in
            if let error = error {
                print("Send error: \(error)")
            }
        }
    }

    private func receiveResults() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                if case .string(let text) = message {
                    // JSON 파싱 후 처리
                    print("Received: \(text)")
                }
                self?.receiveResults()
            case .failure(let error):
                print("Receive error: \(error)")
            }
        }
    }
}
```

### Android (Kotlin)

```kotlin
import okhttp3.*

class SpeechStreamingClient {
    private val client = OkHttpClient()
    private var webSocket: WebSocket? = null

    fun connect() {
        val request = Request.Builder()
            .url("ws://your-server/api/v1/voice/stream")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                // JSON 파싱 후 처리
                println("Received: $text")
            }
        })
    }

    fun sendAudioChunk(data: ByteArray) {
        webSocket?.send(ByteString.of(*data))
    }
}
```

---

## 제약사항

1. **스트리밍 시간 제한**: Google STT는 최대 5분 (305초) 스트리밍 지원
2. **재연결 로직**: 긴 녹음 시 자동 재연결 필요
3. **오디오 포맷**: LINEAR16, 16kHz, mono 필수

---

## 테스트 방법

### 1. WebSocket 테스트 (websocat 사용)

```bash
# websocat 설치
brew install websocat

# 연결 테스트
websocat ws://localhost:8000/api/v1/voice/stream
```

### 2. Python 테스트 스크립트

```python
import asyncio
import websockets

async def test_streaming():
    uri = "ws://localhost:8000/api/v1/voice/stream"

    async with websockets.connect(uri) as ws:
        # 테스트 오디오 파일 전송
        with open("test_audio.raw", "rb") as f:
            while chunk := f.read(3200):  # 100ms chunks
                await ws.send(chunk)
                await asyncio.sleep(0.1)

                # 결과 수신
                try:
                    result = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    print(result)
                except asyncio.TimeoutError:
                    pass

asyncio.run(test_streaming())
```

---

## 참고 문서

- [Google Cloud Speech-to-Text 스트리밍 인식](https://cloud.google.com/speech-to-text/docs/streaming-recognize)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Google Cloud Speech Python 예제](https://github.com/googleapis/python-speech/tree/main/samples)