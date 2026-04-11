export interface SupportSummary {
  kpis: Record<string, number>
  tickets: Array<Record<string, any>>
}

export function useSupport() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getSupportQueue(pageSize = 25) {
    loading.value = true
    error.value = null

    try {
      const result = await request<SupportSummary>('/admin/support/', {
        method: 'GET',
        query: { page_size: pageSize },
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
    getSupportQueue,
    loading,
  }
}
