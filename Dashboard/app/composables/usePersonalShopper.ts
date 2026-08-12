export interface ShopperListItemInput {
  product_id: number
  quantity: number
  note?: string
}

export interface ShopperListInput {
  customer_id: number
  title: string
  note?: string
  status: 'draft' | 'shared' | 'archived'
  expires_at?: string | null
  discount_percentage?: number
  items: ShopperListItemInput[]
}

export interface ShopperListRecord {
  id: number
  title: string
  status: string
  share_token: string
  date_updated: string
  customer: { id: number, name: string, email: string }
  items: Array<{ id: number, quantity: number, product: Record<string, unknown> }>
  discount: { percentage: string | number, code: string }
}

function apiError(err: unknown) {
  const error = err as { data?: { error?: { detail?: string }, detail?: string }, message?: string }
  return error.data?.error?.detail || error.data?.detail || error.message || 'Request failed.'
}

export function usePersonalShopper() {
  const { request } = useBackendApi()

  async function getLists(query: Record<string, string> = {}) {
    try {
      const data = await request<{ results: ShopperListRecord[] }>('/admin/personal-shopper/lists/', { query })
      return { success: true, data: data.results || [] }
    }
    catch (err: unknown) {
      return { success: false, error: apiError(err), data: [] }
    }
  }

  async function createList(payload: ShopperListInput) {
    try {
      const data = await request<{ shopper_list: ShopperListRecord }>('/admin/personal-shopper/lists/', { method: 'POST', body: payload })
      return { success: true, data: data.shopper_list }
    }
    catch (err: unknown) {
      return { success: false, error: apiError(err) }
    }
  }

  async function archiveList(id: number) {
    try {
      const data = await request<{ shopper_list: ShopperListRecord }>(`/admin/personal-shopper/lists/${id}/`, { method: 'DELETE' })
      return { success: true, data: data.shopper_list }
    }
    catch (err: unknown) {
      return { success: false, error: apiError(err) }
    }
  }

  async function duplicateList(id: number, payload: { customer_id: number, title?: string, status: 'draft' | 'shared' }) {
    try {
      const data = await request<{ shopper_list: ShopperListRecord }>(`/admin/personal-shopper/lists/${id}/duplicate/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: data.shopper_list }
    }
    catch (err: unknown) {
      return { success: false, error: apiError(err) }
    }
  }

  return { getLists, createList, archiveList, duplicateList }
}
