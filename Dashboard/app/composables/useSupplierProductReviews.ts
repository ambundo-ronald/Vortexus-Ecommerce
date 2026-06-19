import type { SupplierItem } from '~/composables/useSuppliers'

export interface SupplierProductReviewProduct {
  id: number
  title: string
  upc?: string
  sku?: string
  image?: string
  thumbnail?: string
  price?: number | string | null
  currency?: string
  status?: string
  isPublic?: boolean
}

export interface SupplierProductReviewItem {
  id: number
  status: string
  review_note: string
  supplier_note: string
  submitted_at: string
  reviewed_at: string | null
  supplier: SupplierItem
  product: SupplierProductReviewProduct
  reviewed_by: { id: number, email: string } | null
}

export interface SupplierProductReviewPayload {
  status: string
  review_note?: string
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

export function useSupplierProductReviews() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getReviews(params: { status?: string, supplierId?: number | string, page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: SupplierProductReviewItem[], pagination: any }>('/admin/supplier-products/reviews/', {
        method: 'GET',
        query: {
          status: params.status || '',
          supplier_id: params.supplierId || '',
          page: params.page || 1,
          page_size: params.pageSize || 24,
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

  async function updateReview(id: number | string, payload: SupplierProductReviewPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ submission: SupplierProductReviewItem }>(`/admin/supplier-products/reviews/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.submission }
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
    getReviews,
    updateReview,
  }
}
