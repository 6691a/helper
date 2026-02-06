export interface User {
  id: number;
  email: string;
  nickname: string;
  profile_image: string | null;
}

export interface BackendResponse<T> {
  code: number;
  message: string;
  result: T;
}

export interface AuthResponse {
  session_token: string;
}

export interface SignupRequest {
  auth_code: string;
  nickname: string;
}

export interface ApiError {
  detail: string;
}
