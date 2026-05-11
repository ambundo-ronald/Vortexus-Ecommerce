import type { UserTableRow } from "~/types/UserTableRow";

export interface UserListParams {
  page?: number
  pageSize?: number
  search?: string
  role?: string
  status?: string
  sortBy?: string
}

export interface UserFormPayload {
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  company?: string
  role?: string
  status?: string
  password?: string
}

export interface UserProductAlert {
  id: number
  product_id: number
  product_title: string
  email: string
  status: string
  key: string
  date_created: string
  date_confirmed: string | null
  date_cancelled: string | null
  date_closed: string | null
}

function extractApiError(err: any) {
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

  if (typeof detail === 'string')
    return detail

  return 'Unknown error'
}

function mapUserSort(sortBy?: string) {
  if (sortBy === 'email')
    return 'email'
  if (sortBy === 'role')
    return 'role'
  if (sortBy === 'status')
    return 'status'
  if (sortBy === 'name')
    return 'name'
  return 'newest'
}

function mapUserDetailToForm(user: any) {
  return {
    id: user.id,
    username: user.username || '',
    email: user.email || '',
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    name: user.name || '',
    phone: user.phone || '',
    company: user.company || '',
    role: user.role?.toLowerCase() === 'admin'
      ? 'admin'
      : user.role?.toLowerCase() === 'staff'
        ? 'staff'
        : 'customer',
    status: user.is_active ? 'active' : 'suspended',
    isActive: !!user.is_active,
    isStaff: !!user.is_staff,
    isSuperuser: !!user.is_superuser,
    dateJoined: user.date_joined || '',
    lastLogin: user.last_login || '',
    countryCode: user.country_code || '',
    preferredCurrency: user.preferred_currency || '',
    receiveOrderUpdates: !!user.receive_order_updates,
    receiveMarketingEmails: !!user.receive_marketing_emails,
    isSupplier: user.supplier?.is_supplier || false,
    supplierStatus: user.supplier?.status || '',
    supplierCompanyName: user.supplier?.company_name || '',
  }
}

export function useUser() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getUsers(params: UserListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: UserTableRow[], pagination: any, summary: any }>('/admin/users/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 10,
          q: params.search || '',
          role: params.role || '',
          status: params.status || '',
          sort_by: mapUserSort(params.sortBy),
        },
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getUser(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ user: any }>(`/admin/users/${id}/`, {
        method: 'GET',
      })
      return { success: true, data: mapUserDetailToForm(result.user), raw: result.user }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function createUser(payload: UserFormPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ user: any }>('/admin/users/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: mapUserDetailToForm(result.user), raw: result.user }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateUser(id: number | string, payload: Partial<UserFormPayload>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ user: any }>(`/admin/users/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: mapUserDetailToForm(result.user), raw: result.user }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function generatePasswordReset(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ detail: string, uid: string, token: string, email: string }>(`/admin/users/${id}/password-reset/`, {
        method: 'POST',
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getUserProductAlerts(id: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: UserProductAlert[] }>(`/admin/users/${id}/product-alerts/`, {
        method: 'GET',
      })
      return { success: true, data: result.results }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function cancelUserProductAlert(userId: number | string, alertId: number | string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ alert: UserProductAlert }>(`/admin/users/${userId}/product-alerts/${alertId}/`, {
        method: 'DELETE',
      })
      return { success: true, data: result.alert }
    }
    catch (err: any) {
      error.value = extractApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  return {
    cancelUserProductAlert,
    loading,
    error,
    generatePasswordReset,
    getUserProductAlerts,
    getUsers,
    getUser,
    createUser,
    updateUser,
  }
}
