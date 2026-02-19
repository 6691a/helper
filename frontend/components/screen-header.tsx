import { StyleSheet, View } from "react-native";
import { ThemedText } from "@/components/themed-text";
import { BackButton } from "@/components/back-button";
import { useThemeColor } from "@/hooks/use-theme-color";

interface ScreenHeaderProps {
  title: string;
  onBackPress?: () => void;
  rightElement?: React.ReactNode;
}

export function ScreenHeader({
  title,
  onBackPress,
  rightElement,
}: ScreenHeaderProps) {
  const backgroundColor = useThemeColor({}, "background");

  return (
    <View style={[styles.header, { backgroundColor }]}>
      <BackButton onPress={onBackPress} />
      <ThemedText style={styles.headerTitle}>{title}</ThemedText>
      <View style={styles.headerRight}>{rightElement}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: "600",
    flex: 1,
    textAlign: "center",
  },
  headerRight: {
    width: 40,
    alignItems: "center",
    justifyContent: "center",
  },
});
