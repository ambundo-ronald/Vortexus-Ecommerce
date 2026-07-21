export default defineNuxtRouteMiddleware(async (to) => {
  // Session auth depends on browser cookies. On a hard reload the server-side
  // middleware cannot see the Django session cookie reliably, so let the client
  // perform the auth check after hydration.
  if (import.meta.server)
    return

  const publicRoutes = new Set(['/login'])
  const supplierRoutes = new Set(['/supplier-dashboard'])
  const auth = useAuth()

  if (!auth.hasCheckedSession.value)
    await auth.refreshSession()

  if (publicRoutes.has(to.path)) {
    if (auth.isAdmin.value)
      return navigateTo('/')
    if (auth.isSupplier.value)
      return navigateTo('/supplier-dashboard')
    return
  }

  if (!auth.hasDashboardAccess.value)
    return navigateTo('/login')

  if (supplierRoutes.has(to.path) && !auth.isSupplier.value)
    return navigateTo('/')

  if (auth.isSupplier.value && !auth.isAdmin.value && !supplierRoutes.has(to.path))
    return navigateTo('/supplier-dashboard')
})
