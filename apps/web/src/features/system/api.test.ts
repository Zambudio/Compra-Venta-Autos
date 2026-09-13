import { beforeEach, expect, test, vi } from "vitest";

import {
  checkSourceHealth,
  getSources,
  updateSource,
} from "@/features/system/api";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("uses authenticated source endpoints and CSRF for updates", async () => {
  document.cookie = "motorscope_csrf=csrf-source";
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [],
  } as Response);

  await getSources();
  await checkSourceHealth("wallapop");
  await updateSource("manual", false);

  expect(global.fetch).toHaveBeenNthCalledWith(
    1,
    "/api/v1/sources",
    expect.anything(),
  );
  expect(global.fetch).toHaveBeenNthCalledWith(
    2,
    "/api/v1/sources/wallapop/health",
    expect.anything(),
  );
  expect(global.fetch).toHaveBeenNthCalledWith(
    3,
    "/api/v1/sources/manual",
    expect.objectContaining({
      method: "PATCH",
      headers: expect.objectContaining({ "X-CSRF-Token": "csrf-source" }),
      body: JSON.stringify({ is_active: false }),
    }),
  );
});
