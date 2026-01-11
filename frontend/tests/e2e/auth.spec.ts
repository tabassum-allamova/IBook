import { test } from '@playwright/test'

// These tests are stubs. They will be unskipped and implemented in Plan 04
// once the auth UI (login/register pages) is built.

test.skip('persist: user stays logged in after refresh', async ({ page }) => {
  // @skip Plan 04
  // 1. Log in via /login form
  // 2. Reload the page
  // 3. Assert the user is still authenticated (no redirect to /login)
})

test.skip('logout: user is redirected to login after logout', async ({ page }) => {
  // @skip Plan 04
  // 1. Log in via /login form
  // 2. Click logout button
  // 3. Assert the user is redirected to /login
})

test.skip('settings: user can update profile info', async ({ page }) => {
  // @skip Plan 04
  // 1. Log in via /login form
  // 2. Navigate to /settings
  // 3. Update profile fields
  // 4. Assert changes are persisted
})
