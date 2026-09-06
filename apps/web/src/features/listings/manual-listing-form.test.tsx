import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { beforeEach, expect, test, vi } from "vitest";

import * as api from "@/features/listings/api";
import { ManualListingForm } from "@/features/listings/manual-listing-form";
import { ApiError } from "@/lib/api";
import { renderWithClient } from "@/test/render";

beforeEach(() => {
  vi.restoreAllMocks();
});

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Marca"), "Seat");
  await user.type(screen.getByLabelText("Modelo"), "Ibiza");
  await user.type(screen.getByLabelText("Año"), "2014");
  await user.type(screen.getByLabelText("Kilometraje"), "120000");
  await user.type(screen.getByLabelText("Precio (€)"), "4200");
}

test("validates required fields", async () => {
  const user = userEvent.setup();
  renderWithClient(
    <ManualListingForm onCreated={vi.fn()} onCancel={vi.fn()} />,
  );

  await user.click(screen.getByRole("button", { name: "Registrar vehículo" }));

  expect(screen.getByText("La marca es obligatoria.")).toBeInTheDocument();
  expect(screen.getByText("El modelo es obligatorio.")).toBeInTheDocument();
});

test("submits a valid vehicle and calls onCreated", async () => {
  const user = userEvent.setup();
  const onCreated = vi.fn();
  const create = vi
    .spyOn(api, "createManualListing")
    .mockResolvedValue({} as never);
  renderWithClient(
    <ManualListingForm onCreated={onCreated} onCancel={vi.fn()} />,
  );

  await fillValidForm(user);
  await user.click(screen.getByRole("button", { name: "Registrar vehículo" }));

  expect(create).toHaveBeenCalled();
  expect(create.mock.calls[0]?.[0]).toMatchObject({
    brand: "Seat",
    model: "Ibiza",
    price_amount: "4200",
    year: 2014,
    mileage_km: 120000,
  });
  expect(onCreated).toHaveBeenCalled();
});

test("shows a friendly message on a duplicate", async () => {
  const user = userEvent.setup();
  vi.spyOn(api, "createManualListing").mockRejectedValue(
    new ApiError(409, "listing_already_exists", "dup"),
  );
  renderWithClient(
    <ManualListingForm onCreated={vi.fn()} onCancel={vi.fn()} />,
  );

  await fillValidForm(user);
  await user.click(screen.getByRole("button", { name: "Registrar vehículo" }));

  expect(
    await screen.findByText("Ese vehículo ya está registrado manualmente."),
  ).toBeInTheDocument();
});

test("cancel calls onCancel", async () => {
  const user = userEvent.setup();
  const onCancel = vi.fn();
  renderWithClient(
    <ManualListingForm onCreated={vi.fn()} onCancel={onCancel} />,
  );

  await user.click(screen.getByRole("button", { name: "Cancelar" }));

  expect(onCancel).toHaveBeenCalled();
});

test("has no accessibility violations", async () => {
  const { container } = renderWithClient(
    <ManualListingForm onCreated={vi.fn()} onCancel={vi.fn()} />,
  );
  expect(await axe(container)).toHaveNoViolations();
});
