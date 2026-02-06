import { StatusBar, StyleSheet, View } from "react-native";
import { router } from "expo-router";
import { GoogleLoginButton } from "@/components/google-login-button";
import { ThemedText } from "@/components/themed-text";
import { useGoogleLogin } from "@/hooks/use-google-login";
import { useAuth } from "@/contexts/auth-context";
import { useThemeColor } from "@/hooks/use-theme-color";
import { useColorScheme } from "@/hooks/use-color-scheme";

export default function LoginScreen() {
  const { startOAuthFlow, isLoading, error } = useGoogleLogin();
  const { login } = useAuth();
  const backgroundColor = useThemeColor({}, "background");
  const colorScheme = useColorScheme();

  const handleGoogleLogin = async () => {
    const result = await startOAuthFlow();

    if (!result) return;

    if (result.is_new_user && result.auth_code) {
      // Navigate to signup screen
      router.push("/(auth)/signup");
    } else if (!result.is_new_user && result.session_token) {
      // Existing user - login
      await login(result.session_token, {
        id: 0, // Placeholder - backend should return user data
        email: result.email || "",
        nickname: result.nickname || "",
        profile_image: result.profile_image || null,
      });
      router.replace("/(tabs)");
    }
  };

  return (
    <View style={[styles.container, { backgroundColor }]}>
      <StatusBar
        barStyle={colorScheme === "dark" ? "light-content" : "dark-content"}
      />
      <View style={styles.content}>
        <ThemedText style={styles.title}>Helper</ThemedText>
        <View style={styles.buttonContainer}>
          <GoogleLoginButton
            onPress={handleGoogleLogin}
            isLoading={isLoading}
          />
        </View>
        {error && (
          <ThemedText
            style={styles.errorText}
            lightColor="#ef4444"
            darkColor="#fca5a5"
          >
            {error}
          </ThemedText>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    lineHeight: 40,
    marginBottom: 60,
    textAlign: "center",
  },
  buttonContainer: {
    width: "100%",
    alignItems: "center",
  },
  errorText: {
    marginTop: 16,
    fontSize: 14,
    textAlign: "center",
  },
});
