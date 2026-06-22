export interface AuthUser {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignUpRequest {
  email: string;
  password: string;
}
