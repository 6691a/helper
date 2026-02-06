import {useRef, useState} from "react";
import {ActivityIndicator, Modal, Pressable, StyleSheet, View,} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import type {WebViewNavigation} from "react-native-webview";
import {WebView} from "react-native-webview";
import {ThemedText} from "@/components/themed-text";

interface OAuthWebViewModalProps {
    visible: boolean;
    authUrl: string;
    redirectScheme: string;
    onSuccess: (url: string) => void;
    onCancel: () => void;
}

export function OAuthWebViewModal({
                                      visible,
                                      authUrl,
                                      redirectScheme,
                                      onSuccess,
                                      onCancel,
                                  }: OAuthWebViewModalProps) {
    const [loading, setLoading] = useState(true);
    const webViewRef = useRef<WebView>(null);

    const handleNavigationStateChange = (navState: WebViewNavigation) => {
        const {url} = navState;

        // 리다이렉트 URL 감지 (helper://, exp:// 등)
        if (url.startsWith(redirectScheme)) {
            onSuccess(url);
        }
    };

    return (
        <Modal
            visible={visible}
            animationType="slide"
            presentationStyle="fullScreen"
            onRequestClose={onCancel}
        >
            <SafeAreaView style={styles.safeArea}>
                <View style={styles.container}>
                    <View style={styles.header}>
                        <ThemedText style={styles.title}>로그인</ThemedText>
                        <Pressable onPress={onCancel} style={styles.closeButton}>
                            <ThemedText style={styles.closeText}>닫기</ThemedText>
                        </Pressable>
                    </View>

                    {loading && (
                        <View style={styles.loadingContainer}>
                            <ActivityIndicator size="large" color="#4a9eff"/>
                        </View>
                    )}

                    <WebView
                        ref={webViewRef}
                        source={{uri: authUrl}}
                        onNavigationStateChange={handleNavigationStateChange}
                        onLoadStart={() => setLoading(true)}
                        onLoadEnd={() => setLoading(false)}
                        style={styles.webview}
                        // 세션 쿠키 허용
                        sharedCookiesEnabled={true}
                        thirdPartyCookiesEnabled={true}
                        // User-Agent를 일반 Chrome 브라우저로 위장
                        userAgent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                        // iOS 추가 설정
                        allowsBackForwardNavigationGestures={false}
                        hideKeyboardAccessoryView={true}
                        keyboardDisplayRequiresUserAction={false}
                    />
                </View>
            </SafeAreaView>
        </Modal>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: "#fff",
    },
    container: {
        flex: 1,
        backgroundColor: "#fff",
    },
    header: {
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: "#e5e7eb",
        backgroundColor: "#fff",
    },
    title: {
        fontSize: 18,
        fontWeight: "600",
    },
    closeButton: {
        padding: 8,
    },
    closeText: {
        color: "#4a9eff",
        fontSize: 16,
    },
    loadingContainer: {
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#fff",
        zIndex: 1,
    },
    webview: {
        flex: 1,
    },
});