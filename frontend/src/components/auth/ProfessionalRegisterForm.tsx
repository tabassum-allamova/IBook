'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { api } from '@/lib/axios'
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

const professionalSchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  email: z.string().email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Za-z]/, 'Password must contain at least one letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  role: z.enum(['BARBER', 'SHOP_OWNER'], {
    error: () => ({ message: 'Please select your role' }),
  }),
  phone_number: z.string().optional(),
})

type ProfessionalFormValues = z.infer<typeof professionalSchema>

export function ProfessionalRegisterForm() {
  const [success, setSuccess] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const form = useForm<ProfessionalFormValues>({
    resolver: zodResolver(professionalSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      role: 'BARBER',
      phone_number: '',
    },
  })

  const onSubmit = async (values: ProfessionalFormValues) => {
    setServerError(null)
    try {
      const payload: Record<string, string> = {
        full_name: values.full_name,
        email: values.email,
        password: values.password,
        role: values.role,
      }
      if (values.phone_number) {
        payload.phone_number = values.phone_number
      }
      await api.post('/api/auth/register/professional/', payload)
      setSuccess(true)
    } catch (err: unknown) {
      const error = err as {
        response?: {
          data?: Record<string, string | string[]>
        }
      }
      const data = error?.response?.data
      if (data) {
        const firstKey = Object.keys(data)[0]
        const msg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey]
        setServerError(String(msg))
      } else {
        setServerError('Registration failed. Please try again.')
      }
    }
  }

  if (success) {
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-ibook-brown-900">Check your email</h2>
          <p className="mt-2 text-ibook-brown-500">
            We sent a verification link to your email address. Please click the link to activate
            your account before logging in.
          </p>
        </div>
        <p className="text-sm text-ibook-brown-500">
          Already verified?{' '}
          <Link href="/login" className="font-medium text-ibook-brown-700 underline underline-offset-4">
            Log in
          </Link>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <Link href="/" className="text-sm text-ibook-brown-500 hover:text-ibook-brown-700 inline-flex items-center gap-1 mb-4">
          ← Back to home
        </Link>
        <h2 className="text-3xl font-bold text-ibook-brown-900">Join as a Professional</h2>
        <p className="mt-2 text-ibook-brown-500">Create your IBook professional account</p>
      </div>

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
                    placeholder="John Smith"
                    autoComplete="name"
                    className="bg-white border-ibook-brown-100 focus:border-ibook-gold-400"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    className="bg-white border-ibook-brown-100 focus:border-ibook-gold-400"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="Min 8 chars, letter + number"
                    autoComplete="new-password"
                    className="bg-white border-ibook-brown-100 focus:border-ibook-gold-400"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="role"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-ibook-brown-700 font-medium">I am a…</FormLabel>
                <FormControl>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        value="BARBER"
                        checked={field.value === 'BARBER'}
                        onChange={() => field.onChange('BARBER')}
                        className="accent-ibook-brown-700"
                      />
                      <span className="text-ibook-brown-900 text-sm font-medium">Barber</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        value="SHOP_OWNER"
                        checked={field.value === 'SHOP_OWNER'}
                        onChange={() => field.onChange('SHOP_OWNER')}
                        className="accent-ibook-brown-700"
                      />
                      <span className="text-ibook-brown-900 text-sm font-medium">Shop Owner</span>
                    </label>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

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
                    autoComplete="tel"
                    className="bg-white border-ibook-brown-100 focus:border-ibook-gold-400"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {serverError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {serverError}
            </div>
          )}

          <Button
            type="submit"
            disabled={form.formState.isSubmitting}
            className="w-full bg-ibook-brown-700 hover:bg-ibook-brown-900 text-white font-semibold py-2.5 rounded-xl h-auto"
          >
            {form.formState.isSubmitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-ibook-brown-500">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-ibook-brown-700 underline underline-offset-4">
          Log in
        </Link>
      </p>
    </div>
  )
}
