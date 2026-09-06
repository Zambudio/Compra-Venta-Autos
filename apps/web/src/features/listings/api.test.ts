import { afterEach, beforeEach, expect, test, vi } from "vitest";

import {
  createManualListing,
  getListing,
  getListings,
  getSources,
  syncSource,
} from "@/features/listings/api";

function mockFetch(payload: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => payload,
  } as Response);
  global.fetch = fetchMock;
  return fetchMock;
}

beforeEach(() => vi.restoreAllMocks());
afterEach(() => vi.restoreAllMocks());

test("getListings serialises filters into query params", async () => {
  const fetchMock = mockFetch({ items: [], page: 1, page_size: 12, total: 0, has_more: false });

  await getListings({
    brand: "SEAT",
    year_min: 2010,
    source: ["mock", "manual"],
    sort: "price_asc",
    page: 2,
  });

  const url = fetchMock.mock.calls[0]?.[0] as string;
  expect(url).toContain("/listings?");
  expect(url).toContain("brand=SEAT");
  expect(url).toContain("year_min=2010");
  expect(url).toContain("source=mock");
  expect(url).toContain("source=manual");
  expect(url).toContain("sort=price_asc");
});

test("getListings omits empty filters", async () => {
  const fetchMock = mockFetch({ items: [], page: 1, page_size: 12, total: 0, has_more: false });

  await getListings({ brand: "", sort: "newest" });

  expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/listings?sort=newest");
});

test("getListing requests a single listing", async () => {
  const fetchMock = mockFetch({ id: "l1", snapshots: [] });

  await getListing("l1");

  expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/listings/l1");
});

test("getSources requests the catalogue", async () => {
  const fetchMock = mockFetch([]);
  await getSources();
  expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/sources");
});

test("syncSource posts with the CSRF header", async () => {
  document.cookie = "motorscope_csrf=csrf-token";
  const fetchMock = mockFetch({ id: "run-1", status: "SUCCESS" });

  await syncSource("mock");

  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/sources/mock/sync",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
    }),
  );
});

test("createManualListing posts the vehicle payload", async () => {
  document.cookie = "motorscope_csrf=csrf-token";
  const fetchMock = mockFetch({ id: "l1" });

  await createManualListing({
    brand: "Seat",
    model: "Ibiza",
    year: 2014,
    mileage_km: 120000,
    price_amount: "4200",
    fuel_type: "DIESEL",
    transmission: "MANUAL",
    seller_type: "PRIVATE",
  });

  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/listings/manual",
    expect.objectContaining({ method: "POST" }),
  );
});
