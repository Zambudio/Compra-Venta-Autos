import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getCurrentUser,
  getSystemStatus,
  login,
  logout,
} from "@/features/auth/api";
import { ApiError, apiRequest, readCookie } from "@/lib/api";

describe("lib/api", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("completes successful requests", async () => {
    const mockData = { id: "123", name: "test" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await apiRequest<{ id: string; name: string }>("/test");
    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/test",
      expect.objectContaining({
        credentials: "include",
      }),
    );
  });

  it("handles error responses with error details", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ code: "unauthorized", detail: "Invalid token" }),
    } as Response);

    await expect(apiRequest("/test")).rejects.toThrow(ApiError);
    await expect(apiRequest("/test")).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
      message: "Invalid token",
    });
  });

  it("handles error responses when json parsing fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("Invalid json");
      },
    } as unknown as Response);

    await expect(apiRequest("/test")).rejects.toMatchObject({
      status: 500,
      code: "request_failed",
      message: "No se pudo completar la solicitud.",
    });
  });

  it("reads cookies accurately", () => {
    document.cookie = "motorscope_csrf=test-csrf-token; other=value";
    expect(readCookie("motorscope_csrf")).toBe("test-csrf-token");
    expect(readCookie("missing")).toBeUndefined();
  });

  it("invokes auth api helper functions", async () => {
    const user = { id: "u1", email: "a@b.com", role: "OWNER" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => user,
    } as Response);

    await getCurrentUser();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/me",
      expect.anything(),
    );

    await login({ email: "a@b.com", password: "pwd" });
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({ method: "POST" }),
    );

    document.cookie = "motorscope_csrf=csrf123";
    await logout();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf123" }),
      }),
    );

    const status = {
      api: "available",
      postgresql: "available",
      redis: "ready",
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => status,
    } as Response);

    await getSystemStatus();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/system/status",
      expect.anything(),
    );
  });
});
