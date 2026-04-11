export interface AdminStoreSettings {
  site_name: string
  site_domain: string
  default_currency: string
  shop_name: string
  support_email: string
  reply_to_email: string
  payment_methods: Array<{
    code: string
    name: string
    type: string
    requires_prepayment: boolean
  }>
  async_enabled: boolean
  search_host: string
}

export interface AdminProfileSettings {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  company: string
  country_code: string
  preferred_currency: string
  settings: {
    receive_order_updates: boolean
    receive_marketing_emails: boolean
  }
}

export interface AdminSettingsPayload {
  store?: Partial<Pick<AdminStoreSettings, 'site_name' | 'site_domain'>>
  profile?: {
    email?: string
    first_name?: string
    last_name?: string
    phone?: string
    company?: string
    country_code?: string
    preferred_currency?: string
    receive_order_updates?: boolean
    receive_marketing_emails?: boolean
  }
}

export function useSettings() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getSettings() {
    loading.value = true
    error.value = null
    try {
      const result = await request<{
        store: AdminStoreSettings
        profile: AdminProfileSettings
        editable: Record<string, string[]>
      }>('/admin/settings/', { method: 'GET' })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateSettings(payload: AdminSettingsPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{
        store: AdminStoreSettings
        profile: AdminProfileSettings
      }>('/admin/settings/', {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getSettings,
    updateSettings,
  }
}
