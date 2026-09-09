import { render, screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { expect, test } from "vitest";

import { OpportunityScoreBreakdown } from "@/features/opportunities/opportunity-score-breakdown";
import { mockOpportunityScore } from "@/features/opportunities/test-fixtures";

test("renders score breakdown with all 9 components and total score", () => {
  render(<OpportunityScoreBreakdown score={mockOpportunityScore} />);

  // Título de la sección
  expect(screen.getByText("Scoring Multicriterio Determinista")).toBeInTheDocument();
  // Score total formateado
  expect(screen.getByText(/83 \/ 100/)).toBeInTheDocument();
  // Nivel de confianza
  expect(screen.getByText(/Alta \(85%\)/)).toBeInTheDocument();

  // Componentes clave presentes
  expect(screen.getByText("Precio vs Mercado")).toBeInTheDocument();
  expect(screen.getByText("Fiabilidad Modelo")).toBeInTheDocument();
  expect(screen.getByText("Liquidez de Venta")).toBeInTheDocument();
  expect(screen.getByText("Riesgo Mecánico")).toBeInTheDocument();
  expect(screen.getByText("Kilometraje")).toBeInTheDocument();
  expect(screen.getByText("Antigüedad")).toBeInTheDocument();
  expect(screen.getByText("Historial de Precios")).toBeInTheDocument();
  expect(screen.getByText("Estado General")).toBeInTheDocument();
  expect(screen.getByText("Días en Venta")).toBeInTheDocument();

  // Justificaciones textuales presentes
  expect(
    screen.getByText(/Precio 22% por debajo de estimación de mercado/),
  ).toBeInTheDocument();
});

test("renders empty state when score is null", () => {
  render(<OpportunityScoreBreakdown score={null} />);
  expect(
    screen.getByText("No hay puntuación calculada para esta oportunidad todavía."),
  ).toBeInTheDocument();
});

test("score breakdown has no accessibility violations", async () => {
  const { container } = render(
    <OpportunityScoreBreakdown score={mockOpportunityScore} />,
  );
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
