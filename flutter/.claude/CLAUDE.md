# CLAUDE.md — Flutter

Flutter 프로젝트 개발 가이드라인 (Flutter 3.41.2, Dart 3.11.0)

## Project Overview

Helper Flutter — AI 음성 비서 + 메모리/리마인더 관리 네이티브 앱

## Development Commands

```bash
cd flutter

just pub           # flutter pub get
just gen           # dart run build_runner build --delete-conflicting-outputs
just run           # flutter run
just ios           # flutter run -d "iPhone" 시뮬레이터
just android       # flutter run -d android
just build-ios     # flutter build ios --debug --no-codesign
just build-apk     # flutter build apk --debug
just analyze       # dart analyze
just test          # flutter test
just clean         # flutter clean && flutter pub get
just logs          # flutter logs (연결된 기기)
```

## Tech Stack

| 분류 | 패키지 | 용도 |
|------|--------|------|
| 네비게이션 | go_router ^14 | 선언형 라우팅 + auth guard |
| 상태 관리 | flutter_riverpod ^2.6, riverpod_annotation ^2.6 | Provider 패턴 |
| HTTP | dio ^5.8 | REST API + 인터셉터 |
| WebSocket | web_socket_channel ^3 | 음성 스트리밍 |
| OAuth | flutter_web_auth_2 ^4 | Google OAuth 인앱 브라우저 |
| 로컬 저장소 | flutter_secure_storage ^9.2 | 토큰 저장 |
| 설정 | shared_preferences ^2.3 | 다크모드 등 |
| 오디오 | record ^5.2 | PCM 16-bit 스트리밍 |
| 권한 | permission_handler ^11.3 | 마이크 권한 |
| 이미지 | image_picker ^1.1, cached_network_image ^3.4 | 프로필 이미지 |
| 유틸 | intl ^0.19 | 날짜 포맷 |
| 코드 생성 | build_runner ^2.4, riverpod_generator ^2.6 | Riverpod 자동 생성 |

## Architecture

```
flutter/lib/
├── main.dart
├── core/
│   ├── constants.dart               # API_BASE, WS_BASE 등
│   ├── router.dart                  # GoRouter (auth guard 포함)
│   ├── api/
│   │   ├── api_client.dart          # Dio + interceptors
│   │   ├── auth_api.dart
│   │   ├── memory_api.dart
│   │   ├── assistant_api.dart
│   │   └── reminder_api.dart
│   ├── models/
│   │   ├── user.dart
│   │   ├── memory.dart
│   │   ├── reminder.dart
│   │   └── conversation.dart
│   └── providers/
│       ├── auth_provider.dart       # flutter_secure_storage 기반
│       └── theme_provider.dart      # shared_preferences 기반
├── features/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   └── signup_screen.dart
│   ├── home/
│   │   ├── home_screen.dart
│   │   └── memory_card.dart
│   ├── calendar/
│   │   ├── calendar_screen.dart
│   │   └── calendar_grid.dart       # 커스텀 애니메이션 캘린더
│   ├── reminder/
│   │   ├── reminder_screen.dart
│   │   └── reminder_card.dart
│   ├── profile/
│   │   └── profile_screen.dart
│   ├── settings/
│   │   └── settings_screen.dart
│   ├── memory_detail/
│   │   └── memory_detail_screen.dart
│   └── voice/
│       ├── voice_sheet.dart         # 음성 녹음 바텀 시트 UI
│       └── voice_service.dart       # AudioRecorder + WebSocket
└── shared/
    ├── widgets/
    │   ├── type_badge.dart
    │   └── screen_header.dart
    └── theme/
        ├── app_theme.dart           # ThemeData light()/dark()
        └── app_colors.dart          # 색상 상수
```

계층 구조: Screen → Provider (Riverpod) → API Service → Dio → Backend

## 핵심 패턴

### Riverpod: StateNotifierProvider

