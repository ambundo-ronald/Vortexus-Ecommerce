export interface SupplierWorkspaceMetrics {
  product_count: number
  public_product_count: number
  pending_product_count: number
  low_stock_count: number
  inventory_units: number
  order_count: number
  open_order_count: number
  delivered_order_count: number
  cancelled_order_count: number
  gross_sales_total: number | string
  confirmed_payment_total: number | string
  pending_payment_total: number | string
}

export interface SupplierWorkspacePaymentSummary {
  basis: string
  status: string
  confirmed_total: number | string
  pending_total: number | string
  paid_out_total: number | string
}

export interface SupplierWorkspaceDashboard {
  supplier: any
  metrics: SupplierWorkspaceMetrics
  payments: SupplierWorkspacePaymentSummary
  orders?: {
    count: number
    open_count: number
  }
}

function extractSupplierError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Supplier workspace is not available.'
}

export function useSupplierWorkspace() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getDashboard() {
    loading.value = true
    error.value = null
    try {
      const result = await request<SupplierWorkspaceDashboard>('/supplier/dashboard/', {
        method: 'GET',
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = extractSupplierError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getProducts(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: any[], pagination: any }>('/supplier/products/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 8,
        },
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = extractSupplierError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getOrders(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: any[], pagination: any }>('/supplier/orders/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 8,
        },
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = extractSupplierError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getDashboard,
    getProducts,
    getOrders,
  }
}
