import { expect, test } from "vitest";

import { formatDate, formatKm, formatPrice } from "@/features/listings/format";

test("formats EUR prices without decimals", () => {
  expect(formatPrice("2800.00", "EUR")).toContain("2800");
  expect(formatPrice("2800.00", "EUR")).toContain("€");
});

test("formats non-EUR prices with the code", () => {
  expect(formatPrice("2800", "USD")).toBe("2800 USD");
});

test("falls back to raw value when amount is not numeric", () => {
  expect(formatPrice("n/a", "EUR")).toBe("n/a EUR");
});

test("formats kilometres with a unit", () => {
  expect(formatKm(168000)).toContain("km");
  expect(formatKm(168000)).toMatch(/168/);
});

test("formats dates in Spanish locale", () => {
  expect(formatDate("2026-08-20T00:00:00Z")).toMatch(/2026/);
});