```dart
// auth_provider.dart
@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() => const AuthState.loading();

  Future<void> loginWithGoogle() async { ... }
  Future<void> logout() async { ... }
}

// theme_provider.dart
@riverpod
class ThemeNotifier extends _$ThemeNotifier {
  @override
  ThemeMode build() => ThemeMode.system;

  void toggle() { ... }
}
```

### GoRouter: redirect guard로 인증 처리

```dart
// router.dart
final router = GoRouter(
  redirect: (context, state) {
    final auth = ref.read(authNotifierProvider);
    final isLoggedIn = auth is AuthStateAuthenticated;
    final isLoginPage = state.uri.path == '/login';

    if (!isLoggedIn && !isLoginPage) return '/login';
    if (isLoggedIn && isLoginPage) return '/home';
    return null;
  },
  routes: [...],
);
```

### Dio: 인터셉터 구조

```dart
// api_client.dart
// 요청 인터셉터: Bearer 토큰 + X-Timezone 헤더 주입
// 응답 인터셉터: { code, message, result } → result unwrap
// 에러 인터셉터: 401 → 토큰 삭제 + /login 리다이렉트
```

### OAuth 인증 플로우

```dart
final result = await FlutterWebAuth2.authenticate(
  url: '$apiBase/api/v1/auth/google?redirect_uri=${Uri.encodeComponent("helper://auth")}',
  callbackUrlScheme: 'helper',
);
final uri = Uri.parse(result);
final sessionToken = uri.queryParameters['session_token'];
final authCode = uri.queryParameters['auth_code'];
final isNewUser = uri.queryParameters['is_new_user'] == 'true';
```

### VoiceService: PCM 스트리밍 → WebSocket

```dart
// voice_service.dart
class VoiceService {
  final AudioRecorder _recorder = AudioRecorder();
  late WebSocketChannel _channel;

  Future<void> start(String token) async {
    _channel = WebSocketChannel.connect(Uri.parse(
      '$wsBase/api/v1/voice/stream?language=ko-KR&sample_rate=16000',
    ));
    final stream = await _recorder.startStream(RecordConfig(
      encoder: AudioEncoder.pcm16bits,
      sampleRate: 16000,
      numChannels: 1,
    ));
    _audioSub = stream.listen((chunk) => _channel.sink.add(chunk));
  }

  Future<void> stop() async {
    await _recorder.stop();
    _audioSub?.cancel();
    _channel.sink.add(jsonEncode({'type': 'stop'}));
  }
}
```

### 색상 시스템

`AppColors` 상수를 직접 사용하고, `AppTheme.light()` / `AppTheme.dark()`로 ThemeData를 생성합니다.

| 용도 | Light | Dark |
|------|-------|------|
| 배경 | #ffffff | #151718 |
| 텍스트 | #11181C | #ECEDEE |
| Accent | #4a9eff | #60a5fa |
| 카드 배경 | #ffffff | #1f2937 |
| 경계선 | #e5e7eb | #374151 |
| 위험 | #ef4444 | #ef4444 |

### 캘린더 애니메이션

```dart
// AnimationController + SizeTransition으로 월/주 전환
// 월 뷰: 6행 × 7열 전체 표시
// 주 뷰: 선택된 주의 1행만 표시
// 전환: Curves.easeInOutCubic, 300ms
```

## GoRouter 구조

```
/                  → auth 상태에 따라 리다이렉트
/login             → LoginScreen
/signup            → SignupScreen (auth_code 쿼리 파라미터)
/home (ShellRoute) → 탭 네비게이터
  /home            → HomeScreen
  /home/calendar   → CalendarScreen
  /home/record     → (탭 탭 시 voice sheet 표시)
  /home/reminders  → ReminderScreen
  /home/profile    → ProfileScreen
/memory/:id        → MemoryDetailScreen
/settings          → SettingsScreen
```

## 코드 품질

```bash
dart analyze         # 정적 분석
flutter test         # 테스트 실행
```

- `analysis_options.yaml`에 strict linting 규칙 적용
- riverpod_generator 사용 시 `just gen`으로 코드 재생성 필수
- 모델 클래스는 `fromJson` / `toJson` 명시적 구현 (json_serializable 미사용)
