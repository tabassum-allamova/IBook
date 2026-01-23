'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api } from '@/lib/axios'
import { useAuth } from '@/hooks/useAuth'
import { HydrationGuard } from '@/components/HydrationGuard'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface Profile {
  id: number
  email: string
  role: 'CUSTOMER' | 'BARBER' | 'SHOP_OWNER'
  full_name: string
  phone_number: string | null
  avatar: string | null
  bio: string | null
  years_of_experience: number | string | null
}

const settingsSchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  phone_number: z.string().optional(),
  avatar: z.string().optional(),
  bio: z.string().optional(),
  years_of_experience: z.string().optional(),
})

type SettingsFormValues = z.infer<typeof settingsSchema>

const ROLE_LABELS: Record<string, string> = {
  CUSTOMER: 'Customer',
  BARBER: 'Barber',
  SHOP_OWNER: 'Shop Owner',
}

function SettingsContent() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login?returnUrl=/settings')
    }
  }, [isAuthenticated, router])

  const { data: profile, isLoading } = useQuery<Profile>({
    queryKey: ['profile'],
    queryFn: () => api.get('/api/auth/profile/').then((r) => r.data),
    enabled: isAuthenticated,
  })

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      full_name: '',
      phone_number: '',
      avatar: '',
      bio: '',
      years_of_experience: '',
    },
  })

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      form.reset({
        full_name: profile.full_name || '',
        phone_number: profile.phone_number || '',
        avatar: profile.avatar || '',
        bio: profile.bio || '',
        years_of_experience:
        profile.years_of_experience != null ? String(profile.years_of_experience) : '',
      })
    }
  }, [profile, form])

  const mutation = useMutation({
    mutationFn: (data: Partial<SettingsFormValues>) => api.patch('/api/auth/profile/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      setSaveMessage({ type: 'success', text: 'Profile updated successfully.' })
      setTimeout(() => setSaveMessage(null), 3000)
    },
    onError: () => {
      setSaveMessage({ type: 'error', text: 'Failed to save changes. Please try again.' })
    },
  })

  const onSubmit = (values: SettingsFormValues) => {
    setSaveMessage(null)
    // Only send non-empty optional fields
    const payload: Partial<SettingsFormValues> = { full_name: values.full_name }
    if (values.phone_number !== undefined) payload.phone_number = values.phone_number
    if (values.avatar !== undefined) payload.avatar = values.avatar
    if (user?.role === 'BARBER') {
      if (values.bio !== undefined) payload.bio = values.bio
      if (values.years_of_experience !== undefined)
        payload.years_of_experience = values.years_of_experience
    }
    mutation.mutate(payload)
  }

  if (!isAuthenticated) return null

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-ibook-brown-500">Loading profile…</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto py-10 px-6 w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-ibook-brown-900">Settings</h1>
        <p className="mt-1 text-ibook-brown-500">Manage your profile information</p>
      </div>

      {/* Role badge */}
      {profile && (
        <div className="mb-6">
          <span className="inline-block rounded-full bg-ibook-brown-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ibook-brown-700">
            {ROLE_LABELS[profile.role] ?? profile.role}
          </span>
        </div>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">Full Name</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Your full name"
                    className="bg-white border-ibook-brown-100"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Email — read-only */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-ibook-brown-700">Email</label>
            <Input
              value={profile?.email ?? ''}
              readOnly
              className="bg-ibook-brown-50 border-ibook-brown-100 text-ibook-brown-500 cursor-not-allowed"
            />
          </div>

          <FormField
            control={form.control}
            name="phone_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">
                  Phone Number{' '}
                  <span className="font-normal text-ibook-brown-500">(optional)</span>
                </FormLabel>
                <FormControl>
                  <Input
                    type="tel"
                    placeholder="+1 555 000 0000"
                    className="bg-white border-ibook-brown-100"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="avatar"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">
                  Avatar URL{' '}
                  <span className="font-normal text-ibook-brown-500">(optional)</span>
                </FormLabel>
                <FormControl>
                  <Input
                    type="url"
                    placeholder="https://example.com/avatar.jpg"
                    className="bg-white border-ibook-brown-100"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Barber-only fields */}
          {user?.role === 'BARBER' && (
            <>
              <FormField
                control={form.control}
                name="bio"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-ibook-brown-700 font-medium">Bio</FormLabel>
                    <FormControl>
                      <textarea
                        rows={3}
                        placeholder="Tell customers about yourself…"
                        className="w-full rounded-lg border border-ibook-brown-100 bg-white px-3 py-2 text-sm text-ibook-brown-900 placeholder:text-ibook-brown-400 focus:outline-none focus:border-ibook-gold-400"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="years_of_experience"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-ibook-brown-700 font-medium">
                      Years of Experience
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        placeholder="5"
                        className="bg-white border-ibook-brown-100"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </>
          )}

          {saveMessage && (
            <div
              className={`rounded-lg px-4 py-3 text-sm ${
                saveMessage.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-700'
                  : 'bg-destructive/10 border border-destructive/50 text-destructive'
              }`}
            >
              {saveMessage.text}
            </div>
          )}

          <Button
            type="submit"
            disabled={mutation.isPending}
            className="w-full bg-ibook-brown-700 hover:bg-ibook-brown-900 text-white font-semibold py-2.5 rounded-xl h-auto"
          >
            {mutation.isPending ? 'Saving…' : 'Save changes'}
          </Button>
        </form>
      </Form>
    </div>
  )
}

export default function SettingsPage() {
  return (
    <HydrationGuard>
      <SettingsContent />
    </HydrationGuard>
  )
}
