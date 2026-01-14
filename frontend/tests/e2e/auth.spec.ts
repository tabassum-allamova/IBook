/**
 * E2E auth tests — requires both servers running:
 *   Terminal 1: cd backend && python manage.py runserver
 *   Terminal 2: cd frontend && npm run dev
 *
 * SETUP: seed test users first:
 *   cd backend && python manage.py seed_test_users
 */
import { test, expect } from '@playwright/test'
import { loginAs, logout } from './helpers/auth'

test('persist: user stays logged in after refresh', async ({ page }) => {
  // Log in as customer via API helper (fast, no UI navigation)
  await loginAs(page, 'customer')

  // Navigate to the customer explore page
  await page.goto('http://localhost:3000/customer/explore')

  // Reload the page
  await page.reload()

  // Assert still on /customer/explore — not redirected to /login
  await expect(page).toHaveURL(/\/customer\/explore/)
  await expect(page.getByRole('heading', { name: 'Explore Barbers' })).toBeVisible()
})

test('logout: user is redirected to login after logout', async ({ page }) => {
  // Log in as customer
  await loginAs(page, 'customer')
  await page.goto('http://localhost:3000/customer/explore')

  // Wait for navbar to appear
  await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible()

  // Click logout
  await page.getByRole('button', { name: 'Logout' }).click()

  // Assert redirected to /login
  await expect(page).toHaveURL(/\/login/)
})

test('settings: user can update profile info', async ({ page }) => {
  // Log in as customer
  await loginAs(page, 'customer')
  await page.goto('http://localhost:3000/settings')

  // Wait for form to load
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()

  // Update phone number
  const phoneInput = page.getByLabel(/phone number/i)
  await phoneInput.clear()
  await phoneInput.fill('+1 555 999 0001')

  // Save
  await page.getByRole('button', { name: 'Save changes' }).click()

  // Assert success message
  await expect(page.getByText('Profile updated successfully')).toBeVisible()
})
