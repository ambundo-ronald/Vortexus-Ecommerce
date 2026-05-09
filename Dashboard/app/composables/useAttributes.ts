export interface AttributeItem {
  id: number
  product_class_id: number
  name: string
  code: string
  type: string
  required: boolean
  option_group_id: number | null
}

export interface AttributePayload {
  product_class_id: number
  name: string
  code?: string
  type: string
  required: boolean
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useAttributes() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getAttributes(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: AttributeItem[], pagination: any }>('/admin/catalog/attributes/', {
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

  async function createAttribute(payload: AttributePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ attribute: AttributeItem }>('/admin/catalog/attributes/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.attribute }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateAttribute(id: number, payload: Partial<AttributePayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ attribute: AttributeItem }>(`/admin/catalog/attributes/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.attribute }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteAttribute(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/catalog/attributes/${id}/`, {
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
    createAttribute,
    deleteAttribute,
    getAttributes,
    updateAttribute,
  }
}
