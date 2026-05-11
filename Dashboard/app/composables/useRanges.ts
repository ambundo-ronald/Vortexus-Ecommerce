export interface RangeItem {
  id: number
  name: string
  slug: string
  description: string
  is_public: boolean
  includes_all_products: boolean
  num_products: number
}

export interface RangeProductItem {
  id: number
  title: string
  upc: string
}

export interface RangePayload {
  name: string
  slug?: string
  description?: string
  is_public: boolean
  includes_all_products: boolean
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useRanges() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getRanges(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: RangeItem[], pagination: any }>('/admin/ranges/', {
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

  async function createRange(payload: RangePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ range: RangeItem }>('/admin/ranges/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.range }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateRange(id: number, payload: Partial<RangePayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ range: RangeItem }>(`/admin/ranges/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.range }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteRange(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/ranges/${id}/`, { method: 'DELETE' })
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

  async function getRangeProducts(id: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: RangeProductItem[] }>(`/admin/ranges/${id}/products/`, { method: 'GET' })
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

  async function addRangeProduct(id: number, productId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ range: RangeItem }>(`/admin/ranges/${id}/products/`, {
        method: 'POST',
        body: { product_id: productId },
      })
      return { success: true, data: result.range }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function removeRangeProduct(id: number, productId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ range: RangeItem }>(`/admin/ranges/${id}/products/`, {
        method: 'DELETE',
        body: { product_id: productId },
      })
      return { success: true, data: result.range }
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
    addRangeProduct,
    createRange,
    deleteRange,
    getRangeProducts,
    getRanges,
    removeRangeProduct,
    updateRange,
  }
}
