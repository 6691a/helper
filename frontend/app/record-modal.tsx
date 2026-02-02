import { useRef, useState } from "react";
import {
  StyleSheet,
  View,
  useColorScheme,
  Platform,
  PermissionsAndroid,
  Alert,
  Dimensions,
} from "react-native";
import { WebView, WebViewMessageEvent } from "react-native-webview";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Modal from "react-native-modal";
import { API_BASE } from "@/constants/config";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const SHEET_HEIGHT = SCREEN_HEIGHT * 0.4;

export default function RecordModal() {
  const webViewRef = useRef<WebView>(null);
  const colorScheme = useColorScheme();
  const theme = colorScheme === "dark" ? "dark" : "light";
  const insets = useSafeAreaInsets();
  const [isVisible, setIsVisible] = useState(true);

  const handleClose = () => {
    setIsVisible(false);
  };

  const handleModalHide = () => {
    router.back();
  };

  const handleLoad = async () => {
    if (Platform.OS === "android") {
      try {
        const hasPermission = await PermissionsAndroid.check(
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        );

        if (!hasPermission) {
          await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
            {
              title: "마이크 권한",
              message: "음성 인식을 위해 마이크 접근이 필요합니다.",
              buttonPositive: "허용",
              buttonNegative: "거부",
            },
          );
        }
      } catch (err) {
        console.warn("Permission error:", err);
      }
    }
  };

  const handleError = (syntheticEvent: any) => {
    const { nativeEvent } = syntheticEvent;
    console.error("WebView error:", nativeEvent);
  };

  const handleHttpError = (syntheticEvent: any) => {
    const { nativeEvent } = syntheticEvent;
    console.error(
      "WebView HTTP error:",
      nativeEvent.statusCode,
      nativeEvent.description,
    );
  };

  const handleContentProcessDidTerminate = () => {
    console.error("WebView content process terminated");
    webViewRef.current?.reload();
  };

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      console.log("WebView message:", data);

      switch (data.type) {
        case "submit":
          console.log("Submitted text:", data.text);
          console.log("Session ID:", data.sessionId);
          router.back();
          break;
        case "cancel":
          console.log("Recording cancelled");
          router.back();
          break;
        case "error":
          console.error("Recording error:", data.message);
          if (data.message === "microphone_permission_denied") {
            Alert.alert(
              "권한 필요",
              "마이크 접근 권한이 필요합니다. 설정에서 권한을 허용해주세요.",
            );
          }
          break;
      }
    } catch (e) {
      console.error("Failed to parse WebView message:", e);
    }
  };

  const uri = `${API_BASE}/static/voice-input.html?theme=${theme}&auto_open=true`;
  const backgroundColor = colorScheme === "dark" ? "#1a1a1a" : "#ffffff";

  return (
    <Modal
      isVisible={isVisible}
      onBackdropPress={handleClose}
      onSwipeComplete={handleClose}
      onModalHide={handleModalHide}
      swipeDirection="down"
      style={styles.modal}
      backdropOpacity={0.5}
      animationIn="slideInUp"
      animationOut="slideOutDown"
      animationInTiming={300}
      animationOutTiming={250}
      useNativeDriverForBackdrop
      propagateSwipe
    >
      <View
        style={[
          styles.sheet,
          { backgroundColor, paddingBottom: insets.bottom },
        ]}
      >
        <WebView
          ref={webViewRef}
          source={{
            uri,
            headers: {
              "ngrok-skip-browser-warning": "true",
            },
          }}
          style={styles.webview}
          onLoad={handleLoad}
          onMessage={handleMessage}
          onError={handleError}
          onHttpError={handleHttpError}
          onContentProcessDidTerminate={handleContentProcessDidTerminate}
          allowsInlineMediaPlayback
          mediaPlaybackRequiresUserAction={false}
          javaScriptEnabled
          domStorageEnabled
          mediaCapturePermissionGrantType="grant"
          androidLayerType="hardware"
          cacheEnabled={false}
          originWhitelist={["*"]}
          scrollEnabled={false}
          bounces={false}
          allowsBackForwardNavigationGestures={false}
          contentMode="mobile"
          automaticallyAdjustContentInsets={false}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modal: {
    justifyContent: "flex-end",
    margin: 0,
  },
  sheet: {
    height: SHEET_HEIGHT,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    overflow: "hidden",
  },
  webview: {
    flex: 1,
  },
});
