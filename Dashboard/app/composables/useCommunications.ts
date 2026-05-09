export interface CommunicationTemplate {
  id: number
  code: string
  name: string
  category: string
  email_subject_template: string
  email_body_template: string
  email_body_html_template: string
  sms_template: string
}

export interface CommunicationTemplatePayload {
  name?: string
  category?: string
  email_subject_template?: string
  email_body_template?: string
  email_body_html_template?: string
  sms_template?: string
}

function readApiError(err: any) {
  const detail = err?.data?.error?.detail || err?.data?.detail || err?.message
  const errors = err?.data?.error?.errors || err?.data

  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([field, messages]) => {
        const text = Array.isArray(messages) ? messages.join(' ') : String(messages)
        return `${field}: ${text}`
      })
      .join(' ')
  }

  return typeof detail === 'string' ? detail : 'Unknown error'
}

export function useCommunications() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getCommunications() {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: CommunicationTemplate[] }>('/admin/communications/', {
        method: 'GET',
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

  async function getCommunication(code: string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ communication: CommunicationTemplate }>(`/admin/communications/${encodeURIComponent(code)}/`, {
        method: 'GET',
      })
      return { success: true, data: result.communication }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updateCommunication(code: string, payload: CommunicationTemplatePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ communication: CommunicationTemplate }>(`/admin/communications/${encodeURIComponent(code)}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.communication }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getCommunication,
    getCommunications,
    updateCommunication,
  }
}
