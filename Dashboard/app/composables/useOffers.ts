export interface OfferChoice {
  value: string
  label: string
}

export interface OfferComponentItem {
  id: number
  type: string
  range_id: number | null
  range_name: string
  value: string | number | null
  proxy_class: string
  name: string
  description: string
}

export interface OfferConditionItem extends OfferComponentItem {}

export interface OfferBenefitItem extends OfferComponentItem {
  max_affected_items: number | null
}

export interface OfferItem {
  id: number
  name: string
  slug: string
  description: string
  offer_type: string
  exclusive: boolean
  status: string
  priority: number
  start_datetime: string | null
  end_datetime: string | null
  num_applications: number
  num_orders: number
  total_discount: string | number
  condition_id: number | null
  benefit_id: number | null
  condition: OfferConditionItem | null
  benefit: OfferBenefitItem | null
  voucher_ids: number[]
}

export interface OfferPayload {
  name: string
  slug?: string
  description?: string
  offer_type: string
  exclusive?: boolean
  status?: string
  priority?: number
  start_datetime?: string | null
  end_datetime?: string | null
  condition_id: number
  benefit_id: number
}

export interface OfferComponentPayload {
  type: string
  range_id?: number | null
  value?: string | number | null
  proxy_class?: string | null
  max_affected_items?: number | null
}

export interface OfferMetadata {
  offer_types: OfferChoice[]
  offer_statuses: OfferChoice[]
  condition_types: OfferChoice[]
  benefit_types: OfferChoice[]
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useOffers() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getOfferMeta() {
    loading.value = true
    error.value = null

    try {
      const result = await request<OfferMetadata>('/admin/offers/meta/', { method: 'GET' })
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

  async function getOffers(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: OfferItem[], pagination: any }>('/admin/offers/', {
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

  async function createOffer(payload: OfferPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ offer: OfferItem }>('/admin/offers/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.offer }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateOffer(id: number, payload: Partial<OfferPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ offer: OfferItem }>(`/admin/offers/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.offer }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateOfferStatus(id: number, status: string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ offer: OfferItem }>(`/admin/offers/${id}/status/`, {
        method: 'PATCH',
        body: { status },
      })
      return { success: true, data: result.offer }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteOffer(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/offers/${id}/`, { method: 'DELETE' })
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

  async function getConditions(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: OfferConditionItem[], pagination: any }>('/admin/offers/conditions/', {
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

  async function createCondition(payload: OfferComponentPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ condition: OfferConditionItem }>('/admin/offers/conditions/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.condition }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateCondition(id: number, payload: OfferComponentPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ condition: OfferConditionItem }>(`/admin/offers/conditions/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.condition }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteCondition(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/offers/conditions/${id}/`, { method: 'DELETE' })
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

  async function getBenefits(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: OfferBenefitItem[], pagination: any }>('/admin/offers/benefits/', {
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

  async function createBenefit(payload: OfferComponentPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ benefit: OfferBenefitItem }>('/admin/offers/benefits/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.benefit }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateBenefit(id: number, payload: OfferComponentPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ benefit: OfferBenefitItem }>(`/admin/offers/benefits/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.benefit }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteBenefit(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/offers/benefits/${id}/`, { method: 'DELETE' })
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
    createBenefit,
    createCondition,
    createOffer,
    deleteBenefit,
    deleteCondition,
    deleteOffer,
    getBenefits,
    getConditions,
    getOfferMeta,
    getOffers,
    updateBenefit,
    updateCondition,
    updateOffer,
    updateOfferStatus,
  }
}
