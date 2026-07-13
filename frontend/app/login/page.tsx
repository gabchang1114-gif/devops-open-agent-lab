"use client";

import { useState } from "react";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { RedirectIfAuthenticated } from "@/components/auth/RedirectIfAuthenticated";
import { useAuth } from "@/context/AuthContext";

function getErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const axiosError = error as {
      response?: { data?: { detail?: string }; status?: number };
      code?: string;
    };
    if (!axiosError.response) {
      return "Unable to reach the backend API. Make sure the backend is running on port 8000.";
    }
    if (typeof axiosError.response?.data?.detail === "string") {
      return axiosError.response.data.detail;
    }
  }
  return "Unable to sign in. Please try again.";
}

function LoginForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Access the DevOps Open Agent troubleshooting platform"
      footer={
        <>
          No account?{" "}
          <Link href="/signup" className="font-medium text-brand-400 hover:text-brand-300">
            Sign up
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="sr-only">
            Username
          </label>
          <input
            id="email"
            type="text"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Username"
            className="input-field"
          />
        </div>

        <div>
          <label htmlFor="password" className="sr-only">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            className="input-field"
          />
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button type="submit" disabled={isSubmitting} className="btn-primary">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}

export default function LoginPage() {
  return (
    <RedirectIfAuthenticated>
      <LoginForm />
    </RedirectIfAuthenticated>
  );
}
