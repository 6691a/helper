import axios, {type AxiosError} from "axios";
import {API_BASE} from "@/constants/config";
import {secureStorage} from "@/lib/secure-storage";
import type {ApiError} from "./types";

export const apiClient = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
    async (config) => {
        const token = await secureStorage.getSessionToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor: Handle errors and unwrap backend response
apiClient.interceptors.response.use(
    (response) => {
        // Unwrap backend response structure: { code, message, result }
        // Return just the result for easier consumption
        if (response.data && typeof response.data === "object" && "result" in response.data) {
            return response.data.result;
        }
        return response.data;
    },
    async (error: AxiosError<ApiError>) => {
        // Handle authentication errors (401 Unauthorized, 403 Forbidden)
        if (error.response?.status === 401 || error.response?.status === 403) {
            // Clear invalid token
            // Note: Don't call logout here to avoid circular dependency
            // The AuthContext will handle navigation
            await secureStorage.clearAll();
        }

        const errorMessage =
            error.response?.data?.detail || error.message || "네트워크 오류가 발생했습니다";
        return Promise.reject(new Error(errorMessage));
    }
);