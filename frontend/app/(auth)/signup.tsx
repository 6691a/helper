import {useState} from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {router} from "expo-router";
import {ThemedText} from "@/components/themed-text";
import {authApi} from "@/services/api/auth";
import {useAuth} from "@/contexts/auth-context";
import {secureStorage} from "@/lib/secure-storage";

export default function SignupScreen() {
    const [nickname, setNickname] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const {login} = useAuth();

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
                    [{text: "확인", onPress: () => router.replace("/(auth)/login")}]
                );
                return;
            }

            const response = await authApi.signup({
                auth_code: authCode,
                nickname: nickname.trim(),
            });

            // Clear auth code
            await secureStorage.removeAuthCode();

            // Login with new session token
            // Note: Backend should ideally return user data along with session_token
            await login(response.session_token, {
                id: 0, // Placeholder
                email: "",
                nickname: nickname.trim(),
                profile_image: null,
            });

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
        <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
            <KeyboardAvoidingView
                style={styles.container}
                behavior={Platform.OS === "ios" ? "padding" : "height"}
            >
                <View style={styles.content}>
                    <ThemedText style={styles.title}>Complete Your Profile</ThemedText>
                    <ThemedText style={styles.subtitle}>Choose a nickname to get started</ThemedText>

                    <View style={styles.inputContainer}>
                        <ThemedText style={styles.label}>닉네임</ThemedText>
                        <TextInput
                            style={styles.input}
                            placeholder="닉네임을 입력하세요"
                            value={nickname}
                            onChangeText={setNickname}
                            maxLength={20}
                            autoCapitalize="none"
                            autoCorrect={false}
                            editable={!isLoading}
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
                            <ActivityIndicator color="#fff"/>
                        ) : (
                            <ThemedText style={styles.buttonText}>회원가입 완료</ThemedText>
                        )}
                    </Pressable>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: "#fff",
    },
    container: {
        flex: 1,
        backgroundColor: "#fff",
    },
    content: {
        flex: 1,
        justifyContent: "center",
        padding: 24,
        paddingTop: 60,
    },
    title: {
        fontSize: 32,
        fontWeight: "bold",
        marginBottom: 8,
        color: "#11181C",
        textAlign: "center",
    },
    subtitle: {
        fontSize: 16,
        color: "#687076",
        marginBottom: 32,
        textAlign: "center",
    },
    inputContainer: {
        marginBottom: 24,
    },
    label: {
        fontSize: 14,
        fontWeight: "600",
        color: "#11181C",
        marginBottom: 8,
    },
    input: {
        borderWidth: 1,
        borderColor: "#dadce0",
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        color: "#11181C",
    },
    helperText: {
        fontSize: 12,
        color: "#687076",
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