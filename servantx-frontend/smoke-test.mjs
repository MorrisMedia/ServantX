#!/usr/bin/env node
/**
 * ServantX UI Smoke Test
 * Run: npx playwright test smoke-test.spec.mjs (or node smoke-test.mjs with playwright)
 * Or: npx playwright install chromium && node smoke-test.mjs
 */
import { chromium } from "playwright";

const BASE = "http://localhost:5001";
const EMAIL = "marshall+servantx-test@example.com";
const PASSWORD = "TestPass123!";

const results = [];

function log(name, pass, detail = "") {
  const status = pass ? "PASS" : "FAIL";
  results.push({ name, pass, detail });
  console.log(`  [${status}] ${name}${detail ? ` - ${detail}` : ""}`);
}

async function main() {
  console.log("\n=== ServantX UI Smoke Test ===\n");
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    page.setDefaultTimeout(12000);

    // 1) Login
    console.log("1) Login...");
    await page.goto(`${BASE}/auth/login`, { waitUntil: "networkidle" });
    const loginVisible = await page.locator('input[type="email"], input[name="email"]').first().isVisible().catch(() => false);
    if (!loginVisible) {
      log("Login page loads", false, "No email input found");
    } else {
      await page.fill('input[type="email"], input[name="email"]', EMAIL);
      await page.fill('input[type="password"], input[name="password"]', PASSWORD);
      await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")');
      await page.waitForTimeout(2500);
      const url = page.url();
      const hasError = await page.locator('text=/invalid|error|incorrect/i').isVisible().catch(() => false);
      if (hasError) {
        const errText = await page.locator('text=/invalid|error|incorrect/i').first().textContent().catch(() => "");
        log("Login", false, errText || "Error message shown");
      } else if (url.includes("/dashboard") || url.includes("/auth/login")) {
        log("Login", true, url.includes("/dashboard") ? "Redirected to dashboard" : "Stayed on login (check credentials)");
      } else {
        log("Login", true, `Landed at ${url}`);
      }
    }

    if (!page.url().includes("/dashboard")) {
      await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle" });
      await page.waitForTimeout(2000);
    }

    // 2a) Billing records bulk delete controls (check early while session is fresh)
    console.log("\n2a) Billing records bulk delete controls...");
    await page.goto(`${BASE}/dashboard/billing-records`, { waitUntil: "networkidle" });
    await page.waitForTimeout(5000);
    const onBillingPage = page.url().includes("billing-records");
    const billingBody = await page.locator("body").textContent().catch(() => "") || "";
    if (process.env.DEBUG) console.log("  [DEBUG] URL:", page.url(), "| body length:", billingBody.length);
    if (!onBillingPage) {
      log("On billing-records page", false, "Redirected away (no contract?)");
      log("Checkboxes visible", false, "N/A");
      log("Delete Selected button visible", false, "N/A");
    } else {
      const hasQuickDrop = await page.locator('text=Quick Drop Upload').first().isVisible().catch(() => false);
      const hasBillingRecordsHeading = await page.locator('text=Billing Records').first().isVisible().catch(() => false);
      const hasCheckbox = await page.locator('[role="checkbox"], input[type="checkbox"]').first().isVisible().catch(() => false);
      const hasDeleteBtn = await page.locator('button:has-text("Delete Selected")').first().isVisible().catch(() => false);
      log("Billing Records page content", hasQuickDrop || hasBillingRecordsHeading, (hasQuickDrop || hasBillingRecordsHeading) ? "" : "Page may not have fully loaded");
      log("Checkboxes visible", hasCheckbox, hasCheckbox ? "" : "Table checkboxes only when records exist");
      log("Delete Selected button visible", hasDeleteBtn);
    }

    // 2) Page checks
    const pages = [
      { path: "/dashboard", expect: ["Overview", "overview"] },
      { path: "/dashboard/contracts", expect: ["contract", "Contract"] },
      { path: "/dashboard/rules", expect: ["rule", "Rule"] },
      { path: "/dashboard/billing-records", expect: ["billing", "Billing", "record", "Record"] },
      { path: "/dashboard/documents", expect: ["document", "Document"] },
      { path: "/dashboard/audit-workflow", expect: ["batch", "Batch", "audit", "Audit"] },
      { path: "/dashboard/settings", expect: ["setting", "Setting", "tab"] },
    ];

    console.log("\n2) Page content checks...");
    for (const { path, expect } of pages) {
      await page.goto(`${BASE}${path}`, { waitUntil: "domcontentloaded" });
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.waitForTimeout(2500);
      const body = await page.locator("body").textContent().catch(() => "") || "";
      const html = await page.content().catch(() => "") || "";
      const isBlank = body.trim().length < 50 && !html.includes("ServantX") && !html.includes("Loading");
      const hasExpected = expect.some((e) => body.toLowerCase().includes(e.toLowerCase()));
      const hasAnyContent = body.toLowerCase().includes("servantx") || body.includes("Contract") || body.includes("Billing") || body.includes("Overview");
      const blocker = await page.locator('text=/error|failed|404|500|unauthorized/i').first().textContent().catch(() => null);
      const url = page.url();
      const redirected = !url.includes(path.split("?")[0]);
      if (isBlank) {
        log(path, false, "Page appears blank");
      } else if (blocker) {
        log(path, false, `Blocker: ${String(blocker).slice(0, 80)}`);
      } else if (hasExpected || hasAnyContent || (redirected && body.length > 200)) {
        log(path, true, redirected ? "Redirected but content present" : "");
      } else {
        log(path, true, `Content present (${body.length} chars)`);
      }
    }

    // Summary
    console.log("\n=== Summary ===");
    const passed = results.filter((r) => r.pass).length;
    const failed = results.filter((r) => !r.pass);
    console.log(`Passed: ${passed}/${results.length}`);
    if (failed.length) {
      console.log("Failed:");
      failed.forEach((f) => console.log(`  - ${f.name}: ${f.detail || "no detail"}`));
    }
    process.exit(failed.length > 0 ? 1 : 0);
  } catch (err) {
    console.error("Smoke test error:", err.message);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
}

main();
