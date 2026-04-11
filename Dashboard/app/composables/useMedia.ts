export interface MediaListParams {
  page?: number
  pageSize?: number
  search?: string
  productId?: string | number
}

export interface MediaAsset {
  id: number
  name: string
  url: string
  alt: string
  productId: number
  productTitle: string
  displayOrder: number
  createdAt?: string
}

export function useMedia() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getMedia(params: MediaListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: MediaAsset[], pagination: any, summary: any }>('/admin/media/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 24,
          q: params.search || '',
          product_id: params.productId || '',
        },
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function uploadMedia(file: File, productId: string | number, alt = '') {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('product_id', String(productId))
    formData.append('alt', alt)
    try {
      const result = await request<{ media: MediaAsset }>('/admin/media/', {
        method: 'POST',
        body: formData,
      })
      return { success: true, data: result.media }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  async function deleteMedia(id: number) {
    try {
      await request(`/admin/media/${id}/`, {
        method: 'DELETE',
      })
      return { success: true }
    }
    catch (err: any) {
      return { success: false, error: err?.data?.error?.detail || err?.message || 'Unknown error' }
    }
  }

  return {
    loading,
    error,
    deleteMedia,
    getMedia,
    uploadMedia,
  }
}
