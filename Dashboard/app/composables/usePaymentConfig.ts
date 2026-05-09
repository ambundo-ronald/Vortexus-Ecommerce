export interface AdminPaymentConfiguration {
  mpesa: {
    is_enabled: boolean
    is_configured: boolean
    base_url: string
    has_consumer_key: boolean
    has_consumer_secret: boolean
    shortcode: string
    has_passkey: boolean
    callback_url: string
    transaction_type: string
    timeout_seconds: number
  }
  airtel_money: {
    is_enabled: boolean
    is_configured: boolean
    provider_name: string
    sandbox_enabled: boolean
  }
  card: {
    is_enabled: boolean
    is_configured: boolean
    provider_name: string
    sandbox_enabled: boolean
  }
}

export interface AdminPaymentConfigurationPayload {
  mpesa?: {
    is_enabled?: boolean
    base_url?: string
    consumer_key?: string
    consumer_secret?: string
    shortcode?: string
    passkey?: string
    callback_url?: string
    transaction_type?: string
    timeout_seconds?: number
  }
  airtel_money?: {
    is_enabled?: boolean
    provider_name?: string
  }
  card?: {
    is_enabled?: boolean
    provider_name?: string
  }
}

function readApiError(err: any) {
  return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
}

export function usePaymentConfig() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getPaymentConfig() {
    loading.value = true
    error.value = null
    try {
      const result = await request<AdminPaymentConfiguration>('/admin/payments/config/', { method: 'GET' })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updatePaymentConfig(payload: AdminPaymentConfigurationPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<AdminPaymentConfiguration>('/admin/payments/config/', {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getPaymentConfig,
    updatePaymentConfig,
  }
}
