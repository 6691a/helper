import { apiClient } from "./client";
import type { AuthResponse, SignupRequest, User } from "./types";

export const authApi = {
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/api/v1/auth/me");
    return response as User;
  },

  async signup(
    data: SignupRequest,
  ): Promise<{ session_token: string; user: User }> {
    const response = await apiClient.post<AuthResponse>(
      "/api/v1/auth/signup",
      data,
    );
    // Backend returns { session_token } after unwrapping
    // For now, we don't get user data back, so caller needs to construct it
    return response as { session_token: string; user: User };
  },

  async logout(): Promise<void> {
    await apiClient.post("/api/v1/auth/logout");
  },
};
