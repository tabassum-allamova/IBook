/**
 * E2E auth helpers for Playwright tests.
 *
 * SETUP REQUIRED — seed test users before running E2E tests:
 *   cd backend && python manage.py seed_test_users
 *
 * Test user credentials:
 *   customer@test.com  / Pass1234!  (role: CUSTOMER)
 *   barber@test.com    / Pass1234!  (role: BARBER)
 *   owner@test.com     / Pass1234!  (role: SHOP_OWNER)
 */
import { Page } from '@playwright/test'

const TEST_USERS = {
  customer: { email: 'customer@test.com', password: 'Pass1234!' },
  barber: { email: 'barber@test.com', password: 'Pass1234!' },
  owner: { email: 'owner@test.com', password: 'Pass1234!' },
}

/**
 * Log in a test user by posting directly to the Django API and setting the
 * access_token cookie on the browser context. This avoids UI-speed login
 * (no page navigation needed).
 */
export async function loginAs(page: Page, role: keyof typeof TEST_USERS) {
  const { email, password } = TEST_USERS[role]
  const res = await page.request.post('http://localhost:8000/api/auth/login/', {
    data: { email, password },
  })
  const body = await res.json()
  await page.context().addCookies([
    {
      name: 'access_token',
      value: body.access,
      domain: 'localhost',
      path: '/',
    },
  ])
  // Also set Zustand persist state so the React app sees the user
  await page.context().addCookies([])
  return body
}

/**
 * Clear auth state (cookies + localStorage Zustand key).
 */
export async function logout(page: Page) {
  await page.context().clearCookies()
}
