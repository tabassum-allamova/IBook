import { Navbar } from '@/components/layout/Navbar'

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-ibook-cream">
      <Navbar />
      <main className="flex-1 mx-auto w-full max-w-screen-xl px-4 sm:px-6 py-8">{children}</main>
    </div>
  )
}
