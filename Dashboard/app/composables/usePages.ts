export interface CmsPageItem {
  id: number
  url: string
  title: string
  content: string
  registration_required: boolean
}

export interface CmsPagePayload {
  url: string
  title: string
  content: string
  registration_required?: boolean
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

export function usePages() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getPages(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: CmsPageItem[], pagination: any }>('/admin/pages/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 200,
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

  async function getPage(id: number | string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ page: CmsPageItem }>(`/admin/pages/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: result.page }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function createPage(payload: CmsPagePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ page: CmsPageItem }>('/admin/pages/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.page }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updatePage(id: number | string, payload: Partial<CmsPagePayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ page: CmsPageItem }>(`/admin/pages/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.page }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deletePage(id: number | string) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/pages/${id}/`, { method: 'DELETE' })
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

  return {
    loading,
    error,
    createPage,
    deletePage,
    getPage,
    getPages,
    updatePage,
  }
}
