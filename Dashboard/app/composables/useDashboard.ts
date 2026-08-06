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
  site_analytics?: {
    kpis: {
      sessions: number
      page_views: number
      product_views: number
      cart_sessions: number
      checkout_started: number
      checkout_completed: number
      checkout_rate: number
      checkout_completion_rate: number
      checkout_dropoff_rate: number
      bounce_rate: number
      voucher_sessions: number
      avg_session_duration_seconds: number
    }
    checkout_funnel: Array<{ step: string, sessions: number }>
    top_pages: Array<{ path: string, title: string, views: number, sessions: number }>
    top_product_views: Array<{ product_id: number | string, product_title: string, views: number, sessions: number }>
    top_referrers: Array<{ referrer: string, visits: number }>
    activity_heatmap: Array<{ weekday: number, hour: number, sessions: number }>
    busiest_hours: Array<{ weekday: number, hour: number, sessions: number }>
    recent_sessions: Array<{
      session_key: string
      customer: string
      first_page: string
      last_page: string
      first_seen: string
      last_seen: string
      duration_seconds: number
      page_views: number
      event_count: number
      checkout_step: string
      converted: boolean
      journey: Array<{
        event_type: string
        label: string
        path: string
        product_title: string
        query: string
        order_number: string
        created_at: string
      }>
    }>
  }
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
