import { Image, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "@/contexts/auth-context";
import { useThemeColor } from "@/hooks/use-theme-color";

export function UserInfoCard() {
  const { user } = useAuth();
  const textColor = useThemeColor({}, "text");

  if (!user) {
    return null;
  }

  if (!user.nickname || user.nickname.trim() === "") {
    return (
      <View style={styles.container}>
        <Text style={[styles.errorText, { color: textColor }]}>
          프로필 정보를 불러오는 중...
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {user.profile_image ? (
        <Image source={{ uri: user.profile_image }} style={styles.avatar} />
      ) : (
        <View style={styles.avatarPlaceholder}>
          <Ionicons name="person-circle" size={100} color="#9CA3AF" />
        </View>
      )}

      <Text style={[styles.nickname, { color: textColor }]}>
        {user.nickname}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    paddingVertical: 32,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  avatarPlaceholder: {
    width: 100,
    height: 100,
    alignItems: "center",
    justifyContent: "center",
  },
  nickname: {
    fontSize: 24,
    fontWeight: "700",
    marginTop: 16,
    textAlign: "center",
  },
  errorText: {
    fontSize: 16,
    textAlign: "center",
  },
});
