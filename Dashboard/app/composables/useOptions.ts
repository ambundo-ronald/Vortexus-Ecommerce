export interface OptionItem {
  id: number
  name: string
  code: string
  type: string
  required: boolean
  help_text: string
  order: number
}

export interface OptionPayload {
  name: string
  code?: string
  type: string
  required: boolean
  help_text?: string
  order: number
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useOptions() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getOptions(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: OptionItem[], pagination: any }>('/admin/catalog/options/', {
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

  async function createOption(payload: OptionPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ option: OptionItem }>('/admin/catalog/options/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.option }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateOption(id: number, payload: Partial<OptionPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ option: OptionItem }>(`/admin/catalog/options/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.option }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteOption(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/catalog/options/${id}/`, {
        method: 'DELETE',
      })
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
    createOption,
    deleteOption,
    getOptions,
    updateOption,
  }
}
