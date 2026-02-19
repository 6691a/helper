import { ScrollView, StyleSheet, Switch, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Stack } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";
import { ScreenHeader } from "@/components/screen-header";
import { useTheme } from "@/contexts/theme-context";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useThemeColor } from "@/hooks/use-theme-color";

export default function SettingsScreen() {
  const { themeMode, setThemeMode } = useTheme();
  const colorScheme = useColorScheme();
  const backgroundColor = useThemeColor({}, "background");
  const textColor = useThemeColor({}, "text");
  const borderColor = useThemeColor(
    { light: "#e5e7eb", dark: "#374151" },
    "border",
  );
  const isDark = colorScheme === "dark";

  const handleThemeToggle = async (value: boolean) => {
    await setThemeMode(value ? "dark" : "light");
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor }]}
      edges={["top"]}
    >
      <Stack.Screen
        options={{
          headerShown: false,
        }}
      />
      <ScreenHeader title="설정" />
      <ScrollView style={styles.container}>
        <ThemedView style={styles.section}>
          <ThemedText
            style={[
              styles.sectionTitle,
              { color: isDark ? "#9ca3af" : "#6b7280" },
            ]}
          >
            테마
          </ThemedText>

          <View
            style={[styles.settingItem, { borderBottomColor: borderColor }]}
          >
            <View style={styles.settingLeft}>
              <Ionicons
                name="moon"
                size={24}
                color={textColor}
                style={styles.settingIcon}
              />
              <ThemedText style={styles.settingLabel}>다크 모드</ThemedText>
            </View>
            <Switch
              value={themeMode === "dark"}
              onValueChange={handleThemeToggle}
              trackColor={{ false: "#e5e7eb", true: "#4a9eff" }}
              thumbColor="#fff"
            />
          </View>
        </ThemedView>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#9ca3af",
    marginBottom: 12,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  settingItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 16,
  },
  settingLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  settingIcon: {
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: "500",
  },
});
