import { useState } from "react";
import * as WebBrowser from "expo-web-browser";
import * as Linking from "expo-linking";
import { makeRedirectUri } from "expo-auth-session";
import { API_BASE } from "@/constants/config";
import { secureStorage } from "@/lib/secure-storage";

// Required for OAuth callback handling
WebBrowser.maybeCompleteAuthSession();

interface OAuthResult {
  auth_code?: string;
  session_token?: string;
  is_new_user: boolean;
  email?: string;
  nickname?: string;
  profile_image?: string | null;
}

export function useGoogleLogin() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const redirectUri = makeRedirectUri({
    scheme: "helper",
    path: "/",
  });

  const startOAuthFlow = async (): Promise<OAuthResult | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // Build OAuth initiation URL
      const authUrl = `${API_BASE}/api/v1/auth/google?redirect_uri=${encodeURIComponent(
        redirectUri,
      )}`;

      // Open system browser for OAuth (SFSafariViewController on iOS, Chrome Custom Tabs on Android)
      const result = await WebBrowser.openAuthSessionAsync(
        authUrl,
        redirectUri,
      );

      if (result.type === "cancel") {
        setError("로그인이 취소되었습니다");
        return null;
      }

      if (result.type === "success" && result.url) {
        // Parse callback URL parameters
        const url = Linking.parse(result.url);
        const params = url.queryParams as Record<string, string>;

        const isNewUser = params.is_new_user === "true";

        if (isNewUser && params.auth_code) {
          // New user - store auth_code
          await secureStorage.setAuthCode(params.auth_code);
          return {
            auth_code: params.auth_code,
            is_new_user: true,
            email: params.email,
            nickname: params.nickname,
            profile_image: params.profile_image || null,
          };
        } else if (!isNewUser && params.session_token) {
          // Existing user - return session_token
          return {
            session_token: params.session_token,
            is_new_user: false,
            email: params.email,
            nickname: params.nickname,
            profile_image: params.profile_image || null,
          };
        } else {
          throw new Error("Invalid OAuth response");
        }
      }

      return null;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "인증에 실패했습니다";
      setError(errorMessage);
      console.error("OAuth flow error:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    startOAuthFlow,
    isLoading,
    error,
  };
}
