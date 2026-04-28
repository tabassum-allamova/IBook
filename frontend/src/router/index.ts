import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // Public
  {
    path: '/',
    redirect: '/customer/explore',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/register/customer',
    name: 'register-customer',
    component: () => import('@/views/RegisterCustomerPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/register/professional',
    name: 'register-professional',
    component: () => import('@/views/RegisterProfessionalPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/verify-email',
    name: 'verify-email',
    component: () => import('@/views/VerifyEmailPage.vue'),
  },

  // Customer routes
  {
    path: '/customer',
    redirect: '/customer/explore',
  },
  {
    path: '/customer/explore',
    name: 'customer-explore',
    component: () => import('@/views/customer/ExplorePage.vue'),
  },
  {
    path: '/customer/search',
    name: 'customer-search',
    component: () => import('@/views/customer/SearchPage.vue'),
  },
  {
    path: '/customer/book/:barberId',
    name: 'customer-booking',
    component: () => import('@/views/customer/BookingPage.vue'),
    meta: { requiresAuth: true, role: 'CUSTOMER' as UserRole },
    props: true,
  },
  {
    path: '/customer/appointments',
    name: 'customer-appointments',
    component: () => import('@/views/customer/AppointmentsPage.vue'),
    meta: { requiresAuth: true, role: 'CUSTOMER' as UserRole },
  },
  {
    path: '/customer/settings',
    name: 'customer-settings',
    component: () => import('@/views/customer/SettingsPage.vue'),
    meta: { requiresAuth: true, role: 'CUSTOMER' as UserRole },
  },
  {
    path: '/customer/shop/:shopId',
    name: 'customer-shop-detail',
    component: () => import('@/views/customer/ShopDetailPage.vue'),
    props: true,
  },
  {
    path: '/customer/barber/:barberId',
    name: 'customer-barber-profile',
    component: () => import('@/views/customer/BarberProfilePage.vue'),
    props: true,
  },
  {
    path: '/customer/review/:appointmentId',
    name: 'customer-review',
    component: () => import('@/views/customer/ReviewPage.vue'),
    meta: { requiresAuth: true, role: 'CUSTOMER' as UserRole },
    props: true,
  },

  // Barber routes
  {
    path: '/barber',
    redirect: '/barber/dashboard',
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },
  {
    path: '/barber/dashboard',
    name: 'barber-dashboard',
    component: () => import('@/views/barber/DashboardPage.vue'),
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },
  {
    path: '/barber/appointments',
    name: 'barber-appointments',
    component: () => import('@/views/barber/AppointmentsPage.vue'),
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },
  {
    path: '/barber/services',
    name: 'barber-services',
    component: () => import('@/views/barber/ServicesPage.vue'),
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },
  {
    path: '/barber/availability',
    name: 'barber-availability',
    component: () => import('@/views/barber/AvailabilityPage.vue'),
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },
  {
    path: '/barber/settings',
    name: 'barber-settings',
    component: () => import('@/views/barber/SettingsPage.vue'),
    meta: { requiresAuth: true, role: 'BARBER' as UserRole },
  },

  // Shop Owner routes
  {
    path: '/owner',
    redirect: '/owner/overview',
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },
  {
    path: '/owner/overview',
    name: 'owner-overview',
    component: () => import('@/views/owner/OverviewPage.vue'),
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },
  {
    path: '/owner/settings',
    name: 'owner-settings',
    component: () => import('@/views/owner/SettingsPage.vue'),
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },

  // Shop Owner shop routes
  {
    path: '/owner/shop/setup',
    name: 'owner-shop-setup',
    component: () => import('@/views/owner/ShopSetupPage.vue'),
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },
  {
    path: '/owner/barbers',
    name: 'owner-barbers',
    component: () => import('@/views/owner/BarbersPage.vue'),
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },
  {
    path: '/owner/analytics',
    name: 'owner-analytics',
    component: () => import('@/views/owner/AnalyticsPage.vue'),
    meta: { requiresAuth: true, role: 'SHOP_OWNER' as UserRole },
  },

  // Catch-all
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from) => {
  const auth = useAuthStore()

  // Authenticated non-customers visiting customer-facing discovery pages:
  // send them to their own dashboard.
  const customerDiscoveryRoutes = new Set([
    'customer-explore',
    'customer-search',
    'customer-shop-detail',
    'customer-barber-profile',
  ])
  if (
    auth.isAuthenticated &&
    auth.user &&
    auth.user.role !== 'CUSTOMER' &&
    typeof to.name === 'string' &&
    customerDiscoveryRoutes.has(to.name)
  ) {
    // Exception: a barber previewing their OWN public profile. Settings →
    // "View public page" hits this path; redirecting would send them to
    // /barber/dashboard instead of the preview they asked for.
    const isOwnProfilePreview =
      to.name === 'customer-barber-profile' &&
      auth.user.role === 'BARBER' &&
      to.params.barberId != null &&
      Number(to.params.barberId) === auth.user.id
    if (!isOwnProfilePreview) {
      return roleDashboard(auth.user.role)
    }
  }

  // Guest-only routes: redirect authenticated users to their dashboard
  if (to.meta.guest && auth.isAuthenticated && auth.user) {
    return roleDashboard(auth.user.role)
  }

  // Protected routes
  if (to.meta.requiresAuth) {
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { returnUrl: to.fullPath } }
    }
    // Role check
    if (to.meta.role && auth.user?.role !== to.meta.role) {
      return { name: 'login' }
    }
  }

  return true
})

function roleDashboard(role: UserRole) {
  switch (role) {
    case 'CUSTOMER':
      return '/customer/explore'
    case 'BARBER':
      return '/barber/dashboard'
    case 'SHOP_OWNER':
      return '/owner/overview'
  }
}

export { roleDashboard }
export default router
