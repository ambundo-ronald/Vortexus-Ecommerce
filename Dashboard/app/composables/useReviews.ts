export interface ReviewItem {
  id: number
  product_id: number | null
  product_title: string
  score: number
  title: string
  body: string
  user_id: number | null
  name: string
  email: string
  status: number
  status_label?: string
  date_created: string | null
}

export interface ReviewPayload {
  status?: number
  title?: string
  body?: string
  score?: number
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useReviews() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getReviews(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: ReviewItem[], pagination: any }>('/admin/reviews/', {
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

  async function updateReview(id: number, payload: ReviewPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ review: ReviewItem }>(`/admin/reviews/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.review }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteReview(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/reviews/${id}/`, { method: 'DELETE' })
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
    deleteReview,
    getReviews,
    updateReview,
  }
}
