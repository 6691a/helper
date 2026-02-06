import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import { ThemedText } from "@/components/themed-text";
import { useThemeColor } from "@/hooks/use-theme-color";

interface GoogleLoginButtonProps {
  onPress: () => void;
  isLoading?: boolean;
}

export function GoogleLoginButton({
  onPress,
  isLoading,
}: GoogleLoginButtonProps) {
  const backgroundColor = useThemeColor({}, "background");
  const textColor = useThemeColor({}, "text");
  const borderColor = useThemeColor(
    { light: "#dadce0", dark: "#5f6368" },
    "text",
  );

  return (
    <Pressable
      style={[styles.button, { backgroundColor, borderColor }]}
      onPress={onPress}
      disabled={isLoading}
    >
      {isLoading ? (
        <ActivityIndicator size="small" color={textColor} />
      ) : (
        <>
          <View style={styles.iconContainer}>
            <ThemedText style={styles.googleG}>G</ThemedText>
          </View>
          <ThemedText style={styles.text}>Google로 계속하기</ThemedText>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 280,
  },
  iconContainer: {
    width: 24,
    height: 24,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  googleG: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#4285F4",
  },
  text: {
    fontSize: 16,
    fontWeight: "600",
  },
});
