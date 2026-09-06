import { expect, test } from "@playwright/test";

test("owner can login, inspect Foundation status and logout", async ({
  page,
}) => {
  const email = process.env.E2E_OWNER_EMAIL;
  const password = process.env.E2E_OWNER_PASSWORD;
  test.skip(
    !email || !password,
    "E2E_OWNER_EMAIL and E2E_OWNER_PASSWORD are required",
  );

  await page.goto("/");
  await page.getByLabel("Correo electrónico").fill(email!);
  await page.getByLabel("Contraseña").fill(password!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByRole("heading", { name: "Anuncios", level: 1 }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Estado" }).click();
  await expect(
    page.getByRole("heading", { name: "Foundation operativa" }),
  ).toBeVisible();
  await expect(page.getByText("PostgreSQL")).toBeVisible();
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(
    page.getByRole("heading", { name: "Acceso privado" }),
  ).toBeVisible();
});
