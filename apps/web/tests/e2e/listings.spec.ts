import { expect, test } from "@playwright/test";

test("owner syncs the mock catalogue, filters and registers a vehicle", async ({
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

  await page
    .getByRole("button", { name: "Sincronizar catálogo Mock" })
    .click();
  await expect(page.getByRole("status")).toContainText("nuevos");
  await expect(page.getByRole("heading", { name: /SEAT/ }).first()).toBeVisible();

  await page.getByLabel("Marca").fill("Dacia");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page.getByRole("heading", { name: /Dacia/ }).first()).toBeVisible();

  await page.getByRole("button", { name: "Ver detalle" }).first().click();
  await expect(
    page.getByText("Histórico de observaciones"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Volver a la lista" }).click();

  await page.getByRole("button", { name: "Registrar vehículo" }).click();
  await page.getByLabel("Marca").fill("Renault");
  await page.getByLabel("Modelo").fill("Clio");
  await page.getByLabel("Año").fill("2016");
  await page.getByLabel("Kilometraje").fill("85000");
  await page.getByLabel("Precio (€)").fill("6500");
  await page.getByRole("button", { name: "Registrar vehículo" }).click();

  await expect(
    page.getByRole("heading", { name: "Anuncios", level: 1 }),
  ).toBeVisible();
  await page.getByLabel("Marca").fill("Renault");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(
    page.getByRole("heading", { name: /Renault Clio/ }).first(),
  ).toBeVisible();
});
