import { screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/auth/api";
import { StatusView } from "@/features/system/status-view";
import { renderWithClient } from "@/test/render";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("shows every dependency as available", async () => {
  vi.spyOn(api, "getSystemStatus").mockResolvedValue({
    api: "available",
    postgresql: "available",
    redis: "ready",
  });
  renderWithClient(<StatusView />);

  expect(await screen.findAllByText("Disponible")).toHaveLength(2);
  expect(screen.getByText("Preparado")).toBeInTheDocument();
});

test("shows an alert when the status check fails", async () => {
  vi.spyOn(api, "getSystemStatus").mockRejectedValue(new Error("down"));
  renderWithClient(<StatusView />);

  expect(
    await screen.findByText("No se pudo comprobar el estado del sistema."),
  ).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  vi.spyOn(api, "getSystemStatus").mockResolvedValue({
    api: "available",
    postgresql: "available",
    redis: "ready",
  });
  const { container } = renderWithClient(<StatusView />);
  await screen.findAllByText("Disponible");
  expect(await axe(container)).toHaveNoViolations();
});
