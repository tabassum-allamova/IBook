'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { api } from '@/lib/axios'
import { useAuth } from '@/hooks/useAuth'
import { HydrationGuard } from '@/components/HydrationGuard'

function NavbarContent() {
  const router = useRouter()
  const { user, clearAuth } = useAuth()

  const handleLogout = async () => {
    try {
      await api.post('/api/auth/logout/')
    } catch {
      // Continue with logout even if API call fails
    }
    clearAuth()
    Cookies.remove('access_token')
    router.push('/login')
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-ibook-brown-100 bg-ibook-cream">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link href="/customer/explore" className="text-xl font-bold text-ibook-brown-900">
          IBook
        </Link>

        {/* Nav links */}
        <nav className="hidden sm:flex items-center gap-6 text-sm font-medium text-ibook-brown-700">
          <Link href="/customer/explore" className="hover:text-ibook-brown-900 transition-colors">
            Explore
          </Link>
          <Link href="/customer/appointments" className="hover:text-ibook-brown-900 transition-colors">
            Appointments
          </Link>
        </nav>

        {/* User actions */}
        <div className="flex items-center gap-3">
          {user && (
            <span className="hidden sm:block text-sm text-ibook-brown-500">
              {user.fullName}
            </span>
          )}
          <Link
            href="/customer/settings"
            className="text-sm text-ibook-brown-700 hover:text-ibook-brown-900 transition-colors"
          >
            Settings
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-ibook-brown-700 hover:text-ibook-brown-900 transition-colors border border-ibook-brown-200 rounded-lg px-3 py-1.5 hover:bg-ibook-brown-100"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}

export function Navbar() {
  return (
    <HydrationGuard>
      <NavbarContent />
    </HydrationGuard>
  )
}
