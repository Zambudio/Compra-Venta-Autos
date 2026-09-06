import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { expect, test, vi } from "vitest";

import { StatusScreen } from "@/features/auth/status-screen";

function renderStatus(onLogout = vi.fn().mockResolvedValue(undefined)) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData(["system-status"], {
    api: "available",
    postgresql: "available",
    redis: "ready",
  });
  return {
    onLogout,
    ...render(
      <QueryClientProvider client={queryClient}>
        <StatusScreen
          user={{ id: "user-id", email: "owner@example.com", role: "OWNER" }}
          onLogout={onLogout}
          isLoggingOut={false}
        />
      </QueryClientProvider>,
    ),
  };
}

test("muestra el estado real y ejecuta logout", async () => {
  const user = userEvent.setup();
  const { onLogout } = renderStatus();
  expect(
    screen.getByRole("heading", { name: "Foundation operativa" }),
  ).toBeInTheDocument();
  expect(screen.getAllByText("Disponible")).toHaveLength(2);
  expect(screen.getByText("Preparado")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));
  expect(onLogout).toHaveBeenCalledOnce();
});

test("no tiene violaciones de accesibilidad detectables", async () => {
  const { container } = renderStatus();
  expect(await axe(container)).toHaveNoViolations();
});
