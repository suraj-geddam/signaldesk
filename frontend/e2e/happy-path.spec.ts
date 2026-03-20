import { test, expect } from "@playwright/test";

// react-hot-toast renders a fixed overlay at z-index 9999 with
// pointer-events:none. Playwright's actionability checks see it as
// covering buttons and refuses to click. We hide it on every page load.
async function dismissToastOverlay(page: import("@playwright/test").Page) {
  await page.addStyleTag({
    content: "[data-rht-toaster] { display: none !important; }",
  });
}

test("happy path: member CRUD, dashboard, admin delete", async ({ page }) => {
  // ── Login as member ──────────────────────────────────────────────
  await test.step("login as member", async () => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await dismissToastOverlay(page);
    await page.getByLabel("Username").fill("member");
    await page.getByLabel("Password").fill("member123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/feedback**");
    await dismissToastOverlay(page);
    await expect(page.getByText("member").first()).toBeVisible();
  });

  // ── Create feedback ──────────────────────────────────────────────
  await test.step("create feedback", async () => {
    await page.getByRole("button", { name: "+ New feedback" }).click();
    await expect(
      page.getByRole("heading", { name: "New feedback" }),
    ).toBeVisible();

    const modal = page.locator("dialog");
    await modal.getByLabel("Title").fill("E2E: SOC2 export support");
    await modal.getByLabel("Description").fill(
      "Enterprise customers need SOC2-compliant CSV exports for audit purposes.",
    );
    await modal.getByLabel("Source").selectOption("email");
    await modal.getByLabel("Priority").selectOption("high");
    await page.getByRole("button", { name: "Create", exact: true }).click();

    // Modal closes, feedback appears in table
    await expect(
      page.getByRole("heading", { name: "New feedback" }),
    ).not.toBeVisible();
    await expect(
      page.getByRole("cell", { name: /SOC2 export support/ }),
    ).toBeVisible();
  });

  // ── Verify table row details ─────────────────────────────────────
  await test.step("verify feedback in table", async () => {
    const row = page
      .getByRole("row")
      .filter({ hasText: "SOC2 export support" });
    await expect(row.getByText("New")).toBeVisible();
    await expect(row.getByText("High")).toBeVisible();
    await expect(row.getByText("Email")).toBeVisible();
  });

  // ── Open detail modal ────────────────────────────────────────────
  await test.step("view detail modal", async () => {
    await page
      .getByRole("row")
      .filter({ hasText: "SOC2 export support" })
      .click();
    await expect(
      page.getByRole("heading", { name: "E2E: SOC2 export support" }),
    ).toBeVisible();
    await expect(
      page.getByRole("dialog").getByText("Enterprise customers need"),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Edit" })).toBeVisible();
  });

  // ── Edit feedback ────────────────────────────────────────────────
  await test.step("edit feedback (change status to in_progress)", async () => {
    await page.getByRole("button", { name: "Edit" }).click();
    await expect(
      page.getByRole("heading", { name: "Edit feedback" }),
    ).toBeVisible();

    // Change the status via JS to avoid Playwright's selectOption
    // auto-triggering form submission in headless Chromium.
    await page.getByRole("dialog").getByLabel("Status").evaluate(
      (el: HTMLSelectElement) => {
        el.value = "in_progress";
        el.dispatchEvent(new Event("change", { bubbles: true }));
      },
    );
    // Use evaluate to submit the form directly — Playwright's click
    // on the Save button races with a prior auto-submit from selectOption.
    await page.evaluate(() => {
      const form = document.getElementById("edit-feedback-form") as HTMLFormElement;
      if (form) form.requestSubmit();
    });

    // Modal closes, table shows updated status
    await expect(
      page
        .getByRole("row")
        .filter({ hasText: "SOC2 export support" })
        .getByText("In Progress"),
    ).toBeVisible({ timeout: 10_000 });
  });

  // ── Dashboard ────────────────────────────────────────────────────
  await test.step("dashboard shows correct counts", async () => {
    await page.getByRole("link", { name: "Dashboard" }).click();
    await dismissToastOverlay(page);
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Status: 0 new, 1 in progress, 0 done
    const statusSection = page.locator("text=BY STATUS").locator("..");
    await expect(statusSection.getByText("1")).toBeVisible();

    // Priority: 1 high
    const prioritySection = page.locator("text=BY PRIORITY").locator("..");
    await expect(prioritySection.getByText("1")).toBeVisible();
  });

  // ── Insights (member — no refresh button) ────────────────────────
  await test.step("insights shows empty state for member", async () => {
    await page.getByRole("link", { name: "Insights" }).click();
    await dismissToastOverlay(page);
    await expect(
      page.getByRole("heading", { name: "Insights" }),
    ).toBeVisible();
    await expect(page.getByText("No insights generated yet.")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Refresh insights" }),
    ).not.toBeVisible();
  });

  // ── Logout ───────────────────────────────────────────────────────
  await test.step("logout", async () => {
    await page.getByRole("button", { name: "Log out" }).click();
    await page.waitForURL("**/login**");
  });

  // ── Login as admin ───────────────────────────────────────────────
  await test.step("login as admin", async () => {
    await dismissToastOverlay(page);
    await page.getByLabel("Username").fill("admin");
    await page.getByLabel("Password").fill("admin123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/feedback**");
    await dismissToastOverlay(page);
    await expect(page.getByText("admin").first()).toBeVisible();
  });

  // ── Insights (admin — refresh button visible) ────────────────────
  await test.step("admin can trigger insights refresh", async () => {
    await page.getByRole("link", { name: "Insights" }).click();
    await dismissToastOverlay(page);
    await expect(
      page.getByRole("button", { name: "Refresh insights" }),
    ).toBeVisible();

    // Click refresh — the POST hits the real backend (returns 202).
    await page.getByRole("button", { name: "Refresh insights" }).click();

    // Intercept GET /feedback/insights to return mock data so we can
    // verify the polling + rendering flow without a real LLM backend.
    await page.route("**/feedback/insights", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            insights: [
              {
                theme: "Export compliance workflows",
                confidence: 0.91,
                justification:
                  "Customer feedback consistently requests SOC2 and CSV exports.",
              },
            ],
            feedback_count: 1,
            model_used: "mock-e2e",
            generated_at: new Date().toISOString(),
            stale: false,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Wait for the mocked insight card to render
    await expect(page.getByText("Export compliance workflows")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText("91%")).toBeVisible();

    // Clean up route mock
    await page.unroute("**/feedback/insights");
  });

  // ── Delete feedback (admin) ──────────────────────────────────────
  await test.step("admin deletes feedback", async () => {
    await page.getByRole("link", { name: "Feedback" }).click();
    await dismissToastOverlay(page);
    await expect(
      page.getByRole("cell", { name: /SOC2 export support/ }),
    ).toBeVisible();

    // Click the three-dot actions menu
    await page.getByRole("button", { name: "Actions" }).click();
    await page.getByRole("button", { name: "Delete" }).click();

    // Confirmation dialog
    await expect(page.getByText("Delete this feedback?")).toBeVisible();
    await page
      .locator("div")
      .filter({ hasText: /^CancelDelete$/ })
      .getByRole("button", { name: "Delete" })
      .click();

    // Table should show empty state
    await expect(page.getByText("No feedback yet.")).toBeVisible();
  });
});
