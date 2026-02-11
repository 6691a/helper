import { Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";

interface BackButtonProps {
  onPress?: () => void;
  color?: string;
  size?: number;
  style?: object;
}

export function BackButton({
  onPress,
  color = "#11181C",
  size = 24,
  style,
}: BackButtonProps) {
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
        pressed && styles.backButtonPressed,
        style,
      ]}
      onPress={handlePress}
    >
      <Ionicons name="arrow-back" size={size} color={color} />
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
  backButtonPressed: {
    backgroundColor: "#f3f4f6",
  },
});
