'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Cookies from 'js-cookie'
import { api } from '@/lib/axios'
import { useAuth } from '@/hooks/useAuth'
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

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormValues = z.infer<typeof loginSchema>

interface LoginResponse {
  access: string
  user: {
    id: number
    email: string
    role: 'CUSTOMER' | 'BARBER' | 'SHOP_OWNER'
    full_name: string
  }
}

export function LoginForm() {
  const router = useRouter()
  const { setAuth } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null)
    try {
      const { data } = await api.post<LoginResponse>('/api/auth/login/', {
        email: values.email,
        password: values.password,
      })

      // Store in Zustand
      setAuth(
        {
          id: data.user.id,
          email: data.user.email,
          role: data.user.role,
          fullName: data.user.full_name,
        },
        data.access
      )

      // Set non-httpOnly cookie so middleware.ts can read it
      // Expires in 15 minutes (1/96 of a day)
      Cookies.set('access_token', data.access, { expires: 1 / 96, sameSite: 'lax' })

      // Role-based redirect
      if (data.user.role === 'CUSTOMER') {
        router.push('/customer/explore')
      } else if (data.user.role === 'BARBER') {
        router.push('/barber/dashboard')
      } else if (data.user.role === 'SHOP_OWNER') {
        router.push('/owner/overview')
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.non_field_errors?.[0] ||
        'Invalid email or password. Please try again.'
      setServerError(detail)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-ibook-brown-900">Welcome back</h2>
        <p className="mt-2 text-ibook-brown-500">Sign in to your IBook account</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
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
                    placeholder="••••••••"
                    autoComplete="current-password"
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
            {form.formState.isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-ibook-brown-500">
        Don&apos;t have an account?{' '}
        <Link
          href="/register/customer"
          className="font-medium text-ibook-brown-700 underline underline-offset-4"
        >
          Sign up
        </Link>
      </p>
    </div>
  )
}
