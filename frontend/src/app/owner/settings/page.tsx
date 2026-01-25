import { HydrationGuard } from '@/components/HydrationGuard'
import { SettingsContent } from '@/components/settings/SettingsContent'

export default function OwnerSettingsPage() {
  return (
    <HydrationGuard>
      <SettingsContent />
    </HydrationGuard>
  )
}
