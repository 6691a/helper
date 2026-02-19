import { Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useThemeColor } from "@/hooks/use-theme-color";

interface BackButtonProps {
  onPress?: () => void;
  color?: string;
  size?: number;
  style?: object;
}

export function BackButton({
  onPress,
  color,
  size = 24,
  style,
}: BackButtonProps) {
  const defaultColor = useThemeColor({}, "text");
  const pressedBg = useThemeColor(
    { light: "#f3f4f6", dark: "#374151" },
    "background",
  );

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      router.back();
    }
  };

  return (
    <Pressable
      style={({ pressed }) => [
        styles.backButton,
        pressed && { backgroundColor: pressedBg },
        style,
      ]}
      onPress={handlePress}
    >
      <Ionicons name="arrow-back" size={size} color={color || defaultColor} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
  },
});
