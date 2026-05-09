import type { OfferItem } from '~/composables/useOffers'

export interface VoucherItem {
  id: number
  name: string
  code: string
  usage: string
  start_datetime: string | null
  end_datetime: string | null
  num_basket_additions: number
  num_orders: number
  total_discount: string | number
  date_created: string | null
  offers: OfferItem[]
}

export interface VoucherPayload {
  name: string
  code: string
  usage: string
  start_datetime: string
  end_datetime: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail
    || err?.data?.detail
    || err?.message
    || 'Unknown error'
}

export function useVouchers() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function getVouchers(params: { page?: number, pageSize?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: VoucherItem[], pagination: any }>('/admin/vouchers/', {
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

  async function createVoucher(payload: VoucherPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ voucher: VoucherItem }>('/admin/vouchers/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.voucher }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function updateVoucher(id: number, payload: Partial<VoucherPayload>) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ voucher: VoucherItem }>(`/admin/vouchers/${id}/`, {
        method: 'PATCH',
        body: payload,
      })
      return { success: true, data: result.voucher }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value, errors: err?.data?.error?.errors || null }
    }
    finally {
      loading.value = false
    }
  }

  async function deleteVoucher(id: number) {
    loading.value = true
    error.value = null

    try {
      await request(`/admin/vouchers/${id}/`, { method: 'DELETE' })
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

  async function getVoucherStats(id: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ stats: VoucherItem }>(`/admin/vouchers/${id}/stats/`, { method: 'GET' })
      return { success: true, data: result.stats }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getVoucherOffers(id: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ results: OfferItem[] }>(`/admin/vouchers/${id}/offers/`, { method: 'GET' })
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

  async function attachVoucherOffer(id: number, offerId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ voucher: VoucherItem }>(`/admin/vouchers/${id}/offers/`, {
        method: 'POST',
        body: { offer_id: offerId },
      })
      return { success: true, data: result.voucher }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function detachVoucherOffer(id: number, offerId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await request<{ voucher: VoucherItem }>(`/admin/vouchers/${id}/offers/`, {
        method: 'DELETE',
        body: { offer_id: offerId },
      })
      return { success: true, data: result.voucher }
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
    attachVoucherOffer,
    createVoucher,
    deleteVoucher,
    detachVoucherOffer,
    getVoucherOffers,
    getVoucherStats,
    getVouchers,
    updateVoucher,
  }
}
