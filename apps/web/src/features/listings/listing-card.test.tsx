import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import { ListingCard } from "@/features/listings/listing-card";
import type { Listing } from "@/features/listings/types";

function listing(overrides: Partial<Listing> = {}): Listing {
  return {
    id: "l1",
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

test("renders key data and calls onOpen", async () => {
  const user = userEvent.setup();
  const onOpen = vi.fn();
  render(<ListingCard listing={listing()} onOpen={onOpen} />);

  expect(
    screen.getByRole("heading", { name: /SEAT Ibiza/ }),
  ).toBeInTheDocument();
  expect(screen.getByText(/168.000 km/)).toBeInTheDocument();
  expect(screen.getByText("Particular")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Ver detalle" }));
  expect(onOpen).toHaveBeenCalledWith("l1");
});

test("hides the original-ad link and shows a manual badge for manual listings", () => {
  render(
    <ListingCard
      listing={listing({
        url: null,
        source_key: "manual",
        trim: null,
        seller_type: "DEALER",
      })}
      onOpen={vi.fn()}
    />,
  );

  expect(
    screen.queryByRole("link", { name: "Ver anuncio original" }),
  ).not.toBeInTheDocument();
  expect(screen.getByText("Manual")).toBeInTheDocument();
  expect(screen.getByText("Profesional")).toBeInTheDocument();
});
