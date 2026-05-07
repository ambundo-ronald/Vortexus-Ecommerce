export default defineNuxtRouteMiddleware(async (to) => {
  // Session auth depends on browser cookies. On a hard reload the server-side
  // middleware cannot see the Django session cookie reliably, so let the client
  // perform the auth check after hydration.
  if (import.meta.server)
    return

  const publicRoutes = new Set(['/login'])
  const auth = useAuth()

  if (!auth.hasCheckedSession.value)
    await auth.refreshSession()

  if (publicRoutes.has(to.path)) {
    if (auth.isAdmin.value)
      return navigateTo('/')
    return
  }

  if (!auth.isAdmin.value)
    return navigateTo('/login')
})
