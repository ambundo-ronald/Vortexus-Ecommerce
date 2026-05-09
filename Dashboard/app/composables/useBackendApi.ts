export function useBackendApi() {
  const config = useRuntimeConfig()
  const apiBase = (config.public.apiBase as string).replace(/\/$/, '')
  const csrfToken = useState<string | null>('backend-csrf-token', () => null)

  async function ensureCsrfToken() {
    if (csrfToken.value)
      return csrfToken.value

    const response = await $fetch<{ csrf_token: string }>(`${apiBase}/account/csrf/`, {
      credentials: 'include',
    })
    csrfToken.value = response.csrf_token
    return csrfToken.value
  }

  async function request<T>(path: string, options: Record<string, any> = {}) {
    const { redirectOnAuthError = true, ...fetchOptions } = options
    const method = String(options.method || 'GET').toUpperCase()
    const headers = { ...(fetchOptions.headers || {}) }

    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      headers['X-CSRFToken'] = await ensureCsrfToken()
    }

    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        credentials: 'include',
        ...fetchOptions,
        method,
        headers,
      })
    }
    catch (err: any) {
      if (redirectOnAuthError && import.meta.client && [401, 403].includes(Number(err?.status || err?.statusCode))) {
        const auth = useAuth()
        auth.clearSession()
        if (window.location.pathname !== '/login')
          await navigateTo('/login')
      }
      throw err
    }
  }

  return {
    apiBase,
    csrfToken,
    ensureCsrfToken,
    request,
  }
}
