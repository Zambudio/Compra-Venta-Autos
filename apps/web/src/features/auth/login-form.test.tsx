import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test, vi } from "vitest";

import { LoginForm } from "@/features/auth/login-form";

test("valida el formulario mediante labels accesibles", async () => {
  const user = userEvent.setup();
  const submit = vi.fn();
  render(<LoginForm onSubmit={submit} />);

  await user.type(
    screen.getByLabelText("Correo electrónico"),
    "correo-invalido",
  );
  await user.type(screen.getByLabelText("Contraseña"), "corta");
  await user.click(screen.getByRole("button", { name: "Entrar" }));

  expect(
    await screen.findByText("Introduce un correo electrónico válido."),
  ).toBeInTheDocument();
  expect(
    screen.getByText("La contraseña debe tener al menos 12 caracteres."),
  ).toBeInTheDocument();
  expect(submit).not.toHaveBeenCalled();
});

test("envía valores válidos y permite mostrar la contraseña", async () => {
  const user = userEvent.setup();
  const submit = vi.fn().mockResolvedValue(undefined);
  render(<LoginForm onSubmit={submit} />);

  await user.type(
    screen.getByLabelText("Correo electrónico"),
    "owner@example.com",
  );
  await user.type(screen.getByLabelText("Contraseña"), "a secure password");
  await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
  expect(screen.getByLabelText("Contraseña")).toHaveAttribute("type", "text");
  await user.click(screen.getByRole("button", { name: "Entrar" }));

  expect(submit).toHaveBeenCalledWith(
    { email: "owner@example.com", password: "a secure password" },
    expect.anything(),
  );
});

test("no tiene violaciones de accesibilidad detectables", async () => {
  const { container } = render(
    <LoginForm onSubmit={vi.fn()} serverError="Credenciales inválidas" />,
  );
  expect(await axe(container)).toHaveNoViolations();
});
