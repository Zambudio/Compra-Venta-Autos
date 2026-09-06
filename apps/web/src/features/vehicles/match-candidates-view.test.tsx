import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/vehicles/api";
import { MatchCandidatesView } from "@/features/vehicles/match-candidates-view";
import type { MatchCandidate, MatchCandidatePage } from "@/features/vehicles/types";
import { renderWithClient } from "@/test/render";

const mockCandidate: MatchCandidate = {
  id: "cand-1",
  listing_a_id: "la-1",
  listing_b_id: "lb-1",
  confidence_score: "0.850",
  match_reasons: { brand: 1.0, model: 1.0, year: 0.9 },
  status: "PENDING",
  decided_by_user_id: null,
  decided_at: null,
  created_at: "2026-02-01T00:00:00Z",
  listing_a: {
    id: "la-1",
    source_id: "s-1",
    external_id: "ext-a",
    brand: "Ford",
    model: "Focus",
    year: 2017,
    mileage_km: 95000,
    price_amount: "8500.00",
    price_currency: "EUR",
    province: "Valencia",
    status: "ACTIVE",
    image_urls: [],
  },
  listing_b: {
    id: "lb-1",
    source_id: "s-2",
    external_id: "ext-b",
    brand: "Ford",
    model: "Focus",
    year: 2017,
    mileage_km: 96000,
    price_amount: "8400.00",
    price_currency: "EUR",
    province: "Castellón",
    status: "ACTIVE",
    image_urls: [],
  },
};

const mockPage: MatchCandidatePage = {
  items: [mockCandidate],
  page: 1,
  page_size: 20,
  total: 1,
  has_more: false,
};

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders candidate card and allows confirming match", async () => {
  vi.spyOn(api, "getMatchCandidates").mockResolvedValue(mockPage);
  const confirmSpy = vi.spyOn(api, "confirmMatchCandidate").mockResolvedValue({
    candidate_id: "cand-1",
    status: "CONFIRMED",
    vehicle_id: "veh-new",
  });

  renderWithClient(<MatchCandidatesView />);

  await waitFor(() => {
    expect(screen.getByText(/Similitud 85%/i)).toBeInTheDocument();
  });

  expect(screen.getByText(/ext-a.*Valencia/)).toBeInTheDocument();
  expect(screen.getByText(/ext-b.*Castellón/)).toBeInTheDocument();

  const confirmBtn = screen.getByRole("button", { name: /confirmar coincidencia cand-1/i });
  await userEvent.click(confirmBtn);

  expect(confirmSpy).toHaveBeenCalledWith("cand-1");
  await waitFor(() => {
    expect(screen.getByText(/Emparejamiento confirmado con éxito/i)).toBeInTheDocument();
  });
});

test("allows rejecting candidate match", async () => {
  vi.spyOn(api, "getMatchCandidates").mockResolvedValue(mockPage);
  const rejectSpy = vi.spyOn(api, "rejectMatchCandidate").mockResolvedValue({
    candidate_id: "cand-1",
    status: "REJECTED",
  });

  renderWithClient(<MatchCandidatesView />);

  await waitFor(() => {
    expect(screen.getByText(/Similitud 85%/i)).toBeInTheDocument();
  });

  const rejectBtn = screen.getByRole("button", { name: /descartar coincidencia cand-1/i });
  await userEvent.click(rejectBtn);

  expect(rejectSpy).toHaveBeenCalledWith("cand-1");
  await waitFor(() => {
    expect(screen.getByText(/Candidato descartado/i)).toBeInTheDocument();
  });
});

test("allows scanning for duplicates", async () => {
  vi.spyOn(api, "getMatchCandidates").mockResolvedValue({ ...mockPage, items: [], total: 0 });
  const scanSpy = vi.spyOn(api, "generateMatchCandidates").mockResolvedValue({
    created_candidates: 2,
  });

  renderWithClient(<MatchCandidatesView />);

  await waitFor(() => {
    expect(screen.getByText(/Cola de revisión al día/i)).toBeInTheDocument();
  });

  const scanBtn = screen.getByRole("button", { name: /escanear duplicados/i });
  await userEvent.click(scanBtn);

  expect(scanSpy).toHaveBeenCalled();
  await waitFor(() => {
    expect(screen.getByText(/Se han detectado 2 nuevos candidatos/i)).toBeInTheDocument();
  });
});

test("match candidates view has no accessibility violations", async () => {
  vi.spyOn(api, "getMatchCandidates").mockResolvedValue(mockPage);
  const { container } = renderWithClient(<MatchCandidatesView />);

  await waitFor(() => {
    expect(screen.getByText(/Similitud 85%/i)).toBeInTheDocument();
  });

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
