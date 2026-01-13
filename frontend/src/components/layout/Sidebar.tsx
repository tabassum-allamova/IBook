'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { api } from '@/lib/axios'
import { useAuth } from '@/hooks/useAuth'
import { HydrationGuard } from '@/components/HydrationGuard'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
}

interface SidebarContentProps {
  navItems: NavItem[]
}

function SidebarContent({ navItems }: SidebarContentProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { clearAuth } = useAuth()

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
    <aside className="flex h-screen w-60 flex-col border-r border-ibook-brown-100 bg-ibook-cream">
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-ibook-brown-100 px-5">
        <span className="text-xl font-bold text-ibook-brown-900">IBook</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              pathname === item.href || pathname.startsWith(item.href + '/')
                ? 'bg-ibook-brown-700 text-white'
                : 'text-ibook-brown-700 hover:bg-ibook-brown-100 hover:text-ibook-brown-900'
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-ibook-brown-100 px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium text-ibook-brown-700 hover:bg-ibook-brown-100 hover:text-ibook-brown-900 transition-colors"
        >
          Logout
        </button>
      </div>
    </aside>
  )
}

interface SidebarProps {
  navItems: NavItem[]
}

export function Sidebar({ navItems }: SidebarProps) {
  return (
    <HydrationGuard>
      <SidebarContent navItems={navItems} />
    </HydrationGuard>
  )
}
