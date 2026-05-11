export interface ReportDefinition {
  code: string
  name: string
  description: string
}

export interface ReportDetail {
  report: string
  summary: Record<string, any>
  results: any[]
  pagination: {
    page: number
    page_size: number
    total: number
    num_pages: number
    has_next: boolean
  }
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useReports() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getReports() {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: ReportDefinition[] }>('/admin/reports/', {
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

  async function getReport(reportName: string, params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<ReportDetail>(`/admin/reports/${reportName}/`, {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
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

  return {
    loading,
    error,
    getReport,
    getReports,
  }
}
