import { expect, test } from "@playwright/test";

test("home page renders core panels", async ({ page }) => {
   await page.addInitScript(() => {
     (window as Window & { __ARXOS_DISABLE_WEBGL__?: boolean }).__ARXOS_DISABLE_WEBGL__ = true;
   });
   await page.goto("/");
   await page.waitForLoadState("networkidle");
 
 
  await expect(page.getByRole("button", { name: /Command Palette/i })).toBeVisible();
  await expect(page.getByTestId("panel-floor-plan")).toBeVisible();
  await expect(page.getByTestId("panel-collaboration")).toBeVisible();
  await expect(page.getByTestId("panel-git")).toBeVisible();
  await expect(page.getByTestId("panel-webgl")).toBeVisible();
  await expect(page.getByTestId("panel-ifc")).toBeVisible();
});
