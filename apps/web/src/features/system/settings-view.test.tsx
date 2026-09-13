import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as authApi from "@/features/auth/api";
import * as systemApi from "@/features/system/api";
import { SettingsView } from "@/features/system/settings-view";
import { renderWithClient } from "@/test/render";
import { ApiError } from "@/lib/api";

const sources: systemApi.Source[] = [
  {
    key: "manual",
    name: "Entrada manual",
    provider_kind: "MANUAL",
    is_active: true,
    enabled: true,
    is_automatable: true,
    config: {},
    last_sync: null,
    sync_error: null,
    health: "ok",
    latest_review: null,
  },
  {
    key: "wallapop",
    name: "Wallapop",
    provider_kind: "CONNECTOR",
    is_active: true,
    enabled: true,
    is_automatable: true,
    config: { rate_limit_per_hour: 100 },
    last_sync: "2026-09-12T10:00:00Z",
    sync_error: null,
    health: "ok",
    latest_review: {
      acquisition_method: "Acceso oficial pendiente",
      automated_allowed: false,
      authentication_required: "Autorización escrita y credenciales oficiales",
      rate_limit: null,
      terms_url: "https://about.wallapop.com/condiciones-de-uso/",
      checked_at: "2026-09-12T00:00:00Z",
      notes: "No activar sin autorización.",
    },
  },
];

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(authApi, "getSystemStatus").mockResolvedValue({
    api: "available",
    postgresql: "available",
    redis: "ready",
  });
  vi.spyOn(systemApi, "getSources").mockResolvedValue(sources);
});

test("combines platform status and connector controls in settings", async () => {
  const user = userEvent.setup();
  vi.spyOn(systemApi, "checkSourceHealth").mockResolvedValue({
    source_key: "wallapop",
    healthy: false,
    detail: "Autorización oficial pendiente",
    checked_at: "2026-09-12T10:00:00Z",
  });
  renderWithClient(<SettingsView userRole="OWNER" />);

  expect(
    await screen.findByRole("heading", { name: "Configuración" }),
  ).toBeInTheDocument();
  expect(await screen.findByText("Todo operativo")).toBeInTheDocument();
  expect(screen.getByText("Entrada manual")).toBeInTheDocument();
  expect(screen.getByText("Wallapop")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Comprobar Wallapop" }));

  expect(
    await screen.findByText(/Autorización oficial pendiente/),
  ).toBeInTheDocument();
});

test("lets an owner disable an active source", async () => {
  const user = userEvent.setup();
  const update = vi.spyOn(systemApi, "updateSource").mockResolvedValue({
    key: "manual",
    enabled: false,
    config: {},
    last_sync: null,
    sync_error: null,
    updated_at: "2026-09-13T10:00:00Z",
  });
  renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");

  await user.click(screen.getByRole("switch", { name: "Entrada manual" }));

  await waitFor(() => expect(update).toHaveBeenCalledWith("manual", false));
});

test("keeps connector changes read-only for viewers", async () => {
  renderWithClient(<SettingsView userRole="VIEWER" />);
  await screen.findByText("Entrada manual");

  expect(screen.getByRole("switch", { name: "Entrada manual" })).toBeDisabled();
  expect(screen.getByText("Solo lectura")).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  const { container } = renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");
  expect(await axe(container)).toHaveNoViolations();
});

test("shows a pending state only on the connector being changed", async () => {
  const user = userEvent.setup();
  let resolveUpdate: (() => void) | undefined;
  vi.spyOn(systemApi, "updateSource").mockImplementation(
    () =>
      new Promise((resolve) => {
        resolveUpdate = () =>
          resolve({
            key: "manual",
            enabled: false,
            config: {},
            last_sync: null,
            sync_error: null,
            updated_at: "2026-09-13T10:00:00Z",
          });
      }),
  );
  renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");

  await user.click(screen.getByRole("switch", { name: "Entrada manual" }));

  expect(screen.getByRole("switch", { name: "Entrada manual" })).toBeDisabled();
  expect(screen.getByRole("switch", { name: "Wallapop" })).not.toBeDisabled();
  expect(screen.getByText(/Guardando…/)).toBeInTheDocument();
  resolveUpdate?.();
});

test("explains why the final active connector cannot be disabled", async () => {
  const user = userEvent.setup();
  vi.spyOn(systemApi, "updateSource").mockRejectedValue(
    new ApiError(400, "active_source_required", "Debe quedar uno activo"),
  );
  renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");

  await user.click(screen.getByRole("switch", { name: "Entrada manual" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Mantén al menos un conector activo",
  );
});

test("allows an owner to force a Wallapop synchronization", async () => {
  const user = userEvent.setup();
  vi.spyOn(systemApi, "syncSource").mockResolvedValue({
    id: "run-1",
    source_key: "wallapop",
    status: "SUCCESS",
    mode: "sync",
    listings_seen: 4,
    listings_created: 3,
    listings_updated: 1,
    snapshots_created: 4,
    error_summary: null,
    started_at: "2026-09-13T10:00:00Z",
    finished_at: "2026-09-13T10:00:01Z",
    created_at: "2026-09-13T10:00:00Z",
  });
  renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Wallapop");

  await user.click(
    screen.getByRole("button", { name: "Forzar sincronización de Wallapop" }),
  );

  expect(await screen.findByRole("status")).toHaveTextContent(
    "Sincronización de Wallapop completada",
  );
});
