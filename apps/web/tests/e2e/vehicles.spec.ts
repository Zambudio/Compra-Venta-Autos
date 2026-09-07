import { expect, test } from "@playwright/test";

test("owner navigates vehicles catalog, inspects market data and deduplication review", async ({
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

  // Navegar a la sección de Vehículos
  await page.getByRole("button", { name: "Vehículos" }).click();
  await expect(
    page.getByRole("heading", { name: "Vehículos y Mercado", level: 1 }),
  ).toBeVisible();

  // 1. Verificar subpestaña de Deduplicación
  await page.getByRole("button", { name: /Deduplicación/ }).click();
  await expect(
    page.getByRole("heading", { name: "Revisión asistida de duplicados" }),
  ).toBeVisible();

  // Si existe algún candidato pendiente, podemos confirmar o rechazar
  const confirmBtn = page.getByRole("button", { name: "Confirmar unión" }).first();
  if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await confirmBtn.click();
    await page.waitForTimeout(1000);
  }

  // 2. Volver al Catálogo Unificado
  await page.getByRole("button", { name: "Catálogo Unificado" }).click();
  await expect(page.getByLabel("Marca")).toBeVisible();
  await expect(page.getByLabel("Modelo")).toBeVisible();

  // 3. Si hay vehículos en el catálogo, inspeccionar el detalle
  const detailBtn = page.getByRole("button", { name: /Ver detalle/ }).first();
  if (await detailBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await detailBtn.click();
    await expect(page.getByText("Ficha técnica")).toBeVisible();
    await expect(page.getByText("Valoración de Mercado")).toBeVisible();
    await expect(page.getByText("Histórico de Observaciones")).toBeVisible();

    // Volver a la lista
    await page.getByRole("button", { name: "Volver a la lista" }).click();
    await expect(
      page.getByRole("heading", { name: "Vehículos y Mercado", level: 1 }),
    ).toBeVisible();
  }
});
