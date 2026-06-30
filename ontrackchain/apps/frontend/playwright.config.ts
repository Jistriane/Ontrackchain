import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  globalSetup: "./tests/e2e/global-setup.ts",
  timeout: 120_000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 1,
  reporter: [["html", { outputFolder: "playwright-report" }], ["junit", { outputFile: "test-results/junit.xml" }]],
  use: {
    baseURL: process.env.TEST_BASE_URL || "http://localhost:8080",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry"
  },
  projects: [{ name: "ui", use: { ...devices["Desktop Chrome"] } }]
});
