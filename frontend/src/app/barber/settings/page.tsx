import { HydrationGuard } from '@/components/HydrationGuard'
import { SettingsContent } from '@/components/settings/SettingsContent'

export default function BarberSettingsPage() {
  return (
    <HydrationGuard>
      <SettingsContent />
    </HydrationGuard>
  )
}
