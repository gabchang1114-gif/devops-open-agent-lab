import { apiClient, setAuthToken } from "@/services/api";
import type { AuthTokenResponse, LoginRequest, SignUpRequest, AuthUser } from "@/types/auth";

export const AUTH_TOKEN_KEY = "kda_auth_token";

export const authApi = {
  async signUp(request: SignUpRequest): Promise<AuthTokenResponse> {
    const response = await apiClient.post<AuthTokenResponse>("/api/v1/auth/signup", request);
    return response.data;
  },

  async login(request: LoginRequest): Promise<AuthTokenResponse> {
    const response = await apiClient.post<AuthTokenResponse>("/api/v1/auth/login", request);
    return response.data;
  },

  async getMe(): Promise<AuthUser> {
    const response = await apiClient.get<AuthUser>("/api/v1/auth/me");
    return response.data;
  },
};

export function persistAuthToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  setAuthToken(token);
}

export function loadAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(AUTH_TOKEN_KEY);
  setAuthToken(null);
}
