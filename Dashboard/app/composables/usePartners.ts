export interface PartnerItem {
  id: number
  code: string
  name: string
  user_count: number
}

export interface PartnerUserItem {
  id: number
  email: string
  username: string
}

export interface PartnerPayload {
  name: string
  code?: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function usePartners() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getPartners(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: PartnerItem[], pagination: any }>('/admin/partners/', {
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

  async function createPartner(payload: PartnerPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ partner: PartnerItem }>('/admin/partners/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.partner }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updatePartner(id: number, payload: PartnerPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ partner: PartnerItem }>(`/admin/partners/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.partner }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deletePartner(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/partners/${id}/`, { method: 'DELETE' })
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

  async function getPartnerUsers(id: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: PartnerUserItem[] }>(`/admin/partners/${id}/users/`, { method: 'GET' })
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

  async function linkPartnerUser(partnerId: number, userId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ partner: PartnerItem }>(`/admin/partners/${partnerId}/users/${userId}/link/`, {
        method: 'POST',
      })
      return { success: true, data: result.partner }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function unlinkPartnerUser(partnerId: number, userId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ partner: PartnerItem }>(`/admin/partners/${partnerId}/users/${userId}/unlink/`, {
        method: 'DELETE',
      })
      return { success: true, data: result.partner }
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
    createPartner,
    deletePartner,
    getPartners,
    getPartnerUsers,
    linkPartnerUser,
    unlinkPartnerUser,
    updatePartner,
  }
}
