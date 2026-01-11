import { test } from '@playwright/test'

// These tests are stubs. They will be unskipped and implemented in Plan 04
// once the auth UI and role-based dashboards are built.

test.skip('customer blocked: customer redirected from /barber/dashboard', async ({ page }) => {
  // @skip Plan 04
  // 1. Log in as a CUSTOMER role user
  // 2. Navigate to /barber/dashboard
  // 3. Assert redirect to /login
})

test.skip('barber blocked: barber redirected from /owner/overview', async ({ page }) => {
  // @skip Plan 04
  // 1. Log in as a BARBER role user
  // 2. Navigate to /owner/overview
  // 3. Assert redirect to /login
})

test.skip('unauthenticated blocked: unauthenticated user redirected from /settings', async ({ page }) => {
  // @skip Plan 04
  // 1. Ensure no auth cookie is set
  // 2. Navigate to /settings
  // 3. Assert redirect to /login?returnUrl=/settings
})
