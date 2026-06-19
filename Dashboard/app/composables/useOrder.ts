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

export interface UpdateOrderShippingAddressPayload {
  first_name?: string
  last_name?: string
  line1?: string
  line2?: string
  line3?: string
  line4?: string
  state?: string
  postcode?: string
  country_code?: string
  phone_number?: string
  notes?: string
  latitude?: string | number | null
  longitude?: string | number | null
  location_label?: string
}

export interface CreateOrderNotePayload {
  message: string
  note_type?: string
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
      error.value = readApiError(err)
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
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getOrderLine(orderNumber: string, lineId: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ line: any }>(`/admin/orders/${encodeURIComponent(orderNumber)}/lines/${lineId}/`, {
        method: 'GET',
      })
      return { success: true, data: result.line }
    }
    catch (err: any) {
      error.value = readApiError(err)
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
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateOrderShippingAddress(orderNumber: string, payload: UpdateOrderShippingAddressPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ shipping_address: any }>(`/admin/orders/${encodeURIComponent(orderNumber)}/shipping-address/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.shipping_address }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function getOrderNotes(orderNumber: string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: any[] }>(`/admin/orders/${encodeURIComponent(orderNumber)}/notes/`, {
        method: 'GET',
      })
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

  async function addOrderNote(orderNumber: string, payload: CreateOrderNotePayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ note: any }>(`/admin/orders/${encodeURIComponent(orderNumber)}/notes/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.note }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    addOrderNote,
    getOrderLine,
    getOrderNotes,
    loading,
    error,
    getOrder,
    getOrders,
    updateOrderStatus,
    updateOrderShippingAddress,
  }
}
