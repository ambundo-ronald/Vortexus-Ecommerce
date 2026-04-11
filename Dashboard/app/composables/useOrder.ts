import type { OrderTableRow } from "~/types/OrderTableRow";

export interface OrderListParams {
  page?: number
  pageSize?: number
  search?: string
  status?: string
  sortBy?: string
  sortDir?: 'asc' | 'desc'
}

export interface UpdateOrderStatusPayload {
  status: string
  note?: string
  tracking_reference?: string
}

function mapOrderSort(sortBy?: string, sortDir: 'asc' | 'desc' = 'asc') {
  if (sortBy === 'orderTotal')
    return sortDir === 'desc' ? 'total_desc' : 'total_asc'
  if (sortBy === 'status')
    return 'status'
  return 'newest'
}

export function useOrder() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getOrders(params: OrderListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: OrderTableRow[], pagination: any, summary: any }>('/admin/orders/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 10,
          q: params.search || '',
          status: params.status || '',
          sort_by: mapOrderSort(params.sortBy, params.sortDir || 'asc'),
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

  async function getOrder(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ order: any }>(`/admin/orders/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: result.order }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updateOrderStatus(id: number | string, payload: UpdateOrderStatusPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ detail: string, order: any }>(`/admin/orders/${id}/status/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.order, detail: result.detail }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getOrder,
    getOrders,
    updateOrderStatus,
  }
}
