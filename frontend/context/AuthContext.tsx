"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import {
  authApi,
  clearAuthToken,
  loadAuthToken,
  persistAuthToken,
} from "@/services/authApi";
import { setAuthToken } from "@/services/api";
import type { AuthUser, LoginRequest, SignUpRequest } from "@/types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (request: LoginRequest) => Promise<void>;
  signUp: (request: SignUpRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = loadAuthToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    setAuthToken(token);
    authApi
      .getMe()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        clearAuthToken();
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const applyAuth = useCallback((token: string, currentUser: AuthUser) => {
    persistAuthToken(token);
    setUser(currentUser);
  }, []);

  const login = useCallback(
    async (request: LoginRequest) => {
      const response = await authApi.login(request);
      applyAuth(response.access_token, response.user);
      router.push("/");
    },
    [applyAuth, router],
  );

  const signUp = useCallback(
    async (request: SignUpRequest) => {
      const response = await authApi.signUp(request);
      applyAuth(response.access_token, response.user);
      router.push("/");
    },
    [applyAuth, router],
  );

  const logout = useCallback(() => {
    clearAuthToken();
    setAuthToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      signUp,
      logout,
    }),
    [user, isLoading, login, signUp, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
