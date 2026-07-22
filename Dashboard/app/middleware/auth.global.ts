export default defineNuxtRouteMiddleware(async (to) => {
  // Session auth depends on browser cookies. On a hard reload the server-side
  // middleware cannot see the Django session cookie reliably, so let the client
  // perform the auth check after hydration.
  if (import.meta.server)
    return

  const publicRoutes = new Set(['/login'])
  const supplierRoutes = new Set(['/supplier-dashboard'])
  const accountManagerRoutes = new Set(['/suppliers', '/supplier-product-reviews', '/supplier-offers', '/orders', '/payment-logs', '/support'])
  const auth = useAuth()

  if (!auth.hasCheckedSession.value)
    await auth.refreshSession()

  if (publicRoutes.has(to.path)) {
    if (auth.isPlatformAdmin.value)
      return navigateTo('/')
    if (auth.isAccountManager.value)
      return navigateTo('/suppliers')
    if (auth.isSupplier.value)
      return navigateTo('/supplier-dashboard')
    return
  }

  if (!auth.hasDashboardAccess.value)
    return navigateTo('/login')

  if (supplierRoutes.has(to.path) && !auth.isSupplier.value)
    return navigateTo('/')

  if (auth.isAccountManager.value) {
    const isAllowed = Array.from(accountManagerRoutes).some(route => to.path === route || to.path.startsWith(`${route}/`))
    if (to.path === '/')
      return navigateTo('/suppliers')
    if (!isAllowed)
      return navigateTo('/suppliers')
  }

  if (auth.isSupplier.value && !auth.isAdmin.value && !supplierRoutes.has(to.path))
    return navigateTo('/supplier-dashboard')
})
