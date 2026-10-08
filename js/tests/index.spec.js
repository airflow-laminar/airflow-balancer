import { test, expect } from "@playwright/test";
import { fileURLToPath } from "node:url";

test.describe("Basics", () => {
  test("basic", async () => {
    await expect("").toBe("");
  });
});

test.describe("Host pools", () => {
  for (const { label, pool, expected } of [
    {
      label: "default model",
      pool: { pool: "worker1", slots: 2 },
      expected: "worker1",
    },
    {
      label: "custom model",
      pool: { pool: "compute-pool", slots: 2 },
      expected: "compute-pool",
    },
    { label: "string", pool: "legacy-pool", expected: "legacy-pool" },
    { label: "unset", pool: null, expected: "None" },
  ]) {
    test(label, async ({ page }) => {
      await page.setContent('<div id="airflow-balancer-root"></div>');
      await page.evaluate((pool) => {
        window.__AIRFLOW_BALANCER_CONFIG__ = JSON.stringify({
          hosts: [
            {
              name: "worker1",
              username: "airflow",
              pool,
              size: 2,
              queues: ["workers"],
              tags: [],
            },
          ],
        });
      }, pool);
      await page.addScriptTag({
        path: fileURLToPath(new URL("../dist/cdn/index.js", import.meta.url)),
        type: "module",
      });
      await page.evaluate(() =>
        document.dispatchEvent(new Event("DOMContentLoaded")),
      );
      await page.locator('sl-tab[panel="hosts"]').click();
      const row = page.locator('sl-tab-panel[name="hosts"] tbody tr');
      await expect(row.locator("td").nth(7)).toHaveText(expected);
      await expect(row).not.toContainText("[object Object]");
    });
  }
});
