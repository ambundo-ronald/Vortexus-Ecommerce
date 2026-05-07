export interface CampaignSummary {
  range: { days: number, start: string, end: string }
  kpis: Record<string, number>
  campaigns: Array<Record<string, any>>
  product_opportunities: Array<Record<string, any>>
}

export function useCampaigns() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getCampaigns(days = 30) {
    loading.value = true
    error.value = null

    try {
      const result = await request<CampaignSummary>('/admin/campaigns/', {
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
    getCampaigns,
    loading,
  }
}
