export interface DashboardSummary {
  range: {
    days: number
    start: string
    end: string
  }
  currency: string
  kpis: {
    orders: number
    recent_orders: number
    revenue: number
    recent_revenue: number
    products: number
    active_products: number
    users: number
    staff_users: number
    media_assets: number
    stock_units: number
    low_stock_products: number
    out_of_stock_products: number
  }
  order_status: {
    pending: number
    completed: number
    failed: number
  }
  daily: Array<{
    date: string
    orders: number
    revenue: number
  }>
  latest_orders: Array<{
    id: number
    number: string
    customer: string
    date: string
    total: number
    currency: string
    status: string
  }>
  popular_products: Array<{
    id: number
    name: string
    category: string
    stock: number
    quantity_sold: number
    image: string
  }>
  category_share: Array<{
    name: string
    value: number
    color: string
  }>
}

export function useDashboard() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getDashboard(days = 30) {
    loading.value = true
    error.value = null
    try {
      const result = await request<DashboardSummary>('/admin/dashboard/', {
        method: 'GET',
        query: { days },
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

  return {
    error,
    getDashboard,
    loading,
  }
}
