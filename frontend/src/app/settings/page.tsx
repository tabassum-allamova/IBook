'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { HydrationGuard } from '@/components/HydrationGuard'

function SettingsRedirect() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login?returnUrl=/settings')
      return
    }
    if (user?.role === 'CUSTOMER') router.replace('/customer/settings')
    else if (user?.role === 'BARBER') router.replace('/barber/settings')
    else if (user?.role === 'SHOP_OWNER') router.replace('/owner/settings')
  }, [isAuthenticated, user, router])

  return null
}

export default function SettingsPage() {
  return (
    <HydrationGuard>
      <SettingsRedirect />
    </HydrationGuard>
  )
}
