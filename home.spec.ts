import { expect, test } from "@playwright/test";

test.describe("Home (smoke)", () => {
  test("muestra título, disclaimer y atribución USDA", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1, name: "NutriAI" })).toBeVisible();
    await expect(page.getByText("no sustituye la consulta con un profesional")).toBeVisible();
    await expect(page.getByText("FoodData Central, USDA")).toBeVisible();
  });

  test("reporta el estado del backend", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("backend-status")).toContainText(/API (en línea|no disponible)/);
  });

  test("el enlace 'Saltar al contenido' es accesible por teclado", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Saltar al contenido" })).toBeFocused();
  });
});
