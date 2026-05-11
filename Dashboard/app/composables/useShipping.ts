export interface WeightBandItem {
  id: number
  upper_limit: number
  charge: number
}

export interface WeightBasedMethodItem {
  id: number
  code: string
  name: string
  description: string
  default_weight: number
  bands: WeightBandItem[]
}

export interface WeightBasedMethodPayload {
  code?: string
  name: string
  description?: string
  default_weight?: number | string
}

export interface WeightBandPayload {
  upper_limit: number | string
  charge: number | string
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

export function useShipping() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getWeightBasedMethods(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: WeightBasedMethodItem[], pagination: any }>('/admin/shipping/weight-based/', {
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

  async function getWeightBasedMethod(id: number | string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ method: WeightBasedMethodItem }>(`/admin/shipping/weight-based/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: result.method }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function createWeightBasedMethod(payload: WeightBasedMethodPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ method: WeightBasedMethodItem }>('/admin/shipping/weight-based/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.method }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateWeightBasedMethod(id: number | string, payload: Partial<WeightBasedMethodPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ method: WeightBasedMethodItem }>(`/admin/shipping/weight-based/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.method }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteWeightBasedMethod(id: number | string) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/shipping/weight-based/${id}/`, { method: 'DELETE' })
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

  async function createWeightBand(methodId: number | string, payload: WeightBandPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ band: WeightBandItem }>(`/admin/shipping/weight-based/${methodId}/bands/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.band }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateWeightBand(methodId: number | string, bandId: number | string, payload: WeightBandPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ band: WeightBandItem }>(`/admin/shipping/weight-based/${methodId}/bands/${bandId}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.band }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteWeightBand(methodId: number | string, bandId: number | string) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/shipping/weight-based/${methodId}/bands/${bandId}/`, { method: 'DELETE' })
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
    createWeightBand,
    createWeightBasedMethod,
    deleteWeightBand,
    deleteWeightBasedMethod,
    getWeightBasedMethod,
    getWeightBasedMethods,
    updateWeightBand,
    updateWeightBasedMethod,
  }
}
