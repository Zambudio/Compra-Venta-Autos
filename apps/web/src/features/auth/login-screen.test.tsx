import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { LoginScreen } from "@/features/auth/login-screen";

test("renders login screen with branding and private access title", () => {
  render(<LoginScreen onSubmit={vi.fn()} />);

  expect(screen.getByText("MotorScope")).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: "Acceso privado" }),
  ).toBeInTheDocument();
  expect(
    screen.getByText(
      "Gestiona tus oportunidades de vehículos con criterio y trazabilidad.",
    ),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument();
});

test("displays server error alert when provided", () => {
  render(
    <LoginScreen onSubmit={vi.fn()} serverError="Credenciales no válidas" />,
  );

  expect(screen.getByRole("alert")).toHaveTextContent(
    "Credenciales no válidas",
  );
});
