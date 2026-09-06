import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/listings/api";
import { ListingDetailPanel } from "@/features/listings/listing-detail";
import type { ListingDetail } from "@/features/listings/types";
import { renderWithClient } from "@/test/render";

const detail: ListingDetail = {
  id: "listing-1",
  source_key: "mock",
  external_id: "mock-0001",
  url: "https://mock.local/1",
  brand: "SEAT",
  model: "Ibiza",
  generation: null,
  trim: "1.4 TDI",
  engine_code: null,
  power_kw: 66,
  fuel_type: "DIESEL",
  transmission: "MANUAL",
  year: 2013,
  mileage_km: 168000,
  price_amount: "2800.00",
  price_currency: "EUR",
  location: null,
  province: "Murcia",
  seller_type: "PRIVATE",
  description: "Distribución hecha.",
  image_urls: [],
  status: "ACTIVE",
  first_seen_at: "2026-08-01T00:00:00Z",
  last_seen_at: "2026-08-20T00:00:00Z",
  published_at: null,
  snapshots: [
    {
      observed_at: "2026-08-20T00:00:00Z",
      price_amount: "2800.00",
      price_currency: "EUR",
      mileage_km: 168000,
      status: "ACTIVE",
    },
    {
      observed_at: "2026-09-01T00:00:00Z",
      price_amount: "2500.00",
      price_currency: "EUR",
      mileage_km: 168500,
      status: "ACTIVE",
    },
  ],
};

beforeEach(() => {
  vi.restoreAllMocks();
});

test("renders the vehicle and its price history", async () => {
  vi.spyOn(api, "getListing").mockResolvedValue(detail);
  renderWithClient(<ListingDetailPanel listingId="listing-1" onBack={vi.fn()} />);

  expect(
    await screen.findByRole("heading", { name: "SEAT Ibiza" }),
  ).toBeInTheDocument();
  expect(screen.getByText("Histórico de observaciones")).toBeInTheDocument();
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
});

test("calls onBack", async () => {
  const user = userEvent.setup();
  const onBack = vi.fn();
  vi.spyOn(api, "getListing").mockResolvedValue(detail);
  renderWithClient(<ListingDetailPanel listingId="listing-1" onBack={onBack} />);
  await screen.findByRole("heading", { name: "SEAT Ibiza" });

  await user.click(screen.getByRole("button", { name: "Volver a la lista" }));

  expect(onBack).toHaveBeenCalled();
});

test("shows an error message on failure", async () => {
  vi.spyOn(api, "getListing").mockRejectedValue(new Error("nope"));
  renderWithClient(<ListingDetailPanel listingId="listing-1" onBack={vi.fn()} />);

  expect(
    await screen.findByText("No se pudo cargar el anuncio."),
  ).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  vi.spyOn(api, "getListing").mockResolvedValue(detail);
  const { container } = renderWithClient(
    <ListingDetailPanel listingId="listing-1" onBack={vi.fn()} />,
  );
  await screen.findByRole("heading", { name: "SEAT Ibiza" });
  expect(await axe(container)).toHaveNoViolations();
});
