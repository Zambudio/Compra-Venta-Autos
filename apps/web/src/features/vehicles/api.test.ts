import { afterEach, beforeEach, expect, test, vi } from "vitest";

import {
  computeVehicleMarketEstimate,
  confirmMatchCandidate,
  generateMatchCandidates,
  getMatchCandidates,
  getVehicle,
  getVehicleHistory,
  getVehicles,
  rejectMatchCandidate,
} from "@/features/vehicles/api";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
  document.cookie = "motorscope_csrf=test-token";
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("getVehicles builds query params correctly", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, has_more: false }), {
      status: 200,
    }),
  );

  await getVehicles({ page: 2, pageSize: 10, brand: "SEAT", model: "Ibiza" });

  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/vehicles?page=2&page_size=10&brand=SEAT&model=Ibiza",
    expect.objectContaining({ credentials: "include" }),
  );
});

test("getVehicle fetches detail by id", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ id: "v-1", brand: "SEAT", model: "Ibiza" }), {
      status: 200,
    }),
  );

  const res = await getVehicle("v-1");
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/vehicles/v-1", expect.anything());
  expect(res.id).toBe("v-1");
});

test("getVehicleHistory fetches metrics", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ days_on_market: 15 }), { status: 200 }),
  );

  const res = await getVehicleHistory("v-1");
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/vehicles/v-1/history", expect.anything());
  expect(res.days_on_market).toBe(15);
});

test("computeVehicleMarketEstimate sends POST with CSRF", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ estimated_amount: "5000.00" }), { status: 200 }),
  );

  await computeVehicleMarketEstimate("v-1", 4);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/vehicles/v-1/market-estimate?min_comparables=4",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-CSRF-Token": "test-token" }),
    }),
  );
});

test("getMatchCandidates queries with status and pagination", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 }),
  );

  await getMatchCandidates("PENDING", 1, 20);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/match-candidates?status=PENDING&page=1&page_size=20",
    expect.anything(),
  );
});

test("confirmMatchCandidate sends POST with CSRF", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ candidate_id: "c-1", status: "CONFIRMED", vehicle_id: "v-1" }), {
      status: 200,
    }),
  );

  const res = await confirmMatchCandidate("c-1");
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/match-candidates/c-1/confirm",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-CSRF-Token": "test-token" }),
    }),
  );
  expect(res.status).toBe("CONFIRMED");
});

test("rejectMatchCandidate sends POST with CSRF", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ candidate_id: "c-1", status: "REJECTED" }), { status: 200 }),
  );

  const res = await rejectMatchCandidate("c-1");
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/match-candidates/c-1/reject",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-CSRF-Token": "test-token" }),
    }),
  );
  expect(res.status).toBe("REJECTED");
});

test("generateMatchCandidates triggers scan", async () => {
  const fetchMock = vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ created_candidates: 3 }), { status: 200 }),
  );

  const res = await generateMatchCandidates();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/match-candidates/generate",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-CSRF-Token": "test-token" }),
    }),
  );
  expect(res.created_candidates).toBe(3);
});
