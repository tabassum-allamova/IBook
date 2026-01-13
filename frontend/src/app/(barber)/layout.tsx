import { Sidebar } from '@/components/layout/Sidebar'

const BARBER_NAV = [
  { href: '/barber/dashboard', label: 'Appointments' },
  { href: '/barber/availability', label: 'Availability' },
  { href: '/settings', label: 'Settings' },
]

export default function BarberLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-ibook-cream">
      <Sidebar navItems={BARBER_NAV} />
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  )
}
