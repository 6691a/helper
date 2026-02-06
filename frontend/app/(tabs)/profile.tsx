import {Alert, Pressable, StyleSheet, Text} from "react-native";

import {ThemedView} from "@/components/themed-view";
import {UserInfoCard} from "@/components/user-info-card";
import {useAuth} from "@/contexts/auth-context";

export default function ProfileScreen() {
  const {logout} = useAuth();

  const handleLogout = () => {
    Alert.alert("로그아웃", "로그아웃 하시겠습니까?", [
      {text: "취소", style: "cancel"},
      {
        text: "로그아웃",
        style: "destructive",
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  return (
    <ThemedView style={styles.container}>
      <UserInfoCard/>

      <Pressable style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutButtonText}>로그아웃</Text>
      </Pressable>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  logoutButton: {
    marginTop: 24,
    backgroundColor: "#ef4444",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
  },
  logoutButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});
