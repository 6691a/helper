import { Platform } from "react-native";

export const API_BASE = Platform.select({
  default: "https://8d1ee7f0f895.ngrok-free.app",
});
