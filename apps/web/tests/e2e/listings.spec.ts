import { expect, test } from "@playwright/test";

test("owner registers a vehicle manually and views it", async ({
  page,
}) => {
  const email = process.env.E2E_OWNER_EMAIL;
  const password = process.env.E2E_OWNER_PASSWORD;
  test.skip(
    !email || !password,
    "E2E_OWNER_EMAIL and E2E_OWNER_PASSWORD are required",
  );

  await page.goto("/");
  await page.getByLabel("Correo electrónico", { exact: true }).fill(email!);
  await page.getByLabel("Contraseña", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByRole("heading", { name: "Anuncios", level: 1 }),
  ).toBeVisible();

  // Register a vehicle manually (always works, no external API dependency)
  const testModel = `Ibiza-${Date.now().toString(36)}`;
  await page.getByRole("button", { name: "Registrar vehículo" }).click();
  await page.getByLabel("Marca").fill("SEAT");
  await page.getByLabel("Modelo").fill(testModel);
  await page.getByLabel("Año").fill("2014");
  await page.getByLabel("Kilometraje").fill("168000");
  await page.getByLabel("Precio (€)").fill("2800");
  await page.getByRole("button", { name: "Registrar vehículo" }).click();

  await expect(
    page.getByRole("heading", { name: /SEAT/ }).first(),
  ).toBeVisible();

  // View details
  await page.getByRole("button", { name: "Ver detalle" }).first().click();
  await expect(page.getByText("Histórico de observaciones")).toBeVisible();

  // Test filtering
  await page.getByRole("button", { name: "Volver a la lista" }).click();
  await page.getByLabel("Marca").fill("SEAT");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(
    page.getByRole("heading", { name: /SEAT/ }).first(),
  ).toBeVisible();
});
