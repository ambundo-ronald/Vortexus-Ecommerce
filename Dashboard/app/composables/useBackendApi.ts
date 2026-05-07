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
    const method = String(options.method || 'GET').toUpperCase()
    const headers = { ...(options.headers || {}) }

    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      headers['X-CSRFToken'] = await ensureCsrfToken()
    }

    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        credentials: 'include',
        ...options,
        method,
        headers,
      })
    }
    catch (err: any) {
      if (import.meta.client && [401, 403].includes(Number(err?.status || err?.statusCode))) {
        const route = useRoute()
        if (route.path !== '/login')
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
