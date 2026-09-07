import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as authApi from "@/features/auth/api";
import * as knowledgeApi from "@/features/knowledge/api";
import * as listingsApi from "@/features/listings/api";
import * as vehiclesApi from "@/features/vehicles/api";
import { AppShell } from "@/features/shell/app-shell";
import { renderWithClient } from "@/test/render";

const user = { id: "u1", email: "owner@example.com", role: "OWNER" as const };

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(listingsApi, "getListings").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 12,
    total: 0,
    has_more: false,
  });
  vi.spyOn(authApi, "getSystemStatus").mockResolvedValue({
    api: "available",
    postgresql: "available",
    redis: "ready",
  });
  vi.spyOn(vehiclesApi, "getVehicles").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 12,
    total: 0,
    has_more: false,
  });
  vi.spyOn(vehiclesApi, "getMatchCandidates").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 1,
    total: 0,
    has_more: false,
  });
  vi.spyOn(knowledgeApi, "getKnownIssues").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    has_more: false,
  });
});

test("opens on the Anuncios tab and switches to Vehículos, Conocimiento and Estado", async () => {
  const kbUser = userEvent.setup();
  renderWithClient(
    <AppShell user={user} onLogout={vi.fn()} isLoggingOut={false} />,
  );

  expect(
    await screen.findByRole("heading", { name: "Anuncios" }),
  ).toBeInTheDocument();

  // Switch to Vehículos
  await kbUser.click(screen.getByRole("button", { name: "Vehículos" }));
  expect(
    await screen.findByRole("heading", { name: "Vehículos y Mercado" }),
  ).toBeInTheDocument();

  // Switch to Conocimiento
  await kbUser.click(screen.getByRole("button", { name: "Conocimiento" }));
  expect(
    await screen.findByRole("heading", { name: /Base de Conocimiento/i }),
  ).toBeInTheDocument();

  // Switch to Estado
  await kbUser.click(screen.getByRole("button", { name: "Estado" }));
  expect(
    await screen.findByRole("heading", { name: "Foundation operativa" }),
  ).toBeInTheDocument();
});

test("the active tab is marked as current", async () => {
  renderWithClient(
    <AppShell user={user} onLogout={vi.fn()} isLoggingOut={false} />,
  );
  await screen.findByRole("heading", { name: "Anuncios" });

  expect(screen.getByRole("button", { name: "Anuncios" })).toHaveAttribute(
    "aria-current",
    "page",
  );
});

test("logout button triggers onLogout", async () => {
  const kbUser = userEvent.setup();
  const onLogout = vi.fn().mockResolvedValue(undefined);
  renderWithClient(
    <AppShell user={user} onLogout={onLogout} isLoggingOut={false} />,
  );
  await screen.findByRole("heading", { name: "Anuncios" });

  await kbUser.click(screen.getByRole("button", { name: "Cerrar sesión" }));

  expect(onLogout).toHaveBeenCalled();
});

test("has no accessibility violations", async () => {
  const { container } = renderWithClient(
    <AppShell user={user} onLogout={vi.fn()} isLoggingOut={false} />,
  );
  await screen.findByRole("heading", { name: "Anuncios" });
  expect(await axe(container)).toHaveNoViolations();
});
