"use client";

import { useState } from "react";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { RedirectIfAuthenticated } from "@/components/auth/RedirectIfAuthenticated";
import { useAuth } from "@/context/AuthContext";

function getErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (typeof response?.data?.detail === "string") {
      return response.data.detail;
    }
  }
  return "Unable to create account. Please try again.";
}

function SignUpForm() {
  const { signUp } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      await signUp({ email, password });
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Sign up"
      subtitle="Create an account for the DevOps Open Agent platform"
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-brand-400 hover:text-brand-300">
            Sign in
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
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            className="input-field"
          />
        </div>

        <div>
          <label htmlFor="confirm-password" className="sr-only">
            Confirm password
          </label>
          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Confirm password"
            className="input-field"
          />
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <button type="submit" disabled={isSubmitting} className="btn-primary">
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}

export default function SignUpPage() {
  return (
    <RedirectIfAuthenticated>
      <SignUpForm />
    </RedirectIfAuthenticated>
  );
}
