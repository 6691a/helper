import { ScrollView, StyleSheet, View } from "react-native";
import { UserInfoCard } from "@/components/user-info-card";
import { useThemeColor } from "@/hooks/use-theme-color";

export default function HomeScreen() {
  const backgroundColor = useThemeColor({}, "background");

  return (
    <ScrollView style={[styles.container, { backgroundColor }]}>
      <View style={styles.content}>
        <UserInfoCard />
        {/* Add more content here */}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
});
