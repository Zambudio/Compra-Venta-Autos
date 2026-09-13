import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as authApi from "@/features/auth/api";
import * as systemApi from "@/features/system/api";
import { SettingsView } from "@/features/system/settings-view";
import { renderWithClient } from "@/test/render";

const sources: systemApi.Source[] = [
  {
    key: "manual",
    name: "Entrada manual",
    provider_kind: "MANUAL",
    is_active: true,
    is_automatable: true,
    latest_review: null,
  },
  {
    key: "wallapop",
    name: "Wallapop",
    provider_kind: "CONNECTOR",
    is_active: false,
    is_automatable: false,
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
  expect(screen.getByText("Todo operativo")).toBeInTheDocument();
  expect(screen.getByText("Entrada manual")).toBeInTheDocument();
  expect(screen.getByText("Wallapop")).toBeInTheDocument();

  await user.click(
    screen.getByRole("button", { name: "Comprobar Wallapop" }),
  );

  expect(
    await screen.findByText("Autorización oficial pendiente"),
  ).toBeInTheDocument();
});

test("lets an owner disable an active source", async () => {
  const user = userEvent.setup();
  const update = vi
    .spyOn(systemApi, "updateSource")
    .mockResolvedValue({ ...sources[0], is_active: false });
  renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");

  await user.click(
    screen.getByRole("button", { name: "Desactivar Entrada manual" }),
  );

  await waitFor(() => expect(update).toHaveBeenCalledWith("manual", false));
});

test("keeps connector changes read-only for viewers", async () => {
  renderWithClient(<SettingsView userRole="VIEWER" />);
  await screen.findByText("Entrada manual");

  expect(
    screen.getByRole("button", { name: "Desactivar Entrada manual" }),
  ).toBeDisabled();
  expect(screen.getByText("Solo lectura")).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  const { container } = renderWithClient(<SettingsView userRole="OWNER" />);
  await screen.findByText("Entrada manual");
  expect(await axe(container)).toHaveNoViolations();
});
