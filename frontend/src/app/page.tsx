'use client'

import Link from 'next/link'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { HydrationGuard } from '@/components/HydrationGuard'

function LandingContent() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated || !user) return
    if (user.role === 'CUSTOMER') router.replace('/customer/explore')
    else if (user.role === 'BARBER') router.replace('/barber/dashboard')
    else if (user.role === 'SHOP_OWNER') router.replace('/owner/overview')
  }, [isAuthenticated, user, router])

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-ibook-cream px-6">
      <div className="text-center space-y-6 max-w-lg">
        <h1 className="text-6xl font-bold text-ibook-brown-900 tracking-tight">
          IBook
        </h1>
        <p className="text-xl text-ibook-brown-500 leading-relaxed">
          Book your perfect cut, anywhere.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
          <Link
            href="/register/customer"
            className="inline-flex items-center justify-center bg-ibook-brown-700 hover:bg-ibook-brown-900 text-white font-semibold px-8 py-3 rounded-xl text-base transition-colors"
          >
            I&apos;m a Customer
          </Link>
          <Link
            href="/register/professional"
            className="inline-flex items-center justify-center border-2 border-ibook-brown-700 text-ibook-brown-700 hover:bg-ibook-brown-100 font-semibold px-8 py-3 rounded-xl text-base transition-colors"
          >
            I&apos;m a Barber / Shop Owner
          </Link>
        </div>
        <p className="text-sm text-ibook-brown-500 mt-4">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-ibook-brown-700 underline underline-offset-4">
            Log in
          </Link>
        </p>
      </div>
    </main>
  )
}

export default function HomePage() {
  return (
    <HydrationGuard>
      <LandingContent />
    </HydrationGuard>
  )
}
