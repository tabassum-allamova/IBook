/**
 * E2E RBAC tests — requires both servers running:
 *   Terminal 1: cd backend && python manage.py runserver
 *   Terminal 2: cd frontend && npm run dev
 *
 * SETUP: seed test users first:
 *   cd backend && python manage.py seed_test_users
 */
import { test, expect } from '@playwright/test'
import { loginAs, logout } from './helpers/auth'

test('customer blocked: customer redirected from /barber/dashboard', async ({ page }) => {
  // Log in as a CUSTOMER role user
  await loginAs(page, 'customer')

  // Navigate to barber-only route
  await page.goto('http://localhost:3000/barber/dashboard')

  // Assert redirected to /login (middleware blocks wrong role)
  await expect(page).toHaveURL(/\/login/)
})

test('barber blocked: barber redirected from /owner/overview', async ({ page }) => {
  // Log in as a BARBER role user
  await loginAs(page, 'barber')

  // Navigate to owner-only route
  await page.goto('http://localhost:3000/owner/overview')

  // Assert redirected to /login (middleware blocks wrong role)
  await expect(page).toHaveURL(/\/login/)
})

test('unauthenticated blocked: unauthenticated user redirected from /settings', async ({
  page,
}) => {
  // Ensure no auth cookie
  await logout(page)

  // Navigate to protected /settings
  await page.goto('http://localhost:3000/settings')

  // Assert redirected to /login with returnUrl
  await expect(page).toHaveURL(/\/login\?returnUrl=\/settings/)
})
