import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test } from "vitest";

import { KnownIssueCard } from "./known-issue-card";
import type { KnownIssue } from "./types";

const mockIssue: KnownIssue = {
  id: "iss-1",
  title: "Degradación de correa en baño de aceite",
  description:
    "La correa húmeda se desintegra desprendiendo residuos que taponan la chupona de aceite.",
  component: "TIMING_SYSTEM",
  severity: "CRITICAL",
  frequency: "SYSTEMIC",
  typical_mileage_km: 60000,
  estimated_repair_cost_min: "800.00",
  estimated_repair_cost_max: "3500.00",
  currency: "EUR",
  symptoms: "Aviso de presión de aceite, endurecimiento del pedal de freno",
  prevention: "Comprobar anchura de correa con calibre por el tapón de aceite",
  definitive_repair: "Sustitución de kit de distribución y limpieza de chupona",
  has_recall_campaign: true,
  recall_details: "Alerta Safety Gate A12/01504/20 de la Comisión Europea",
  status: "VERIFIED",
  reviewed_by_user_id: "user-1",
  reviewed_at: "2026-02-01T00:00:00Z",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-02-01T00:00:00Z",
  evidences: [
    {
      id: "ev-1",
      source_id: "src-1",
      component: "TIMING_SYSTEM",
      summary: "Boletín técnico oficial y campaña de llamada a revisión",
      severity: "CRITICAL",
      confidence_score: "0.980",
      verified: true,
      verified_by_user_id: "user-1",
      verified_at: "2026-02-01T00:00:00Z",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-02-01T00:00:00Z",
      source: {
        id: "src-1",
        source_type: "OFFICIAL_RECALL",
        name: "Safety Gate Alerta A12/01504/20",
        url: "https://ec.europa.eu/safety-gate",
        publisher: "Comisión Europea",
        published_at: "2020-11-20T00:00:00Z",
        retrieved_at: "2026-01-01T00:00:00Z",
        trust_level: "A",
        notes: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    },
  ],
};

test("renders known issue card summary and badges", () => {
  render(<KnownIssueCard issue={mockIssue} />);

  expect(
    screen.getByText("Degradación de correa en baño de aceite"),
  ).toBeInTheDocument();
  expect(screen.getByText(/Crítica/i)).toBeInTheDocument();
  expect(screen.getByText(/Campaña Oficial/i)).toBeInTheDocument();
  expect(screen.getByText(/Distribución/i)).toBeInTheDocument();
  expect(screen.getByText(/800/)).toBeInTheDocument();
  expect(screen.getByText(/3\.?500/)).toBeInTheDocument();
});

test("expands details to show symptoms, prevention, and evidences", async () => {
  render(<KnownIssueCard issue={mockIssue} />);

  const expandBtn = screen.getByRole("button", {
    name: /síntomas, prevención y evidencias/i,
  });
  await userEvent.click(expandBtn);

  expect(screen.getByText(/presión de aceite/i)).toBeInTheDocument();
  expect(screen.getByText(/calibre por el tapón/i)).toBeInTheDocument();
  expect(
    screen.getByText(/Safety Gate Alerta A12\/01504\/20/i),
  ).toBeInTheDocument();
  expect(screen.getByText(/Nivel A/i)).toBeInTheDocument();
});

test("known issue card has no accessibility violations", async () => {
  const { container } = render(<KnownIssueCard issue={mockIssue} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
