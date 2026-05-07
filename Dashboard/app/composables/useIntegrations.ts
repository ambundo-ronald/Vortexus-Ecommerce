export interface IntegrationConnection {
  id: number
  name: string
  partner?: number | null
  partner_name?: string
  connection_type: string
  base_url: string
  auth_type: string
  credential_source: string
  secret_env_prefix?: string
  has_api_key: boolean
  has_api_secret: boolean
  default_company?: string
  default_warehouse?: string
  poll_interval_minutes?: number
  status: string
  is_active: boolean
  last_successful_sync_at?: string | null
  last_failed_sync_at?: string | null
  created_at: string
  updated_at: string
}

export interface IntegrationLog {
  id: number
  connection: number
  connection_name: string
  direction: string
  entity_type: string
  external_reference: string
  status: string
  payload_excerpt?: Record<string, any>
  error_message?: string
  created_at: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.data?.connection?.[0]
    || err?.message
    || 'Unknown error'
}

export function useIntegrations() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getConnections() {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: IntegrationConnection[] }>('/admin/integrations/', {
        method: 'GET',
      })
      return { success: true, data: result.results || [] }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getLogs(connectionId: number) {
    try {
      const result = await request<{ results: IntegrationLog[] }>(`/admin/integrations/${connectionId}/logs/`, {
        method: 'GET',
      })
      return { success: true, data: result.results || [] }
    }
    catch (err: any) {
      return { success: false, error: readApiError(err), data: [] }
    }
  }

  async function testConnection(connectionId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ result: Record<string, any> }>(`/admin/integrations/${connectionId}/erpnext/test/`, {
        method: 'POST',
      })
      return { success: true, data: result.result }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function syncStock(connectionId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ summary: Record<string, any> }>(`/admin/integrations/${connectionId}/erpnext/stock-sync/`, {
        method: 'POST',
      })
      return { success: true, data: result.summary }
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
    getConnections,
    getLogs,
    testConnection,
    syncStock,
  }
}
