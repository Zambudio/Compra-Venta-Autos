import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/listings/api";
import { ListingsView } from "@/features/listings/listings-view";
import type { Listing, ListingPage } from "@/features/listings/types";
import { renderWithClient } from "@/test/render";

function listing(overrides: Partial<Listing> = {}): Listing {
  return {
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
    description: null,
    image_urls: [],
    status: "ACTIVE",
    first_seen_at: "2026-08-01T00:00:00Z",
    last_seen_at: "2026-08-20T00:00:00Z",
    published_at: null,
    ...overrides,
  };
}

function page(items: Listing[], extra: Partial<ListingPage> = {}): ListingPage {
  return { items, page: 1, page_size: 12, total: items.length, has_more: false, ...extra };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

test("shows a loading state then the results", async () => {
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  renderWithClient(<ListingsView />);

  expect(screen.getByText("Cargando anuncios…")).toBeInTheDocument();
  expect(await screen.findByText("SEAT Ibiza")).toBeInTheDocument();
  expect(screen.getByText("1 anuncios · página 1")).toBeInTheDocument();
});

test("shows the empty state", async () => {
  vi.spyOn(api, "getListings").mockResolvedValue(page([]));
  renderWithClient(<ListingsView />);

  expect(
    await screen.findByText(/No hay anuncios que coincidan/),
  ).toBeInTheDocument();
});

test("shows the error state", async () => {
  vi.spyOn(api, "getListings").mockRejectedValue(new Error("boom"));
  renderWithClient(<ListingsView />);

  expect(
    await screen.findByText("No se pudieron cargar los anuncios."),
  ).toBeInTheDocument();
});

test("syncs the mock catalogue and reports the result", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  vi.spyOn(api, "syncSource").mockResolvedValue({
    id: "run-1",
    source_key: "mock",
    status: "SUCCESS",
    mode: "sync",
    listings_seen: 36,
    listings_created: 36,
    listings_updated: 0,
    snapshots_created: 36,
    error_summary: null,
    started_at: null,
    finished_at: null,
    created_at: "2026-09-06T00:00:00Z",
  });
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.click(
    screen.getByRole("button", { name: "Sincronizar catálogo Mock" }),
  );

  expect(
    await screen.findByText(/Sincronización completada: 36 nuevos/),
  ).toBeInTheDocument();
});

test("opens the detail view for a listing", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  vi.spyOn(api, "getListing").mockResolvedValue({
    ...listing(),
    snapshots: [
      {
        observed_at: "2026-08-20T00:00:00Z",
        price_amount: "2800.00",
        price_currency: "EUR",
        mileage_km: 168000,
        status: "ACTIVE",
      },
    ],
  });
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.click(screen.getByRole("button", { name: "Ver detalle" }));

  expect(
    await screen.findByRole("button", { name: "Volver a la lista" }),
  ).toBeInTheDocument();
});

test("paginates through results", async () => {
  const user = userEvent.setup();
  const getListings = vi
    .spyOn(api, "getListings")
    .mockImplementation((filters) =>
      Promise.resolve(
        page([listing({ id: `listing-${filters.page ?? 1}` })], {
          page: filters.page ?? 1,
          has_more: (filters.page ?? 1) < 2,
          total: 24,
        }),
      ),
    );
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.click(screen.getByRole("button", { name: "Siguiente" }));
  await waitFor(() =>
    expect(getListings).toHaveBeenCalledWith(expect.objectContaining({ page: 2 })),
  );

  await user.click(screen.getByRole("button", { name: "Anterior" }));
  await waitFor(() =>
    expect(getListings).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1 })),
  );
});

test("reports a sync failure", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  vi.spyOn(api, "syncSource").mockRejectedValue(new Error("boom"));
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.click(
    screen.getByRole("button", { name: "Sincronizar catálogo Mock" }),
  );

  expect(await screen.findByText(/Error inesperado al sincronizar/)).toBeInTheDocument();
});

test("applies a filter from the filter form", async () => {
  const user = userEvent.setup();
  const getListings = vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.type(screen.getByLabelText("Marca"), "SEAT");
  await user.click(screen.getByRole("button", { name: "Aplicar filtros" }));

  await waitFor(() =>
    expect(getListings).toHaveBeenCalledWith(
      expect.objectContaining({ brand: "SEAT", page: 1 }),
    ),
  );
});

test("opens the manual registration form", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");

  await user.click(screen.getByRole("button", { name: "Registrar vehículo" }));

  expect(
    await screen.findByRole("form", { name: "Registrar vehículo manualmente" }),
  ).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  vi.spyOn(api, "getListings").mockResolvedValue(page([listing()]));
  const { container } = renderWithClient(<ListingsView />);
  await screen.findByText("SEAT Ibiza");
  await waitFor(async () => {
    expect(await axe(container)).toHaveNoViolations();
  });
});
