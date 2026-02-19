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
  profile_image?: string | null;
}

export interface ApiError {
  detail: string;
}

export enum MemoryType {
  ITEM = "item",
  PLACE = "place",
  SCHEDULE = "schedule",
  PERSON = "person",
  MEMO = "memo",
}

export interface Memory {
  id: number;
  type: MemoryType;
  keywords: string;
  content: string;
  metadata_: Record<string, unknown> | null;
  original_text: string;
  created_at: string;
  updated_at: string;
}
