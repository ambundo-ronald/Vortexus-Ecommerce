interface AdminUser {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_staff: boolean
}

export function useAdminAuth() {
  const user = useState<AdminUser | null>('admin-auth-user', () => null)
  const checked = useState<boolean>('admin-auth-checked', () => false)
  const loading = useState<boolean>('admin-auth-loading', () => false)
  const { request } = useBackendApi()

  const isAuthenticated = computed(() => Boolean(user.value?.is_staff))

  async function fetchCurrentUser() {
    loading.value = true
    try {
      const result = await request<{ user: AdminUser }>('/account/me/', { method: 'GET' })
      user.value = result.user?.is_staff ? result.user : null
      checked.value = true
      return { success: Boolean(user.value), user: user.value }
    }
    catch (err: any) {
      user.value = null
      checked.value = true
      return {
        success: false,
        error: err?.data?.error?.detail || err?.message || 'Not authenticated',
      }
    }
    finally {
      loading.value = false
    }
  }

  async function login(identifier: string, password: string) {
    loading.value = true
    try {
      const result = await request<{ user: AdminUser }>('/account/login/', {
        method: 'POST',
        body: { identifier, password },
      })

      if (!result.user?.is_staff) {
        await logout()
        return { success: false, error: 'This dashboard requires a staff or admin account.' }
      }

      user.value = result.user
      checked.value = true
      return { success: true, user: user.value }
    }
    catch (err: any) {
      user.value = null
      checked.value = true
      return {
        success: false,
        error: err?.data?.error?.detail || err?.message || 'Login failed',
      }
    }
    finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await request('/account/logout/', { method: 'POST' })
    }
    catch {
      // The local dashboard should still clear its state if the server session is already gone.
    }
    user.value = null
    checked.value = true
    await navigateTo('/login')
  }

  return {
    checked,
    fetchCurrentUser,
    isAuthenticated,
    loading,
    login,
    logout,
    user,
  }
}
