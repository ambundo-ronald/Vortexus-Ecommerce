export interface MarketingBlock {
  id: number
  title: string
  slug: string
  placement: string
  headline: string
  body: string
  eyebrow: string
  image_url: string
  image_alt: string
  cta_text: string
  cta_url: string
  background_color: string
  text_color: string
  sort_order: number
  is_active: boolean
  starts_at: string | null
  ends_at: string | null
  metadata: Record<string, any>
  is_current?: boolean
  created_at?: string
  updated_at?: string
}

export interface MarketingBlockPayload {
  title: string
  slug: string
  placement: string
  headline?: string
  body?: string
  eyebrow?: string
  image_url?: string
  image_alt?: string
  cta_text?: string
  cta_url?: string
  background_color?: string
  text_color?: string
  sort_order?: number
  is_active?: boolean
  starts_at?: string | null
  ends_at?: string | null
  metadata?: Record<string, any>
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

export function useMarketingBlocks() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getMarketingBlocks(params: { page?: number, pageSize?: number, q?: string, placement?: string, status?: string } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: MarketingBlock[], pagination: any, summary: any, placements: Array<{ value: string, label: string }> }>('/admin/marketing-blocks/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 100,
          q: params.q || undefined,
          placement: params.placement || undefined,
          status: params.status || undefined,
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

  async function createMarketingBlock(payload: MarketingBlockPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ block: MarketingBlock }>('/admin/marketing-blocks/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.block }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateMarketingBlock(id: number | string, payload: Partial<MarketingBlockPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ block: MarketingBlock }>(`/admin/marketing-blocks/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.block }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteMarketingBlock(id: number | string) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/marketing-blocks/${id}/`, { method: 'DELETE' })
      return { success: true }
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
    createMarketingBlock,
    deleteMarketingBlock,
    getMarketingBlocks,
    updateMarketingBlock,
  }
}
