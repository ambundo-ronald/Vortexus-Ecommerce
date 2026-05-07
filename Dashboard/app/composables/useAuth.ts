export interface AdminSessionUser {
  id: number
  username?: string
  email: string
  first_name?: string
  last_name?: string
  full_name?: string
  is_staff?: boolean
  supplier?: {
    is_supplier?: boolean
    status?: string
    company_name?: string
    partner_id?: number | null
  }
}

export interface LoginPayload {
  identifier: string
  password: string
}

function readApiError(err: any) {
  return err?.data?.detail
    || err?.data?.error?.detail
    || err?.data?.non_field_errors?.[0]
    || err?.message
    || 'Something went wrong.'
}

export function useAuth() {
  const user = useState<AdminSessionUser | null>('admin-session-user', () => null)
  const hasCheckedSession = useState('admin-session-checked', () => false)
  const isLoading = useState('admin-session-loading', () => false)
  const error = useState<string | null>('admin-session-error', () => null)
  const { request, csrfToken } = useBackendApi()

  const isAuthenticated = computed(() => Boolean(user.value))
  const isAdmin = computed(() => Boolean(user.value?.is_staff))

  async function refreshSession() {
    isLoading.value = true
    error.value = null

    try {
      const response = await request<{ user: AdminSessionUser }>('/account/me/')
      user.value = response.user
      return response.user
    }
    catch (err: any) {
      user.value = null
      error.value = err?.status === 401 ? null : readApiError(err)
      return null
    }
    finally {
      hasCheckedSession.value = true
      isLoading.value = false
    }
  }

  async function login(payload: LoginPayload) {
    isLoading.value = true
    error.value = null

    try {
      const response = await request<{ user: AdminSessionUser, csrf_token?: string }>('/account/login/', {
        method: 'POST',
        body: payload,
      })

      if (!response.user?.is_staff) {
        await logout({ redirect: false })
        throw new Error('This account does not have dashboard access.')
      }

      user.value = response.user
      if (response.csrf_token)
        csrfToken.value = response.csrf_token

      hasCheckedSession.value = true
      return { success: true, user: response.user }
    }
    catch (err: any) {
      user.value = null
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      isLoading.value = false
    }
  }

  async function logout(options: { redirect?: boolean } = {}) {
    const shouldRedirect = options.redirect !== false
    isLoading.value = true
    error.value = null

    try {
      const response = await request<{ csrf_token?: string }>('/account/logout/', {
        method: 'POST',
      })
      if (response.csrf_token)
        csrfToken.value = response.csrf_token
    }
    catch {
      // The local session still needs to be cleared even if the server session is already gone.
    }
    finally {
      user.value = null
      hasCheckedSession.value = true
      isLoading.value = false
      if (shouldRedirect)
        await navigateTo('/login')
    }
  }

  return {
    user,
    hasCheckedSession,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    refreshSession,
    login,
    logout,
  }
}
