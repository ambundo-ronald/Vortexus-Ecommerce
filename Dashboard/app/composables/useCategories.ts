export interface CategoryItem {
  id: number
  name: string
  slug: string
  description: string
  is_public: boolean
  parent_id: number | null
  depth: number
  numchild: number
}

export interface CategoryPayload {
  name: string
  slug?: string
  description?: string
  is_public: boolean
  parent_id?: number | null
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useCategories() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getCategories(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: CategoryItem[], pagination: any }>('/admin/catalog/categories/', {
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

  async function createCategory(payload: CategoryPayload) {
    loading.value = true
    error.value = null

    try {
      const path = payload.parent_id
        ? `/admin/catalog/categories/${payload.parent_id}/children/`
        : '/admin/catalog/categories/'
      const result = await request<{ category: CategoryItem }>(path, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.category }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateCategory(id: number, payload: Partial<CategoryPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ category: CategoryItem }>(`/admin/catalog/categories/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.category }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteCategory(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/catalog/categories/${id}/`, {
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
    createCategory,
    deleteCategory,
    getCategories,
    updateCategory,
  }
}
