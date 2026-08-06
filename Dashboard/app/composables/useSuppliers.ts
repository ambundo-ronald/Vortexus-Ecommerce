export interface SupplierPartner {
  id: number
  name: string
  code: string
}

export interface SupplierUser {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  is_active: boolean
}

export interface SupplierItem {
  id: number
  status: 'pending' | 'approved' | 'suspended' | string
  company_name: string
  contact_name: string
  phone: string
  country_code: string
  website: string
  notes: string
  status_note: string
  account_manager?: { id: number, email: string, name: string } | null
  partner: SupplierPartner
  user: SupplierUser
  created_at: string
  updated_at: string
  metrics?: Record<string, any>
  payments?: Record<string, any>
  offers?: any[]
  product_requests?: any[]
  orders?: any[]
  allocations?: any[]
}

export interface SupplierPayload {
  status?: string
  company_name?: string
  contact_name?: string
  phone?: string
  country_code?: string
  website?: string
  notes?: string
  status_note?: string
  account_manager_id?: number | null
}

export interface SupplierCreatePayload extends SupplierPayload {
  email: string
  password?: string
  first_name?: string
  last_name?: string
  partner_code?: string
}

export interface SupplierListParams {
  status?: string
  search?: string
  page?: number
  pageSize?: number
}

export interface SupplierListResponse {
  results: SupplierItem[]
  pagination?: {
    page: number
    page_size: number
    total: number
    num_pages: number
    has_next: boolean
  }
  summary?: {
    total: number
    pending: number
    approved: number
    suspended: number
  }
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

export function useSuppliers() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getSuppliers(params: SupplierListParams = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<SupplierListResponse>('/admin/suppliers/', {
        method: 'GET',
        query: {
          status: params.status || '',
          q: params.search || '',
          page: params.page || 1,
          page_size: params.pageSize || 20,
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

  async function getSupplier(id: number | string) {
    loading.value = true
    error.value = null

    try {
      const result = await request<SupplierItem | { supplier: SupplierItem }>(`/admin/suppliers/${id}/`, {
        method: 'GET',
      })
      if ('supplier' in result)
        return { success: true, data: { ...result.supplier, ...Object.fromEntries(Object.entries(result).filter(([key]) => key !== 'supplier')) } }
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

  async function updateSupplier(id: number | string, payload: SupplierPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ supplier: SupplierItem }>(`/admin/suppliers/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.supplier }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function createSupplier(payload: SupplierCreatePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ supplier: SupplierItem }>('/admin/suppliers/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.supplier }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    createSupplier,
    getSupplier,
    getSuppliers,
    updateSupplier,
  }
}
