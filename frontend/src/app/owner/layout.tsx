import { Sidebar } from '@/components/layout/Sidebar'

const OWNER_NAV = [
  { href: '/owner/overview', label: 'Shop Overview' },
  { href: '/owner/barbers', label: 'Barbers' },
  { href: '/owner/analytics', label: 'Analytics' },
  { href: '/owner/settings', label: 'Settings' },
]

export default function OwnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-ibook-cream">
      <Sidebar navItems={OWNER_NAV} />
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  )
}
