import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test, vi } from "vitest";

import { FilterForm } from "@/features/listings/filter-form";

test("applies typed filters", async () => {
  const user = userEvent.setup();
  const onApply = vi.fn();
  render(<FilterForm onApply={onApply} />);

  await user.type(screen.getByLabelText("Marca"), "SEAT");
  await user.type(screen.getByLabelText("Precio máximo (€)"), "5000");
  await user.selectOptions(screen.getByLabelText("Combustible"), "DIESEL");
  await user.click(screen.getByRole("button", { name: "Aplicar filtros" }));

  expect(onApply).toHaveBeenCalledWith(
    expect.objectContaining({
      brand: "SEAT",
      price_max: 5000,
      fuel_type: "DIESEL",
      page: 1,
    }),
  );
});

test("rejects an inverted year range", async () => {
  const user = userEvent.setup();
  const onApply = vi.fn();
  render(<FilterForm onApply={onApply} />);

  await user.type(screen.getByLabelText("Año desde"), "2020");
  await user.type(screen.getByLabelText("Año hasta"), "2010");
  await user.click(screen.getByRole("button", { name: "Aplicar filtros" }));

  expect(
    screen.getByText("El año máximo no puede ser menor que el mínimo."),
  ).toBeInTheDocument();
  expect(onApply).not.toHaveBeenCalled();
});

test("clear resets to the default sort", async () => {
  const user = userEvent.setup();
  const onApply = vi.fn();
  render(<FilterForm onApply={onApply} />);

  await user.click(screen.getByRole("button", { name: "Limpiar" }));

  expect(onApply).toHaveBeenCalledWith({ sort: "newest", page: 1 });
});

test("has no accessibility violations", async () => {
  const { container } = render(<FilterForm onApply={vi.fn()} />);
  expect(await axe(container)).toHaveNoViolations();
});
