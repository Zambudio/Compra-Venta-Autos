import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test, vi } from "vitest";

import { OpportunityCard } from "@/features/opportunities/opportunity-card";
import { mockOpportunity } from "@/features/opportunities/test-fixtures";

test("renders opportunity card summary, expands detail and triggers status change", async () => {
  const onStatusChange = vi.fn().mockResolvedValue(undefined);
  render(
    <OpportunityCard
      opportunity={mockOpportunity}
      onStatusChange={onStatusChange}
    />,
  );

  // Título
  expect(screen.getByText("SEAT Ibiza 1.9 TDI")).toBeInTheDocument();
  // Score badge
  expect(screen.getByText(/83 \/ 100/)).toBeInTheDocument();
  // Presión
  expect(screen.getByText("Presión media")).toBeInTheDocument();
  // Select de estado
  const select = screen.getByLabelText("Estado:");
  expect(select).toHaveValue("IDENTIFIED");

  // Cambiar estado
  await userEvent.selectOptions(select, "VALIDATED");
  expect(onStatusChange).toHaveBeenCalledWith(mockOpportunity.id, "VALIDATED");

  // Expandir análisis detallado
  const expandBtn = screen.getByRole("button", {
    name: /ver desglose detallado/i,
  });
  expect(
    screen.queryByText("Scoring Multicriterio Determinista"),
  ).not.toBeInTheDocument();
  await userEvent.click(expandBtn);

  // Desglose visible tras click
  expect(
    screen.getByText("Scoring Multicriterio Determinista"),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Valoración Económica y Proyección de Margen"),
  ).toBeInTheDocument();

  // Colapsar
  const collapseBtn = screen.getByRole("button", { name: /ocultar análisis/i });
  await userEvent.click(collapseBtn);
  expect(
    screen.queryByText("Scoring Multicriterio Determinista"),
  ).not.toBeInTheDocument();
});

test("opportunity card has no accessibility violations in collapsed and expanded state", async () => {
  const { container } = render(
    <OpportunityCard opportunity={mockOpportunity} />,
  );
  let results = await axe(container);
  expect(results).toHaveNoViolations();

  // Expandir y verificar de nuevo accesibilidad
  const expandBtn = screen.getByRole("button", {
    name: /ver desglose detallado/i,
  });
  await userEvent.click(expandBtn);
  results = await axe(container);
  expect(results).toHaveNoViolations();
});
