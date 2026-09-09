import { render, screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { expect, test } from "vitest";

import { OpportunityValuationPanel } from "@/features/opportunities/opportunity-valuation-panel";
import { mockOpportunity } from "@/features/opportunities/test-fixtures";

test("renders valuation panel with financial intervals and cost breakdown", () => {
  render(<OpportunityValuationPanel opportunity={mockOpportunity} />);

  // Título
  expect(
    screen.getByText("Valoración Económica y Proyección de Margen"),
  ).toBeInTheDocument();

  // Presión del vendedor
  expect(screen.getByText("Presión media")).toBeInTheDocument();

  // Precios principales
  expect(screen.getByText("Precio Pedido (Asking)")).toBeInTheDocument();
  expect(screen.getByText("Venta Rápida Proyectada")).toBeInTheDocument();
  expect(screen.getByText("Compra Objetivo Sugerida")).toBeInTheDocument();

  // Estructura de costes
  expect(screen.getByText(/ITP \(4% mod\.\):/)).toBeInTheDocument();
  expect(screen.getByText(/Tasa DGT \(55,70€\):/)).toBeInTheDocument();
  expect(screen.getByText(/Coste Preparación:/)).toBeInTheDocument();
  expect(screen.getByText(/Reparaciones Previstas:/)).toBeInTheDocument();

  // Factores de negociación
  expect(screen.getByText(/20 días en mercado/)).toBeInTheDocument();
  expect(
    screen.getByText(/Bajada de precio acumulada de 200 € \(-10.5%\)/),
  ).toBeInTheDocument();
});

test("valuation panel has no accessibility violations", async () => {
  const { container } = render(
    <OpportunityValuationPanel opportunity={mockOpportunity} />,
  );
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
