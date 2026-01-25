import { HydrationGuard } from '@/components/HydrationGuard'
import { SettingsContent } from '@/components/settings/SettingsContent'

export default function CustomerSettingsPage() {
  return (
    <HydrationGuard>
      <SettingsContent />
    </HydrationGuard>
  )
}
