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
    email: user.email || '',
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    phone: user.phone || '',
    company: user.company || '',
    role: user.role?.toLowerCase() === 'admin'
      ? 'admin'
      : user.role?.toLowerCase() === 'staff'
        ? 'staff'
        : 'customer',
    status: user.is_active ? 'active' : 'suspended',
    isSupplier: user.supplier?.is_supplier || false,
    supplierStatus: user.supplier?.status || '',
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
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
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
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
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
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
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
      error.value = err?.data?.error?.detail || err?.message || 'Unknown error'
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    getUsers,
    getUser,
    createUser,
    updateUser,
  }
}
