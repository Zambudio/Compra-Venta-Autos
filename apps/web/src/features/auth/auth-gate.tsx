"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getCurrentUser, login, logout } from "@/features/auth/api";
import { LoginScreen } from "@/features/auth/login-screen";
import type { LoginValues } from "@/features/auth/login-form";
import { StatusScreen } from "@/features/auth/status-screen";
import { ApiError } from "@/lib/api";

export function AuthGate() {
  const queryClient = useQueryClient();
  const [loginError, setLoginError] = useState<string>();
  const session = useQuery({
    queryKey: ["current-user"],
    queryFn: getCurrentUser,
    retry: false,
  });
  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      queryClient.setQueryData(["current-user"], user);
      setLoginError(undefined);
    },
  });
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["current-user"], null);
      queryClient.removeQueries({ queryKey: ["system-status"] });
    },
  });

  async function handleLogin(values: LoginValues) {
    try {
      await loginMutation.mutateAsync(values);
    } catch (error) {
      setLoginError(
        error instanceof ApiError && error.status === 429
          ? "Demasiados intentos. Espera antes de volver a intentarlo."
          : "El correo o la contraseña no son válidos.",
      );
    }
  }

  if (session.isPending) {
    return (
      <main
        className="grid min-h-dvh place-items-center bg-white"
        aria-busy="true"
      >
        <p className="text-sm text-[var(--muted)]">Comprobando sesión…</p>
      </main>
    );
  }

  if (session.data) {
    return (
      <StatusScreen
        user={session.data}
        onLogout={async () => {
          await logoutMutation.mutateAsync();
        }}
        isLoggingOut={logoutMutation.isPending}
      />
    );
  }

  return <LoginScreen onSubmit={handleLogin} serverError={loginError} />;
}
