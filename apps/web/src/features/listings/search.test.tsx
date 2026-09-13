import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/listings/api";
import { LiveListingSearch } from "@/features/listings/live-search";
import { renderWithClient } from "@/test/render";
import { ApiError } from "@/lib/api";

beforeEach(() => vi.restoreAllMocks());

test("searches Wallapop and renders authentic listing fields", async () => {
  const user = userEvent.setup();
  const search = vi.spyOn(api, "searchListings").mockResolvedValue({
    total: 1,
    query: "BMW 320",
    filters: { source: "wallapop" },
    listings: [
      {
        id: "w-1",
        title: "BMW 320d Touring",
        description: "Historial completo",
        price: "12500",
        location: "Madrid",
        images: ["https://img.example/w-1.jpg"],
        seller: { name: "Ana", rating: 4.9, url: null },
        url: "https://es.wallapop.com/item/bmw-320d-w-1",
        posted_at: "2026-09-12T10:30:00Z",
        source_key: "wallapop",
      },
    ],
  });
  renderWithClient(<LiveListingSearch />);

  await user.type(screen.getByLabelText("Buscar en Wallapop"), "BMW 320");
  await user.click(screen.getByRole("button", { name: "Buscar ahora" }));

  expect(await screen.findByText("BMW 320d Touring")).toBeInTheDocument();
  expect(screen.getByText("12.500 €")).toBeInTheDocument();
  expect(screen.getByText("Madrid")).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: "Abrir en Wallapop" }),
  ).toHaveAttribute("href", "https://es.wallapop.com/item/bmw-320d-w-1");
  expect(search).toHaveBeenCalledWith("BMW 320", {});
});

test("explains when the Wallapop connector is disabled", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "searchListings").mockRejectedValue(
    new ApiError(503, "source_disabled", "disabled"),
  );
  renderWithClient(<LiveListingSearch />);

  await user.type(screen.getByLabelText("Buscar en Wallapop"), "Audi A4");
  await user.click(screen.getByRole("button", { name: "Buscar ahora" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Activa Wallapop en Configuración",
  );
});

test("has no accessibility violations", async () => {
  const { container } = renderWithClient(<LiveListingSearch />);
  expect(await axe(container)).toHaveNoViolations();
});
