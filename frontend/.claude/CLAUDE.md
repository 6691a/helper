# Frontend - Expo React Native 앱 개발 가이드

이 파일은 Helper 프론트엔드 개발 시 Claude Code가 참고할 가이드입니다.

## 프로젝트 구조

```
frontend/
├── app/                      # Expo Router (file-based routing)
│   ├── (auth)/               # 인증 관련 화면 (로그인, 회원가입)
│   ├── (tabs)/               # 탭 네비게이션 화면
│   ├── _layout.tsx           # 루트 레이아웃
│   └── settings.tsx          # 설정 화면
├── components/               # 재사용 가능한 컴포넌트
│   ├── ui/                   # UI 프리미티브
│   └── themed-*.tsx          # 테마 지원 컴포넌트
├── contexts/                 # React Context (전역 상태)
│   ├── auth-context.tsx      # 인증 상태 관리
│   └── theme-context.tsx     # 테마 상태 관리
├── hooks/                    # 커스텀 훅
├── constants/                # 상수 (테마, 색상, 폰트)
├── services/api/             # API 클라이언트
└── lib/                      # 유틸리티 함수
```

## 다크모드 구현 (Expo 공식 방법)

### 기본 원칙

Expo는 React Native의 `useColorScheme` 훅과 `Appearance` API를 통해 네이티브 다크모드를 지원합니다.

**참고 문서:** https://docs.expo.dev/develop/user-interface/color-themes/

### 1. 시스템 색상 스키마 감지

```tsx
import { useColorScheme } from "react-native";

function MyComponent() {
  const colorScheme = useColorScheme(); // 'light' | 'dark' | null

  return (
    <View
      style={{
        backgroundColor: colorScheme === "dark" ? "#000" : "#fff",
      }}
    >
      <Text>Current theme: {colorScheme}</Text>
    </View>
  );
}
```

### 2. Appearance API (명령형)

```tsx
import { Appearance } from "react-native";

// 현재 스키마 즉시 가져오기
const currentScheme = Appearance.getColorScheme();

// 변경 감지
const subscription = Appearance.addChangeListener(({ colorScheme }) => {
  console.log("Color scheme changed to:", colorScheme);
});

// 구독 해제
subscription.remove();
```

### 3. app.json 설정

```json
{
  "expo": {
    "userInterfaceStyle": "automatic"
  }
}
```

**옵션:**

- `automatic` (기본값): 시스템 설정 따름
- `light`: 라이트 모드만 지원
- `dark`: 다크 모드만 지원

### 4. 테마 컨텍스트 구현 (권장)

시스템 설정 + 사용자 선택 지원:

```tsx
// contexts/theme-context.tsx
import { createContext, useContext, useState, useEffect } from "react";
import { useColorScheme as useSystemColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

type ThemeMode = "system" | "light" | "dark";
type ColorScheme = "light" | "dark";

interface ThemeContextType {
  colorScheme: ColorScheme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }) {
  const systemColorScheme = useSystemColorScheme();
  const [themeMode, setThemeModeState] = useState<ThemeMode>("system");
  const [colorScheme, setColorScheme] = useState<ColorScheme>(
    systemColorScheme ?? "light",
  );

  // 저장된 설정 로드
  useEffect(() => {
    async function loadTheme() {
      const saved = await AsyncStorage.getItem("@theme_mode");
      if (saved) setThemeModeState(saved as ThemeMode);
    }
    loadTheme();
  }, []);

  // themeMode에 따라 colorScheme 업데이트
  useEffect(() => {
    if (themeMode === "system") {
      setColorScheme(systemColorScheme ?? "light");
    } else {
      setColorScheme(themeMode);
    }
  }, [themeMode, systemColorScheme]);

  const setThemeMode = async (mode: ThemeMode) => {
    await AsyncStorage.setItem("@theme_mode", mode);
    setThemeModeState(mode);
  };

  return (
    <ThemeContext.Provider value={{ colorScheme, themeMode, setThemeMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
}
```

### 5. useColorScheme 훅 래핑

```tsx
// hooks/use-color-scheme.ts
import { useTheme } from "@/contexts/theme-context";

export function useColorScheme() {
  const { colorScheme } = useTheme();
  return colorScheme;
}
```

### 6. 테마 컬러 훅

```tsx
// hooks/use-theme-color.ts
import { useColorScheme } from "./use-color-scheme";

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: keyof typeof Colors.light & keyof typeof Colors.dark,
) {
  const theme = useColorScheme();
  const colorFromProps = props[theme];

  if (colorFromProps) {
    return colorFromProps;
  } else {
    return Colors[theme][colorName];
  }
}
```

### 7. Themed 컴포넌트

```tsx
// components/themed-text.tsx
import { Text, type TextProps } from "react-native";
import { useThemeColor } from "@/hooks/use-theme-color";

export function ThemedText({
  style,
  lightColor,
  darkColor,
  ...rest
}: ThemedTextProps) {
  const color = useThemeColor({ light: lightColor, dark: darkColor }, "text");
  return <Text style={[{ color }, style]} {...rest} />;
}
```

### 8. React Navigation 테마 연동

```tsx
import {
  DarkTheme,
  DefaultTheme,
  ThemeProvider,
} from "@react-navigation/native";
import { useColorScheme } from "@/hooks/use-color-scheme";

function RootLayoutNav() {
  const colorScheme = useColorScheme();

  return (
    <ThemeProvider value={colorScheme === "dark" ? DarkTheme : DefaultTheme}>
      <Stack>{/* ... */}</Stack>
    </ThemeProvider>
  );
}
```

## 컬러 테마 정의

```tsx
// constants/theme.ts
const tintColorLight = "#4a9eff";
const tintColorDark = "#60a5fa";

export const Colors = {
  light: {
    text: "#11181C",
    background: "#fff",
    tint: tintColorLight,
    icon: "#687076",
    tabIconDefault: "#687076",
    tabIconSelected: tintColorLight,
    border: "#e5e7eb",
  },
  dark: {
    text: "#ECEDEE",
    background: "#151718",
    tint: tintColorDark,
    icon: "#9BA1A6",
    tabIconDefault: "#9BA1A6",
    tabIconSelected: tintColorDark,
    border: "#374151",
  },
};
```

## 다크모드 베스트 프랙티스

1. **항상 useThemeColor 사용**: 하드코딩된 색상 대신 테마 컬러 훅 사용
2. **ThemedView/ThemedText 활용**: 일관된 테마 적용을 위해 themed 컴포넌트 사용
3. **동적 스타일**: StyleSheet보다는 인라인 스타일로 동적 색상 적용
4. **이미지 대응**: 다크모드용 이미지 별도 제공 (선택사항)
5. **StatusBar 설정**:
   ```tsx
   <StatusBar style={colorScheme === "dark" ? "light" : "dark"} />
   ```

## 안티패턴 (피해야 할 것)

❌ **하드코딩된 색상**

```tsx
<View style={{ backgroundColor: '#fff' }}>
```

✅ **테마 색상 사용**

```tsx
const backgroundColor = useThemeColor({}, 'background');
<View style={{ backgroundColor }}>
```

❌ **시스템 테마 무시**

```tsx
const [isDark, setIsDark] = useState(false); // 시스템 설정 무시
```

✅ **시스템 테마 존중**

```tsx
const colorScheme = useColorScheme(); // 시스템 설정 따름
```

## 참고 자료

- [Expo Color Themes 공식 문서](https://docs.expo.dev/develop/user-interface/color-themes/)
- [React Native Appearance](https://reactnative.dev/docs/appearance)
- [React Navigation Themes](https://reactnavigation.org/docs/themes)
