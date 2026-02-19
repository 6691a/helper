import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { router } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { ThemedText } from "@/components/themed-text";
import { ScreenHeader } from "@/components/screen-header";
import { authApi } from "@/services/api/auth";
import { useAuth } from "@/contexts/auth-context";
import { secureStorage } from "@/lib/secure-storage";
import { useThemeColor } from "@/hooks/use-theme-color";
import { useColorScheme } from "@/hooks/use-color-scheme";

export default function SignupScreen() {
  const [nickname, setNickname] = useState("");
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [isPickingImage, setIsPickingImage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const nicknameInputRef = useRef<TextInput>(null);

  const colorScheme = useColorScheme();
  const backgroundColor = useThemeColor({}, "background");
  const textColor = useThemeColor({}, "text");
  const borderColor = useThemeColor(
    { light: "#dadce0", dark: "#374151" },
    "border",
  );
  const placeholderBg = useThemeColor(
    { light: "#f3f4f6", dark: "#374151" },
    "background",
  );
  const inputBg = useThemeColor(
    { light: "#fff", dark: "#1f2937" },
    "background",
  );
  const isDark = colorScheme === "dark";

  // Pre-load permissions on component mount
  useEffect(() => {
    (async () => {
      await ImagePicker.getMediaLibraryPermissionsAsync();
    })();
  }, []);

  const pickImage = async () => {
    try {
      setIsPickingImage(true);

      // Check current permission status first
      let permissionResult =
        await ImagePicker.getMediaLibraryPermissionsAsync();

      // Request permission only if not granted
      if (permissionResult.status !== "granted") {
        permissionResult =
          await ImagePicker.requestMediaLibraryPermissionsAsync();

        if (permissionResult.status !== "granted") {
          Alert.alert("권한 필요", "사진 라이브러리 접근 권한이 필요합니다.");
          return;
        }
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.7,
        allowsMultipleSelection: false,
      });

      if (!result.canceled) {
        setProfileImage(result.assets[0].uri);
      }
    } finally {
      setIsPickingImage(false);
    }
  };

  const handleSignup = async () => {
    if (nickname.trim().length < 2) {
      setError("닉네임은 2자 이상이어야 합니다");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const authCode = await secureStorage.getAuthCode();
      if (!authCode) {
        Alert.alert(
          "오류",
          "인증 코드를 찾을 수 없습니다. 다시 로그인해주세요.",
          [{ text: "확인", onPress: () => router.replace("/(auth)/login") }],
        );
        return;
      }

      const response = await authApi.signup({
        auth_code: authCode,
        nickname: nickname.trim(),
        profile_image: profileImage,
      });

      // Clear auth code
      await secureStorage.removeAuthCode();

      // Store session token first
      await secureStorage.setSessionToken(response.session_token);

      // Fetch actual user data from server
      const userData = await authApi.getCurrentUser();

      // Login with actual user data
      await login(response.session_token, userData);

      router.replace("/(tabs)");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "회원가입에 실패했습니다";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor }]}
      edges={["top", "bottom"]}
    >
      <ScreenHeader title="" />
      <KeyboardAwareScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        bottomOffset={40}
        extraKeyboardSpace={20}
      >
        <ThemedText style={styles.title}>프로필 완성</ThemedText>
        <ThemedText style={styles.subtitle}>
          닉네임과 프로필 이미지를 설정해주세요
        </ThemedText>

        <View style={styles.profileImageContainer}>
          <Pressable
            style={({ pressed }) => [
              styles.profileImageButton,
              pressed && styles.profileImageButtonPressed,
            ]}
            onPress={pickImage}
            disabled={isLoading || isPickingImage}
          >
            {isPickingImage ? (
              <View
                style={[
                  styles.profileImagePlaceholder,
                  { backgroundColor: placeholderBg, borderColor },
                ]}
              >
                <ActivityIndicator size="large" color="#4a9eff" />
              </View>
            ) : profileImage ? (
              <Image
                source={{ uri: profileImage }}
                style={styles.profileImage}
              />
            ) : (
              <View
                style={[
                  styles.profileImagePlaceholder,
                  { backgroundColor: placeholderBg, borderColor },
                ]}
              >
                <Text
                  style={[
                    styles.profileImagePlaceholderText,
                    { color: textColor },
                  ]}
                >
                  +
                </Text>
              </View>
            )}
          </Pressable>
          <ThemedText style={styles.profileImageLabel}>
            {isPickingImage ? "이미지 선택 중..." : "프로필 사진 선택"}
          </ThemedText>
        </View>

        <View style={styles.inputContainer}>
          <ThemedText style={styles.label}>닉네임</ThemedText>
          <TextInput
            ref={nicknameInputRef}
            style={[
              styles.input,
              { borderColor, color: textColor, backgroundColor: inputBg },
            ]}
            placeholder="닉네임을 입력하세요"
            placeholderTextColor={isDark ? "#9CA3AF" : "#6B7280"}
            value={nickname}
            onChangeText={setNickname}
            maxLength={20}
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="off"
            editable={!isLoading}
            returnKeyType="done"
            onSubmitEditing={handleSignup}
            blurOnSubmit={true}
            keyboardType="default"
            textContentType="none"
            importantForAutofill="no"
            underlineColorAndroid="transparent"
            {...(Platform.OS === "android" && {
              focusable: true,
            })}
          />
          <ThemedText style={styles.helperText}>2-20자</ThemedText>
        </View>

        {error && <ThemedText style={styles.errorText}>{error}</ThemedText>}

        <Pressable
          style={[
            styles.button,
            (isLoading || nickname.trim().length < 2) && styles.buttonDisabled,
          ]}
          onPress={handleSignup}
          disabled={isLoading || nickname.trim().length < 2}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <ThemedText style={styles.buttonText}>회원가입 완료</ThemedText>
          )}
        </Pressable>
      </KeyboardAwareScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
    paddingTop: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    lineHeight: 40,
    marginBottom: 8,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 32,
    textAlign: "center",
  },
  profileImageContainer: {
    alignItems: "center",
    marginBottom: 32,
  },
  profileImageButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: "hidden",
    marginBottom: 12,
  },
  profileImageButtonPressed: {
    opacity: 0.7,
  },
  profileImage: {
    width: "100%",
    height: "100%",
  },
  profileImagePlaceholder: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderRadius: 60,
  },
  profileImagePlaceholderText: {
    fontSize: 48,
    lineHeight: 48,
    includeFontPadding: false,
  },
  profileImageLabel: {
    fontSize: 14,
  },
  inputContainer: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 44,
  },
  helperText: {
    fontSize: 12,
    marginTop: 4,
  },
  button: {
    backgroundColor: "#4a9eff",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  errorText: {
    marginBottom: 16,
    color: "#ef4444",
    fontSize: 14,
    textAlign: "center",
  },
});
