import { expect, test } from "@playwright/test";

test("command palette opens with keyboard shortcut", async ({ page }) => {
  await page.addInitScript(() => {
    (window as Window & { __ARXOS_DISABLE_WEBGL__?: boolean }).__ARXOS_DISABLE_WEBGL__ = true;
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");

  await expect(page.getByRole("button", { name: /Command Palette/i })).toBeVisible();

  await page.keyboard.press("Meta+k");
  await page.waitForTimeout(300);

  const paletteInput = page.locator('input[placeholder="Type a command..."]');
  await expect(paletteInput).toBeVisible();
  await expect(paletteInput).toBeFocused();
});

test("command palette accepts search input", async ({ page }) => {
  await page.addInitScript(() => {
    (window as Window & { __ARXOS_DISABLE_WEBGL__?: boolean }).__ARXOS_DISABLE_WEBGL__ = true;
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");

  await page.keyboard.press("Meta+k");
  await page.waitForTimeout(300);

  const paletteInput = page.locator('input[placeholder="Type a command..."]');
  await expect(paletteInput).toBeVisible();

  await paletteInput.fill("version");
  await page.waitForTimeout(200);

  await expect(paletteInput).toHaveValue("version");
});

test("command console is visible in layout", async ({ page }) => {
  await page.addInitScript(() => {
    (window as Window & { __ARXOS_DISABLE_WEBGL__?: boolean }).__ARXOS_DISABLE_WEBGL__ = true;
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");

  const consoleHeader = page.locator("text=Console");
  await expect(consoleHeader).toBeVisible();

  const clearButton = page.locator('button:has-text("Clear")');
  await expect(clearButton).toBeVisible();
});
