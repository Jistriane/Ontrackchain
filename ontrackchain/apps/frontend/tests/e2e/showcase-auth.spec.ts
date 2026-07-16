import { expect, test } from "@playwright/test";

import { loginIntoShowcase, showcaseOnly } from "./showcase-helpers";

test.describe("standalone showcase auth", () => {
  test.skip(!showcaseOnly, "requer TEST_SHOWCASE_MODE=true");

  test("login do showcase leva ao dashboard", async ({ page }) => {
    await loginIntoShowcase(page);
    await expect(page.getByText("Casos recentes")).toBeVisible();
  });
});
