import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test, vi } from "vitest";

import { VehicleCard } from "@/features/vehicles/vehicle-card";
import type { Vehicle } from "@/features/vehicles/types";

const mockVehicle: Vehicle = {
  id: "veh-1",
  brand: "Volkswagen",
  model: "Golf",
  generation: "VII",
  trim: "1.6 TDI",
  engine_code: "CRKB",
  power_kw: 81,
  fuel_type: "DIESEL",
  transmission: "MANUAL",
  year: 2016,
  first_listed_at: "2026-01-01T00:00:00Z",
  listing_count: 2,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

test("renders vehicle summary and triggers onSelect", async () => {
  const onSelect = vi.fn();
  render(<VehicleCard vehicle={mockVehicle} onSelect={onSelect} />);

  expect(screen.getByText("Volkswagen Golf")).toBeInTheDocument();
  expect(screen.getByText("1.6 TDI")).toBeInTheDocument();
  expect(screen.getByText(/2 anuncios/i)).toBeInTheDocument();

  const button = screen.getByRole("button", { name: /ver detalles de volkswagen golf/i });
  await userEvent.click(button);

  expect(onSelect).toHaveBeenCalledWith(mockVehicle);
});

test("vehicle card has no accessibility violations", async () => {
  const { container } = render(<VehicleCard vehicle={mockVehicle} onSelect={vi.fn()} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
