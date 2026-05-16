export interface AdminEmailConfiguration {
  is_enabled: boolean
  is_configured: boolean
  host: string
  port: number
  username: string
  password?: string
  has_password: boolean
  use_tls: boolean
  use_ssl: boolean
  timeout_seconds: number
  from_email: string
  reply_to_email: string
  sales_recipients: string
  updated_at?: string
}

export interface AdminEmailConfigurationPayload {
  email: Partial<AdminEmailConfiguration>
}

export interface AdminEmailLogItem {
  id: number
  event_type: string
  status: string
  recipient: string
  subject: string
  related_object_type: string
  related_object_id: string
  error_message: string
  metadata: Record<string, any>
  sent_at?: string | null
  created_at: string
  updated_at: string
}

export interface AdminEmailSuppressionItem {
  id: number
  email: string
  reason: string
  source: string
  note: string
  metadata: Record<string, any>
  created_by: string
  created_at: string
  updated_at: string
}

export interface AdminEmailTemplateItem {
  id: number
  code: string
  name: string
  category: string
  email_subject_template: string
  email_body_template: string
  email_body_html_template: string
  sms_template: string
}

export interface AdminEmailLogParams {
  page?: number
  pageSize?: number
  search?: string
  eventType?: string
  status?: string
  recipient?: string
  relatedObjectType?: string
  relatedObjectId?: string
  dateFrom?: string
  dateTo?: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
}

export function useEmailConfig() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getEmailConfig() {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ email: AdminEmailConfiguration }>('/admin/email/config/', { method: 'GET' })
      return { success: true, data: result.email }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updateEmailConfig(payload: AdminEmailConfigurationPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ email: AdminEmailConfiguration }>('/admin/email/config/', {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.email }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function sendTestEmail(recipient: string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ detail: string, sent: number }>('/admin/email/test/', {
        method: 'POST',
        body: { recipient },
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

  async function getEmailLogs(params: AdminEmailLogParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: AdminEmailLogItem[], pagination: any, summary: any }>('/admin/email/logs/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          event_type: params.eventType || '',
          status: params.status || '',
          recipient: params.recipient || '',
          related_object_type: params.relatedObjectType || '',
          related_object_id: params.relatedObjectId || '',
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

  async function getEmailLog(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ email_log: AdminEmailLogItem }>(`/admin/email/logs/${id}/`, { method: 'GET' })
      return { success: true, data: result.email_log }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function retryEmailLog(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ detail: string, sent: number }>(`/admin/email/logs/${id}/retry/`, {
        method: 'POST',
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

  async function getEmailSuppressions(params: { page?: number, pageSize?: number, search?: string, reason?: string } = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: AdminEmailSuppressionItem[], pagination: any, summary: any }>('/admin/email/suppressions/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          reason: params.reason || '',
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

  async function createEmailSuppression(payload: Partial<AdminEmailSuppressionItem>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ suppression: AdminEmailSuppressionItem }>('/admin/email/suppressions/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.suppression }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteEmailSuppression(id: number | string) {
    loading.value = true
    error.value = null
    try {
      await request(`/admin/email/suppressions/${id}/`, { method: 'DELETE' })
      return { success: true }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getEmailTemplates(search = '') {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: AdminEmailTemplateItem[] }>('/admin/email/templates/', {
        method: 'GET',
        query: { q: search },
      })
      return { success: true, data: result.results }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updateEmailTemplate(code: string, payload: Partial<AdminEmailTemplateItem>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ template: AdminEmailTemplateItem }>(`/admin/email/templates/${code}/`, {
        method: 'PATCH',
        body: { template: payload },
      })
      return { success: true, data: result.template }
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
    getEmailConfig,
    updateEmailConfig,
    sendTestEmail,
    getEmailLogs,
    getEmailLog,
    retryEmailLog,
    getEmailSuppressions,
    createEmailSuppression,
    deleteEmailSuppression,
    getEmailTemplates,
    updateEmailTemplate,
  }
}
