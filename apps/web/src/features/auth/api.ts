import { ApiError, apiRequest, readCookie } from "@/lib/api";
import type { SystemStatus, User } from "@/features/auth/types";

export async function getCurrentUser(): Promise<User | null> {
  try {
    return await apiRequest<User>("/auth/me");
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function login(credentials: { email: string; password: string }) {
  return apiRequest<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function logout() {
  const csrfToken = readCookie("motorscope_csrf");
  return apiRequest<{ success: boolean }>("/auth/logout", {
    method: "POST",
    headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
  });
}

export function getSystemStatus() {
  return apiRequest<SystemStatus>("/system/status");
}
