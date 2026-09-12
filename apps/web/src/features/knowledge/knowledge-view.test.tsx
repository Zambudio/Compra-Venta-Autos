import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import { renderWithClient } from "@/test/render";
import * as api from "./api";
import { KnowledgeView } from "./knowledge-view";
import type { KnownIssuePage, VehicleClassificationPage } from "./types";

const mockIssuesPage: KnownIssuePage = {
  items: [
    {
      id: "iss-1",
      title: "Desgaste prematuro de cadena",
      description:
        "Cadena de distribución se estira provocando salto de dientes.",
      component: "TIMING_SYSTEM",
      severity: "HIGH",
      frequency: "FREQUENT",
      typical_mileage_km: 100000,
      estimated_repair_cost_min: "600.00",
      estimated_repair_cost_max: "1800.00",
      currency: "EUR",
      symptoms: "Ruido de traqueteo metálico en arranque en frío",
      prevention: "Cambio de tensor y comprobación de elongación",
      definitive_repair: "Kit de cadena reforzado",
      has_recall_campaign: false,
      recall_details: null,
      status: "VERIFIED",
      reviewed_by_user_id: null,
      reviewed_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      evidences: [],
    },
  ],
  page: 1,
  page_size: 20,
  total: 1,
  has_more: false,
};

const mockClassificationsPage: VehicleClassificationPage = {
  items: [
    {
      id: "cls-1",
      target_type: "ENGINE",
      target_id: "eng-1",
      status: "BLACKLIST",
      rationale: "Defecto de diseño en correa húmeda.",
      validity_start: null,
      validity_end: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
  page: 1,
  page_size: 20,
  total: 1,
  has_more: false,
};

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders knowledge view with issues list and subtabs", async () => {
  vi.spyOn(api, "getKnownIssues").mockResolvedValue(mockIssuesPage);

  renderWithClient(<KnowledgeView />);

  await waitFor(() => {
    expect(
      screen.getByText("Desgaste prematuro de cadena"),
    ).toBeInTheDocument();
  });

  expect(
    screen.getByText("Base de Conocimiento Técnico y Fiabilidad"),
  ).toBeInTheDocument();
  expect(screen.queryByText(/Ruido de traqueteo/i)).not.toBeInTheDocument(); // Accordion collapsed by default
});

test("switches between subtabs to show classifications and catalog", async () => {
  vi.spyOn(api, "getKnownIssues").mockResolvedValue(mockIssuesPage);
  vi.spyOn(api, "getClassifications").mockResolvedValue(
    mockClassificationsPage,
  );
  vi.spyOn(api, "getManufacturers").mockResolvedValue([
    {
      id: "m-1",
      name: "Volkswagen",
      country: "Alemania",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
  ]);
  vi.spyOn(api, "getModels").mockResolvedValue([
    {
      id: "mod-1",
      manufacturer_id: "m-1",
      name: "Golf",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
  ]);
  vi.spyOn(api, "getEngines").mockResolvedValue([
    {
      id: "eng-1",
      manufacturer_id: "m-1",
      name: "1.4 TSI",
      family_code: "EA111",
      fuel_type: "PETROL",
      displacement_cc: 1390,
      aspiration: "TURBOCHARGED",
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
  ]);
  vi.spyOn(api, "getGenerations").mockResolvedValue([
    {
      id: "gen-1",
      model_id: "mod-1",
      name: "Golf VI",
      year_start: 2008,
      year_end: 2012,
      created_at: "2026-01-01",
      updated_at: "2026-01-01",
    },
  ]);

  renderWithClient(<KnowledgeView />);

  // Cambiar a Clasificaciones
  const clsTab = screen.getByRole("button", { name: /Clasificaciones/i });
  await userEvent.click(clsTab);

  await waitFor(() => {
    expect(
      screen.getByText("Defecto de diseño en correa húmeda."),
    ).toBeInTheDocument();
  });

  // Cambiar a Catálogo
  const catalogTab = screen.getByRole("button", {
    name: /Catálogo Mecánico Canónico/i,
  });
  await userEvent.click(catalogTab);

  await waitFor(() => {
    expect(screen.getByText(/Jerarquía Técnica Canónica/i)).toBeInTheDocument();
  });

  const mfgSelect = screen.getByLabelText(/Fabricante/i);
  await userEvent.selectOptions(mfgSelect, "m-1");

  await waitFor(() => {
    expect(screen.getByText("1.4 TSI")).toBeInTheDocument();
  });

  const modelSelect = screen.getByLabelText(/Modelo/i);
  await userEvent.selectOptions(modelSelect, "mod-1");

  await waitFor(() => {
    expect(screen.getByText("Golf VI")).toBeInTheDocument();
  });
});

test("knowledge view has no accessibility violations", async () => {
  vi.spyOn(api, "getKnownIssues").mockResolvedValue(mockIssuesPage);

  const { container } = renderWithClient(<KnowledgeView />);

  await waitFor(() => {
    expect(
      screen.getByText("Desgaste prematuro de cadena"),
    ).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
