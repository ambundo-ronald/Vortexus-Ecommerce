export interface AuditLogItem {
  id: number
  event_type: string
  status: string
  actor_id: number | null
  actor_email: string
  actor_role: string
  request_method: string
  path: string
  ip_address: string | null
  user_agent: string
  target_type: string
  target_id: string
  target_repr: string
  message: string
  metadata: Record<string, any>
  created_at: string
}

export interface AuditLogListParams {
  page?: number
  pageSize?: number
  search?: string
  eventType?: string
  actorEmail?: string
  targetType?: string
  targetId?: string
  path?: string
  status?: string
  dateFrom?: string
  dateTo?: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useAuditLogs() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getAuditLogs(params: AuditLogListParams = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: AuditLogItem[], pagination: any }>('/admin/audit-logs/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          event_type: params.eventType || '',
          actor_email: params.actorEmail || '',
          target_type: params.targetType || '',
          target_id: params.targetId || '',
          path: params.path || '',
          status: params.status || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
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

  async function getAuditLog(id: number | string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ audit_log: AuditLogItem }>(`/admin/audit-logs/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: result.audit_log }
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
    getAuditLog,
    getAuditLogs,
  }
}
