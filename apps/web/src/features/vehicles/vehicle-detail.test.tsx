import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/vehicles/api";
import type { VehicleDetail as TVehicleDetail } from "@/features/vehicles/types";
import { VehicleDetail } from "@/features/vehicles/vehicle-detail";
import { renderWithClient } from "@/test/render";

const mockDetail: TVehicleDetail = {
  id: "veh-123",
  brand: "SEAT",
  model: "Ibiza",
  generation: "IV",
  trim: "1.4 TDI",
  engine_code: "BMS",
  power_kw: 59,
  fuel_type: "DIESEL",
  transmission: "MANUAL",
  year: 2014,
  first_listed_at: "2026-01-10T00:00:00Z",
  listing_count: 2,
  created_at: "2026-01-10T00:00:00Z",
  updated_at: "2026-01-15T00:00:00Z",
  listings: [
    {
      id: "l-1",
      source_id: "s-1",
      external_id: "ext-1",
      brand: "SEAT",
      model: "Ibiza",
      year: 2014,
      mileage_km: 125000,
      price_amount: "4800.00",
      price_currency: "EUR",
      province: "Madrid",
      status: "ACTIVE",
      image_urls: [],
    },
    {
      id: "l-2",
      source_id: "s-2",
      external_id: "ext-2",
      brand: "SEAT",
      model: "Ibiza",
      year: 2014,
      mileage_km: 126000,
      price_amount: "4950.00",
      price_currency: "EUR",
      province: "Toledo",
      status: "ACTIVE",
      image_urls: [],
    },
  ],
  history: {
    lowest_observed_price: "4800.00",
    highest_observed_price: "5200.00",
    current_min_price: "4800.00",
    days_on_market: 22,
    total_price_changes: 2,
  },
  market_estimate: {
    id: "est-1",
    vehicle_id: "veh-123",
    listing_id: null,
    estimated_amount: "4900.00",
    low_amount: "4500.00",
    high_amount: "5300.00",
    currency: "EUR",
    method: "COMPARABLES_MEDIAN_IQR",
    number_of_comparables: 8,
    confidence_score: "0.820",
    calculated_at: "2026-01-20T00:00:00Z",
  },
};

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders vehicle detail with specs, market estimate, history and listings", async () => {
  vi.spyOn(api, "getVehicle").mockResolvedValue(mockDetail);
  const onBack = vi.fn();

  renderWithClient(<VehicleDetail vehicleId="veh-123" onBack={onBack} />);

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "SEAT Ibiza" })).toBeInTheDocument();
  });

  // Specs
  expect(screen.getByText("1.4 TDI")).toBeInTheDocument();
  expect(screen.getByText("59 kW")).toBeInTheDocument();

  // Market estimate
  expect(screen.getByText(/4\.?900/)).toBeInTheDocument();
  expect(screen.getByText(/82%/)).toBeInTheDocument();
  expect(screen.getByText(/8 vehículos/)).toBeInTheDocument();

  // History
  expect(screen.getByText("22")).toBeInTheDocument();
  expect(screen.getAllByText(/4\.?800/)[0]).toBeInTheDocument();

  // Listings
  expect(screen.getByText(/ext-1/)).toBeInTheDocument();
  expect(screen.getByText(/ext-2/)).toBeInTheDocument();

  // Back button
  const backBtn = screen.getByRole("button", { name: /volver al catálogo de vehículos/i });
  await userEvent.click(backBtn);
  expect(onBack).toHaveBeenCalled();
});

test("recalculates market estimate when button is clicked", async () => {
  vi.spyOn(api, "getVehicle").mockResolvedValue(mockDetail);
  const computeSpy = vi.spyOn(api, "computeVehicleMarketEstimate").mockResolvedValue({
    ...mockDetail.market_estimate!,
    estimated_amount: "5100.00",
  });

  renderWithClient(<VehicleDetail vehicleId="veh-123" onBack={vi.fn()} />);

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "SEAT Ibiza" })).toBeInTheDocument();
  });

  const recalcBtn = screen.getByRole("button", { name: /recalcular estimación de mercado/i });
  await userEvent.click(recalcBtn);

  expect(computeSpy).toHaveBeenCalledWith("veh-123");
});

test("vehicle detail has no accessibility violations", async () => {
  vi.spyOn(api, "getVehicle").mockResolvedValue(mockDetail);
  const { container } = renderWithClient(<VehicleDetail vehicleId="veh-123" onBack={vi.fn()} />);

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "SEAT Ibiza" })).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
