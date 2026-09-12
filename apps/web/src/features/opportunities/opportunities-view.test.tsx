import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/opportunities/api";
import { OpportunitiesView } from "@/features/opportunities/opportunities-view";
import {
  
  mockOpportunityPage,
} from "@/features/opportunities/test-fixtures";
import { renderWithClient } from "@/test/render";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders opportunities catalog and allows filtering", async () => {
  const getOppsSpy = vi
    .spyOn(api, "getOpportunities")
    .mockResolvedValue(mockOpportunityPage);

  renderWithClient(<OpportunitiesView />);

  // Esperar a que cargue la lista
  await waitFor(() => {
    expect(screen.getByText("SEAT Ibiza 1.9 TDI")).toBeInTheDocument();
  });

  // KPI y cabecera
  expect(screen.getByText("Mesa de Oportunidades y Scoring")).toBeInTheDocument();
  expect(screen.getByText("Oportunidades en Vista")).toBeInTheDocument();

  // Filtrar por estado
  const statusSelect = screen.getByLabelText("Filtrar por estado");
  await userEvent.selectOptions(statusSelect, "VALIDATED");

  expect(getOppsSpy).toHaveBeenCalledWith(
    expect.objectContaining({ status: "VALIDATED" }),
  );
});

test("renders empty state when no opportunities found", async () => {
  vi.spyOn(api, "getOpportunities").mockResolvedValue({
    items: [],
    page: 1,
    page_size: 15,
    total: 0,
    has_more: false,
  });

  renderWithClient(<OpportunitiesView />);

  await waitFor(() => {
    expect(
      screen.getByText("No se han encontrado oportunidades"),
    ).toBeInTheDocument();
  });
});

test("opportunities view has no accessibility violations", async () => {
  vi.spyOn(api, "getOpportunities").mockResolvedValue(mockOpportunityPage);

  const { container } = renderWithClient(<OpportunitiesView />);

  await waitFor(() => {
    expect(screen.getByText("SEAT Ibiza 1.9 TDI")).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
