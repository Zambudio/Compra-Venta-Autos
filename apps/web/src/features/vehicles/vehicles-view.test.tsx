import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/vehicles/api";
import type {
  Vehicle,
  VehicleDetail as TVehicleDetail,
  VehiclePage,
} from "@/features/vehicles/types";
import { VehiclesView } from "@/features/vehicles/vehicles-view";
import { renderWithClient } from "@/test/render";

const mockVehicle: Vehicle = {
  id: "v-1",
  brand: "Toyota",
  model: "Auris",
  generation: "II",
  trim: "140H",
  engine_code: null,
  power_kw: 100,
  fuel_type: "HYBRID",
  transmission: "AUTOMATIC",
  year: 2016,
  first_listed_at: "2026-01-01T00:00:00Z",
  listing_count: 2,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

const mockPage: VehiclePage = {
  items: [mockVehicle],
  page: 1,
  page_size: 12,
  total: 1,
  has_more: false,
};

const mockDetail: TVehicleDetail = {
  ...mockVehicle,
  listings: [],
  history: null,
  market_estimate: null,
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api, "getMatchCandidates").mockResolvedValue({
    items: [],
    total: 3,
    page: 1,
    page_size: 1,
    has_more: false,
  });
});

test("renders vehicles catalog with badge and allows selection", async () => {
  vi.spyOn(api, "getVehicles").mockResolvedValue(mockPage);
  vi.spyOn(api, "getVehicle").mockResolvedValue(mockDetail);

  renderWithClient(<VehiclesView />);

  await waitFor(() => {
    expect(screen.getByText("Toyota Auris")).toBeInTheDocument();
  });

  // Badge de deduplicación con 3 pendientes
  expect(screen.getByText("3")).toBeInTheDocument();

  // Seleccionar vehículo
  const detailBtn = screen.getByRole("button", {
    name: /ver detalles de toyota auris/i,
  });
  await userEvent.click(detailBtn);

  await waitFor(() => {
    expect(
      screen.getByRole("heading", { name: "Toyota Auris" }),
    ).toBeInTheDocument();
  });

  // Volver
  const backBtn = screen.getByRole("button", {
    name: /volver al catálogo de vehículos/i,
  });
  await userEvent.click(backBtn);

  await waitFor(() => {
    expect(screen.getByText("Toyota Auris")).toBeInTheDocument();
  });
});

test("allows switching to deduplication tab", async () => {
  vi.spyOn(api, "getVehicles").mockResolvedValue(mockPage);

  renderWithClient(<VehiclesView />);

  const dedupTab = screen.getByRole("button", { name: /deduplicación/i });
  await userEvent.click(dedupTab);

  await waitFor(() => {
    expect(
      screen.getByRole("heading", { name: /deduplicación asistida/i }),
    ).toBeInTheDocument();
  });
});

test("renders empty catalog state when no vehicles exist", async () => {
  vi.spyOn(api, "getVehicles").mockResolvedValue({
    ...mockPage,
    items: [],
    total: 0,
  });

  renderWithClient(<VehiclesView />);

  await waitFor(() => {
    expect(
      screen.getByText(/no se encontraron vehículos unificados/i),
    ).toBeInTheDocument();
  });
});

test("vehicles view has no accessibility violations", async () => {
  vi.spyOn(api, "getVehicles").mockResolvedValue(mockPage);
  const { container } = renderWithClient(<VehiclesView />);

  await waitFor(() => {
    expect(screen.getByText("Toyota Auris")).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
