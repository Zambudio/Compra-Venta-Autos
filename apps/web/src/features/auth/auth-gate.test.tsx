import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import { AuthGate } from "@/features/auth/auth-gate";
import * as api from "@/features/auth/api";
import * as listingsApi from "@/features/listings/api";
import type { User } from "@/features/auth/types";

beforeEach(() => {
  vi.spyOn(listingsApi, "getListings").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 12,
    total: 0,
    has_more: false,
  });
});

function renderGate(user: User | null, isPending = false) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  if (isPending) {
    vi.spyOn(api, "getCurrentUser").mockReturnValue(new Promise(() => {}));
  } else {
    vi.spyOn(api, "getCurrentUser").mockResolvedValue(user as User);
  }

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthGate />
    </QueryClientProvider>,
  );
}

test("renders loading screen when checking session", () => {
  renderGate(null, true);
  expect(screen.getByText("Comprobando sesión…")).toBeInTheDocument();
});

test("renders login screen when unauthenticated", async () => {
  renderGate(null, false);
  expect(
    await screen.findByRole("heading", { name: "Acceso privado" }),
  ).toBeInTheDocument();
});

test("renders the app shell when authenticated", async () => {
  renderGate({ id: "user-1", email: "owner@example.com", role: "OWNER" }, false);
  expect(
    await screen.findByRole("heading", { name: "Anuncios" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Cerrar sesión" }),
  ).toBeInTheDocument();
});
