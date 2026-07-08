export interface SearchAnalyticsSummary {
  range: {
    days: number
    start: string
    end: string
  }
  kpis: {
    total_searches: number
    image_searches: number
    zero_result_searches: number
    product_clicks: number
    search_contexts: number
    cart_conversions: number
    order_conversions: number
    search_to_cart_rate: number
    search_to_order_rate: number
  }
  top_terms: Array<{ query: string, count: number, avg_results: number, last_seen: string }>
  zero_result_terms: Array<{ query: string, count: number, last_seen: string }>
  clicked_products: Array<{ product_id: number, product_title: string, clicks: number, last_seen: string }>
  user_searches: Array<{ user_email: string, anonymous_id: string, searches: number, last_seen: string }>
  recent_events: Array<{
    id: number
    event_type: string
    source: string
    query: string
    result_count: number | null
    product_id: number | null
    product_title: string
    order_number: string
    user_email: string
    category: string
    brand: string
    created_at: string
  }>
}

export function useSearchAnalytics() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getSearchAnalytics(days = 30) {
    loading.value = true
    error.value = null
    try {
      const result = await request<SearchAnalyticsSummary>('/admin/search-analytics/', {
        method: 'GET',
        query: { days },
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  return {
    error,
    getSearchAnalytics,
    loading,
  }
}
