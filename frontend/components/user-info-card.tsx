import {Image, StyleSheet, Text, View} from "react-native";
import {useAuth} from "@/contexts/auth-context";
import {useThemeColor} from "@/hooks/use-theme-color";

export function UserInfoCard() {
    const {user} = useAuth();
    const backgroundColor = useThemeColor({}, "background");
    const textColor = useThemeColor({}, "text");
    const borderColor = useThemeColor(
        {light: "#dadce0", dark: "#5f6368"},
        "text"
    );

    if (!user) return null;

    return (
        <View style={[styles.card, {backgroundColor, borderColor}]}>
            <View style={styles.avatarContainer}>
                {user.profile_image ? (
                    <Image source={{uri: user.profile_image}} style={styles.avatar}/>
                ) : (
                    <View style={[styles.avatar, styles.avatarPlaceholder]}>
                        <Text style={styles.avatarText}>
                            {user.nickname.charAt(0).toUpperCase()}
                        </Text>
                    </View>
                )}
            </View>

            <View style={styles.infoContainer}>
                <Text style={[styles.nickname, {color: textColor}]}>
                    {user.nickname}
                </Text>
                {user.email && (
                    <Text style={[styles.email, {color: textColor}]}>
                        {user.email}
                    </Text>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        flexDirection: "row",
        alignItems: "center",
        padding: 16,
        borderRadius: 12,
        borderWidth: 1,
    },
    avatarContainer: {
        marginRight: 16,
    },
    avatar: {
        width: 60,
        height: 60,
        borderRadius: 30,
    },
    avatarPlaceholder: {
        backgroundColor: "#4a9eff",
        alignItems: "center",
        justifyContent: "center",
    },
    avatarText: {
        color: "#fff",
        fontSize: 24,
        fontWeight: "bold",
    },
    infoContainer: {
        flex: 1,
    },
    nickname: {
        fontSize: 18,
        fontWeight: "600",
        marginBottom: 4,
    },
    email: {
        fontSize: 14,
        opacity: 0.7,
    },
});