import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import type { VehicleDetail } from "@/features/vehicles/types";
import { renderWithClient } from "@/test/render";
import * as api from "./api";
import type { ReliabilityLookupResponse, VehicleMitigation } from "./types";
import { VehicleReliabilityWidget } from "./vehicle-reliability-widget";

const mockVehicle: VehicleDetail = {
  id: "veh-123",
  brand: "Peugeot",
  model: "208",
  generation: "I",
  trim: "1.2 PureTech Allure",
  engine_code: "EB2",
  power_kw: 81,
  fuel_type: "PETROL",
  transmission: "MANUAL",
  year: 2016,
  first_listed_at: "2026-01-01T00:00:00Z",
  listing_count: 1,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  listings: [],
  history: null,
  market_estimate: null,
};

const mockReliability: ReliabilityLookupResponse = {
  brand: "Peugeot",
  model: "208",
  year: 2016,
  fuel_type: "PETROL",
  engine_code: "EB2",
  classification: "BLACKLIST",
  classification_rationale: "Motor EB2 PureTech con correa en baño de aceite y avería catastrófica documentada.",
  issues_count: 1,
  max_severity: "CRITICAL",
  total_estimated_repair_min: "1000.00",
  total_estimated_repair_max: "4000.00",
  currency: "EUR",
  has_recalls: true,
  issues: [
    {
      id: "iss-1",
      title: "Degradación de correa húmeda",
      description: "Desintegración prematura de correa en aceite.",
      component: "TIMING_SYSTEM",
      severity: "CRITICAL",
      frequency: "SYSTEMIC",
      typical_mileage_km: 60000,
      estimated_repair_cost_min: "1000.00",
      estimated_repair_cost_max: "4000.00",
      currency: "EUR",
      symptoms: "Aviso de presión de aceite",
      prevention: "Aceite homologado PSA B71 2010 y medición periódica",
      definitive_repair: "Cambio de kit de distribución",
      has_recall_campaign: true,
      recall_details: null,
      status: "VERIFIED",
      reviewed_by_user_id: null,
      reviewed_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
  preventive_recommendations: [
    "Aceite homologado PSA B71 2010 y medición periódica",
  ],
};

const mockMitigations: VehicleMitigation[] = [
  {
    id: "mit-1",
    vehicle_id: "veh-123",
    known_issue_id: "iss-1",
    mitigation_type: "INVOICE_PROVED_REPLACEMENT",
    description: "Correa sustituida a los 75.000 km con factura oficial.",
    applied_at: "2026-01-15T00:00:00Z",
    verified_by_user_id: null,
    created_at: "2026-01-15T00:00:00Z",
    updated_at: "2026-01-15T00:00:00Z",
    known_issue: {
      id: "iss-1",
      title: "Degradación de correa húmeda",
    } as any,
  },
];

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders reliability diagnosis with Blacklist badge, recalls and recommendations", async () => {
  vi.spyOn(api, "lookupVehicleReliability").mockResolvedValue(mockReliability);
  vi.spyOn(api, "getVehicleMitigations").mockResolvedValue(mockMitigations);

  renderWithClient(<VehicleReliabilityWidget vehicle={mockVehicle} />);

  await waitFor(() => {
    expect(screen.getByText(/Lista Negra/i)).toBeInTheDocument();
  });

  expect(screen.getByText(/Motor EB2 PureTech con correa en baño de aceite/i)).toBeInTheDocument();
  expect(screen.getByText(/Campaña oficial de revisión o recall detectada/i)).toBeInTheDocument();
  expect(screen.getAllByText(/1\.?000/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/4\.?000/).length).toBeGreaterThan(0);
  expect(screen.getByText(/PSA B71 2010/i)).toBeInTheDocument();
  expect(screen.getByText(/Correa sustituida a los 75\.000 km/i)).toBeInTheDocument();
});

test("allows adding a vehicle-level mitigation", async () => {
  vi.spyOn(api, "lookupVehicleReliability").mockResolvedValue(mockReliability);
  vi.spyOn(api, "getVehicleMitigations").mockResolvedValue([]);
  const addMitigationSpy = vi.spyOn(api, "addVehicleMitigation").mockResolvedValue({
    id: "mit-2",
    vehicle_id: "veh-123",
    known_issue_id: "iss-1",
    mitigation_type: "INVOICE_PROVED_REPLACEMENT",
    description: "Nueva correa instalada",
    applied_at: "2026-02-01T00:00:00Z",
    verified_by_user_id: null,
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-02-01T00:00:00Z",
  });

  renderWithClient(<VehicleReliabilityWidget vehicle={mockVehicle} />);

  await waitFor(() => {
    expect(screen.getByText(/Registrar mitigación/i)).toBeInTheDocument();
  });

  await userEvent.click(screen.getByRole("button", { name: /registrar mitigación/i }));

  const input = screen.getByLabelText(/Evidencia \/ Factura acreditativa:/i);
  await userEvent.type(input, "Factura de concesionario oficial");

  const submitBtn = screen.getByRole("button", { name: /guardar mitigación/i });
  await userEvent.click(submitBtn);

  expect(addMitigationSpy).toHaveBeenCalledWith(
    expect.objectContaining({
      vehicle_id: "veh-123",
      known_issue_id: "iss-1",
      description: "Factura de concesionario oficial",
    }),
  );
});

test("vehicle reliability widget has no accessibility violations", async () => {
  vi.spyOn(api, "lookupVehicleReliability").mockResolvedValue(mockReliability);
  vi.spyOn(api, "getVehicleMitigations").mockResolvedValue(mockMitigations);

  const { container } = renderWithClient(<VehicleReliabilityWidget vehicle={mockVehicle} />);

  await waitFor(() => {
    expect(screen.getByText(/Lista Negra/i)).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
