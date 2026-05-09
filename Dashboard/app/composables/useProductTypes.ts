export interface ProductTypeItem {
  id: number
  name: string
  slug: string
  requires_shipping: boolean
  track_stock: boolean
}

export interface ProductTypePayload {
  name: string
  slug?: string
  requires_shipping: boolean
  track_stock: boolean
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useProductTypes() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getProductTypes(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: ProductTypeItem[], pagination: any }>('/admin/catalog/product-types/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 100,
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

  async function createProductType(payload: ProductTypePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ product_type: ProductTypeItem }>('/admin/catalog/product-types/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.product_type }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateProductType(id: number, payload: Partial<ProductTypePayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ product_type: ProductTypeItem }>(`/admin/catalog/product-types/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.product_type }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteProductType(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/catalog/product-types/${id}/`, {
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
    createProductType,
    deleteProductType,
    getProductTypes,
    updateProductType,
  }
}
