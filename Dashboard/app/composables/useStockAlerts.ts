export interface StockAlertItem {
  id: number
  status: string
  threshold: number
  date_created: string
  date_closed: string | null
  stockrecord: {
    id: number
    partner_sku: string
    num_in_stock: number
    product_id: number
    product_title: string
  }
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useStockAlerts() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getStockAlerts(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: StockAlertItem[], pagination: any }>('/admin/catalog/stock-alerts/', {
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

  async function updateStockAlert(id: number, payload: { status: string }) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ stock_alert: StockAlertItem }>(`/admin/catalog/stock-alerts/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.stock_alert }
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
    loading,
    error,
    getStockAlerts,
    updateStockAlert,
  }
}
