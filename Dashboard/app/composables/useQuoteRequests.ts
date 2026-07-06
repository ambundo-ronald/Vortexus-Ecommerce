import type { AuditLogItem } from '~/composables/useAuditLogs'

export interface QuoteRequestItem extends AuditLogItem {
  customer_name: string
  customer_email: string
  customer_phone: string
  company: string
  product_id: number | null
  product_title: string
  message_text: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

function mapQuoteRequest(log: AuditLogItem): QuoteRequestItem {
  const metadata = log.metadata || {}
  return {
    ...log,
    customer_name: metadata.name || log.actor_email || 'Customer',
    customer_email: metadata.email || log.actor_email || '',
    customer_phone: metadata.phone || '',
    company: metadata.company || '',
    product_id: metadata.product_id || (log.target_id ? Number(log.target_id) : null),
    product_title: metadata.product_title || log.target_repr || 'General quotation',
    message_text: metadata.message || log.message || '',
  }
}

export function useQuoteRequests() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getQuoteRequests(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: AuditLogItem[], pagination: any }>('/admin/audit-logs/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 200,
          event_type: 'quotes.requested',
        },
      })
      return {
        success: true,
        data: {
          results: (result.results || []).map(mapQuoteRequest),
          pagination: result.pagination,
        },
      }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getQuoteRequest(id: number | string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ audit_log: AuditLogItem }>(`/admin/audit-logs/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: mapQuoteRequest(result.audit_log) }
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
    getQuoteRequest,
    getQuoteRequests,
  }
}
