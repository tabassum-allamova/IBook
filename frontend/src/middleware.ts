import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify } from 'jose'

// Role-based route protection map
const ROLE_ROUTES: Record<string, string[]> = {
  '/barber': ['BARBER'],
  '/owner': ['SHOP_OWNER'],
  '/customer': ['CUSTOMER'],
  '/settings': ['CUSTOMER', 'BARBER', 'SHOP_OWNER'], // any authenticated
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Find if current path matches a protected route prefix
  const matchedPrefix = Object.keys(ROLE_ROUTES).find((prefix) =>
    pathname.startsWith(prefix)
  )

  // Not a protected route — allow through
  if (!matchedPrefix) return NextResponse.next()

  // NOTE: Middleware reads from 'access_token' cookie (non-httpOnly).
  // Plan 04 must set this cookie on login alongside updating Zustand.
  // The httpOnly refresh_token cookie is separate and handled by the backend.
  const accessToken = request.cookies.get('access_token')?.value

  if (!accessToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  try {
    const secret = new TextEncoder().encode(
      process.env.JWT_SECRET || process.env.NEXTAUTH_SECRET || ''
    )
    const { payload } = await jwtVerify(accessToken, secret)
    const role = payload.role as string

    // Role check — wrong role redirects to login
    if (!ROLE_ROUTES[matchedPrefix].includes(role)) {
      return NextResponse.redirect(new URL('/login', request.url))
    }

    return NextResponse.next()
  } catch {
    // Token invalid or expired — redirect to login with return URL
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }
}

export const config = {
  matcher: ['/barber/:path*', '/owner/:path*', '/customer/:path*', '/settings/:path*'],
}
