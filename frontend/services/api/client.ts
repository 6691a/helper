import axios, { type AxiosError } from "axios";
import { router } from "expo-router";
import { API_BASE } from "@/constants/config";
import { secureStorage } from "@/lib/secure-storage";
import type { ApiError } from "./types";

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Add auth token and timezone
apiClient.interceptors.request.use(
  async (config) => {
    const token = await secureStorage.getSessionToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add timezone header for server-side datetime conversion
    try {
      const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      config.headers["X-Timezone"] = timeZone;
    } catch (error) {
      // Fallback to UTC if timezone detection fails
      config.headers["X-Timezone"] = "UTC";
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: Handle errors and unwrap backend response
apiClient.interceptors.response.use(
  (response) => {
    // Unwrap backend response structure: { code, message, result }
    // Return just the result for easier consumption
    if (
      response.data &&
      typeof response.data === "object" &&
      "result" in response.data
    ) {
      return response.data.result;
    }
    return response.data;
  },
  async (error: AxiosError<ApiError>) => {
    // Handle authentication errors (401 Unauthorized, 403 Forbidden)
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Clear invalid token
      await secureStorage.clearAll();

      // Redirect to login page
      // Use setTimeout to avoid navigation during render
      setTimeout(() => {
        router.replace("/(auth)/login");
      }, 0);
    }

    const errorMessage =
      error.response?.data?.detail ||
      error.message ||
      "네트워크 오류가 발생했습니다";
    return Promise.reject(new Error(errorMessage));
  },
);
