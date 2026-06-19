export interface AdminPaymentConfiguration {
  mpesa: {
    is_enabled: boolean
    is_configured: boolean
    checkout_visible: boolean
    missing_requirements: string[]
    base_url: string
    has_consumer_key: boolean
    has_consumer_secret: boolean
    shortcode: string
    has_passkey: boolean
    callback_url: string
    transaction_type: string
    timeout_seconds: number
  }
  pesapal: {
    is_enabled: boolean
    is_configured: boolean
    checkout_visible: boolean
    missing_requirements: string[]
    base_url: string
    has_consumer_key: boolean
    has_consumer_secret: boolean
    callback_url: string
    cancellation_url: string
    ipn_url: string
    ipn_id: string
    notification_type: string
    branch: string
    redirect_mode: string
    timeout_seconds: number
  }
  airtel_money: {
    is_enabled: boolean
    is_configured: boolean
    checkout_visible: boolean
    missing_requirements: string[]
    provider_name: string
    sandbox_enabled: boolean
  }
  card: {
    is_enabled: boolean
    is_configured: boolean
    checkout_visible: boolean
    missing_requirements: string[]
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
  pesapal?: {
    is_enabled?: boolean
    base_url?: string
    consumer_key?: string
    consumer_secret?: string
    callback_url?: string
    cancellation_url?: string
    ipn_url?: string
    ipn_id?: string
    notification_type?: string
    branch?: string
    redirect_mode?: string
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

export interface AdminPaymentLogItem {
  id: number
  reference: string
  method: string
  provider: string
  status: string
  amount: number
  currency: string
  payer_email: string
  payer_phone: string
  external_reference: string
  order_number: string
  metadata: Record<string, any>
  provider_payload: Record<string, any>
  reconciliation: AdminPaymentReconciliation
  events: AdminPaymentEventItem[]
  created_at: string
  updated_at: string
  paid_at?: string | null
}

export interface AdminPaymentReconciliation {
  status: string
  label: string
  severity: string
  issues: string[]
  needs_attention: boolean
}

export interface AdminPaymentEventItem {
  id: number
  kind: string
  status_before: string
  status_after: string
  external_reference: string
  message: string
  payload: Record<string, any>
  created_at: string
}

export interface AdminPaymentLogParams {
  page?: number
  pageSize?: number
  search?: string
  method?: string
  status?: string
  provider?: string
  reconciliation?: string
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

  async function getPaymentLogs(params: AdminPaymentLogParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: AdminPaymentLogItem[], pagination: any, summary: any }>('/admin/payments/logs/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          method: params.method || '',
          status: params.status || '',
          provider: params.provider || '',
          reconciliation: params.reconciliation || '',
        },
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
    getPaymentLogs,
  }
}
