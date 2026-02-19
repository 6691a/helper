import { useRef, useState } from "react";
import {
  StyleSheet,
  View,
  Platform,
  PermissionsAndroid,
  Alert,
  Dimensions,
  ActivityIndicator,
} from "react-native";
import { WebView, WebViewMessageEvent } from "react-native-webview";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Modal from "react-native-modal";
import { useTheme } from "@/contexts/theme-context";
import { API_BASE } from "@/constants/config";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const SHEET_HEIGHT = SCREEN_HEIGHT * 0.4;

export default function RecordModal() {
  const webViewRef = useRef<WebView>(null);
  const { colorScheme } = useTheme();
  const theme = colorScheme === "dark" ? "dark" : "light";
  const insets = useSafeAreaInsets();
  const [isVisible, setIsVisible] = useState(true);
  const [isWebViewReady, setIsWebViewReady] = useState(false);

  const handleClose = () => {
    setIsVisible(false);
  };

  const handleModalHide = () => {
    router.back();
  };

  const handleLoad = async () => {
    if (Platform.OS === "android") {
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
    }
  };

  const handleContentProcessDidTerminate = () => {
    webViewRef.current?.reload();
  };

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);

      switch (data.type) {
        case "submit":
          router.back();
          break;
        case "cancel":
          router.back();
          break;
        case "error":
          if (data.message === "microphone_permission_denied") {
            Alert.alert(
              "권한 필요",
              "마이크 접근 권한이 필요합니다. 설정에서 권한을 허용해주세요.",
            );
          }
          break;
      }
    } catch {
      // JSON 파싱 실패 시 무시
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
      backdropOpacity={0.3}
      backdropColor="#000"
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
        {!isWebViewReady && (
          <View style={[styles.loadingContainer, { backgroundColor }]}>
            <ActivityIndicator
              size="large"
              color={colorScheme === "dark" ? "#4a9eff" : "#007aff"}
            />
          </View>
        )}
        <WebView
          key={`webview-${theme}`}
          ref={webViewRef}
          source={{
            uri,
            headers: {
              "ngrok-skip-browser-warning": "true",
            },
          }}
          style={[styles.webview, { opacity: isWebViewReady ? 1 : 0 }]}
          backgroundColor={backgroundColor}
          onLoad={handleLoad}
          onLoadEnd={() => setIsWebViewReady(true)}
          onMessage={handleMessage}
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
  loadingContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 1,
  },
});
