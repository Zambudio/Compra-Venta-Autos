import { beforeEach, expect, test, vi } from "vitest";

import * as api from "./api";

const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

test("getManufacturers calls /knowledge/manufacturers", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "m-1", name: "Peugeot" }],
  });

  const res = await api.getManufacturers();
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/manufacturers",
    expect.objectContaining({ credentials: "include" }),
  );
  expect(res).toEqual([{ id: "m-1", name: "Peugeot" }]);
});

test("getModels passes manufacturerId query param", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "mod-1", name: "208" }],
  });

  await api.getModels("m-1");
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/models?manufacturer_id=m-1",
    expect.anything(),
  );
});

test("getKnownIssues passes filters and pagination", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ items: [], page: 1, page_size: 20, total: 0, has_more: false }),
  });

  await api.getKnownIssues({ component: "TIMING_SYSTEM", severity: "CRITICAL", page: 2 });
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/issues?component=TIMING_SYSTEM&severity=CRITICAL&page=2",
    expect.anything(),
  );
});

test("lookupVehicleReliability encodes query parameters correctly", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      brand: "Peugeot",
      model: "208",
      classification: "BLACKLIST",
      issues_count: 1,
    }),
  });

  await api.lookupVehicleReliability({
    brand: "Peugeot",
    model: "208",
    year: 2016,
    fuelType: "PETROL",
    engineCode: "EB2",
  });

  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/reliability-lookup?brand=Peugeot&model=208&year=2016&fuel_type=PETROL&engine_code=EB2",
    expect.anything(),
  );
});

test("addVehicleMitigation sends POST with CSRF header", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id: "mit-1", mitigation_type: "INVOICE_PROVED_REPLACEMENT" }),
  });
  const res = await api.addVehicleMitigation({
    vehicle_id: "veh-1",
    known_issue_id: "iss-1",
    mitigation_type: "INVOICE_PROVED_REPLACEMENT",
    description: "Factura de sustitución oficial",
  });

  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/mitigations",
    expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "Content-Type": "application/json" }),
    }),
  );
  expect(res.id).toBe("mit-1");
});

test("getGenerations passes modelId correctly", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "gen-1", name: "Gen II" }],
  });

  await api.getGenerations("mod-1");
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/generations?model_id=mod-1",
    expect.anything(),
  );
});

test("getEngines and variants pass query params", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "eng-1", family_code: "EA189" }],
  });

  await api.getEngines({ manufacturerId: "m-1", fuelType: "DIESEL" });
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/engines?manufacturer_id=m-1&fuel_type=DIESEL",
    expect.anything(),
  );

  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "var-1", version_code: "CFCA" }],
  });
  await api.getEngineVariants("eng-1");
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/engine-variants?engine_id=eng-1",
    expect.anything(),
  );
});

test("getTransmissions and getKnownIssue", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "tr-1", code: "MQ250" }],
  });
  await api.getTransmissions();
  expect(mockFetch).toHaveBeenCalledWith("/api/v1/knowledge/transmissions", expect.anything());

  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id: "iss-1", title: "Problema cadena" }),
  });
  await api.getKnownIssue("iss-1");
  expect(mockFetch).toHaveBeenCalledWith("/api/v1/knowledge/issues/iss-1", expect.anything());
});

test("getClassifications and getVehicleMitigations", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ items: [], total: 0 }),
  });
  await api.getClassifications({ status: "BLACKLIST", targetType: "ENGINE", page: 1, pageSize: 10 });
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/classifications?status=BLACKLIST&target_type=ENGINE&page=1&page_size=10",
    expect.anything(),
  );

  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: "mit-1" }],
  });
  await api.getVehicleMitigations("veh-1");
  expect(mockFetch).toHaveBeenCalledWith(
    "/api/v1/knowledge/vehicles/veh-1/mitigations",
    expect.anything(),
  );
});
