export interface FinanceSummaryResponse {
  collections: {
    count: number
    total: number
    gross_total: number
    refund_impact_total: number
    excluded_count: number
    matched_total: number
    by_status: Array<{ status: string, count: number, total: number | string | null }>
    by_method: Array<{ method: string, count: number, total: number | string | null }>
  }
  reconciliation: {
    total: number
    unresolved_count: number
    by_status: Array<{ status: string, count: number }>
    issues_count: number
  }
  supplier_payables: {
    total: number
    ready_total: number
    pending_total: number
    paid_total: number
    by_status: Array<{ status: string, count: number, total: number | string | null }>
  }
  refunds: {
    count: number
    total: number
  }
  fees: {
    gateway_fee_total: number
  }
  margin: {
    gross_margin_total: number
    net_margin_before_overheads: number
  }
}

export interface FinancePagination {
  page: number
  page_size: number
  num_pages: number
  count: number
  has_next: boolean
  has_previous: boolean
}

export interface FinanceReconciliationItem {
  id: number
  status: string
  provider: string
  method: string
  merchant_reference: string
  provider_reference: string
  expected_amount: number
  paid_amount: number
  fee_amount: number
  settled_amount: number
  currency: string
  issues: string[]
  order_number: string
  payment_reference: string
  payment_status: string
  payer_email: string
  payer_phone: string
  last_checked_at: string | null
  reviewed_at: string | null
  review_note: string
  created_at: string
  updated_at: string
}

export interface FinanceSupplierPayableItem {
  id: number
  status: string
  source_status: string
  supplier_id: number | null
  supplier_name: string
  account_manager_id: number | null
  account_manager_email: string
  partner_id: number
  partner_name: string
  order_number: string
  order_status: string
  line_id: number
  line_status: string
  product_id: number | null
  product_title: string
  supplier_offer_id: number | null
  stockrecord_id: number | null
  quantity: number
  supplier_unit_cost: number
  payable_total: number
  gross_payable_total?: number
  adjustment_debit_total: number
  adjustment_credit_total: number
  adjustment_reversal_total: number
  net_payable_total: number
  currency: string
  payout_reference: string
  reversal_reason: string
  customer_unit_price_incl_tax: number
  gross_margin: number
  created_at: string
  updated_at: string
}

export interface FinanceRefundLedgerItem {
  id: number | null
  payment_reference: string
  order_number: string
  refund_reference: string
  refund_type: string
  status: string
  refund_scope: string
  completion_state: string
  gateway: string
  provider_reference: string
  amount: number
  currency: string
  reason: string
  requested_by_email: string
  reviewed_by_email: string
  requested_at: string
  processed_at: string | null
  erpnext_sync_status: string
  erpnext_reference: string
  erpnext_sync_message: string
  erpnext_synced_at: string | null
  notes: string
  document_references: {
    credit_note: string
    refund_payment: string
    provider: string
  }
  next_actions: string[]
  created_at: string
  updated_at: string
}

export interface FinanceReturnCaseItem {
  id: number
  return_reference: string
  payment_reference: string
  refund_reference: string
  order_number: string
  line_id: number
  line_title: string
  product_id: number | null
  product_title: string
  stockrecord_id: number | null
  quantity: number
  accepted_quantity: number
  refund_amount: number
  currency: string
  status: string
  restock_decision: string
  condition_note: string
  reason: string
  notes: string
  erpnext_rule: string
  requested_by_email: string
  reviewed_by_email: string
  received_at: string | null
  completed_at: string | null
  restocked_at: string | null
  document_references: {
    return_authorization: string
    return_receipt: string
    credit_note: string
    refund_payment: string
  }
  next_actions: string[]
  supplier_adjustment_count: number
  created_at: string
  updated_at: string
}

export interface FinanceOrderDetail {
  id: number
  number: string
  status: string
  currency: string
  date_placed: string
  customer_email: string
  shipping_method: string
  shipping_code: string
  totals: Record<string, number>
  payments: Array<{
    id: number
    reference: string
    method: string
    provider: string
    status: string
    amount: number
    currency: string
    external_reference: string
    paid_at: string | null
  }>
  reconciliations: FinanceReconciliationItem[]
  lines: Array<{
    line_id: number
    product_id: number | null
    title: string
    sku: string
    quantity: number
    open_return_quantity: number
    completed_return_quantity: number
    returnable_quantity: number
    return_locked_reason: string
    line_price_excl_tax: number
    line_price_incl_tax: number
    supplier_payable_total: number
    gross_margin_total: number
    payables: FinanceSupplierPayableItem[]
  }>
  supplier_payables: FinanceSupplierPayableItem[]
  refunds: {
    count: number
    total: number
    requests: Array<Record<string, any>>
  }
  returns: FinanceReturnCaseItem[]
}

export interface FinancePayoutBatch {
  id: number
  batch_reference: string
  supplier_id: number | null
  supplier_name: string
  partner_id: number | null
  partner_name: string
  status: string
  currency: string
  total_amount: number
  entry_count: number
  payout_method: string
  payout_reference: string
  evidence_url: string
  evidence_file_url: string
  notes: string
  created_by_email: string
  approved_by_email: string
  paid_by_email: string
  approved_at: string | null
  paid_at: string | null
  created_at: string
  updated_at: string
  entries?: Array<{
    id: number
    payable_id: number
    amount: number
    currency: string
    order_number: string
    product_title: string
    quantity: number
    supplier_name: string
    payable_status: string
    created_at: string
  }>
}

export interface FinanceListParams {
  page?: number
  pageSize?: number
  search?: string
  status?: string
  currency?: string
  dateFrom?: string
  dateTo?: string
  provider?: string
  orderNumber?: string
  reference?: string
  supplierId?: string
  accountManagerId?: string
  refundType?: string
  restockDecision?: string
  lineId?: string
}

function readApiError(err: any) {
  return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
}

export function useFinance() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { apiBase, request } = useBackendApi()

  async function getFinanceSummary() {
    loading.value = true
    error.value = null
    try {
      const result = await request<FinanceSummaryResponse>('/admin/finance/summary/', { method: 'GET' })
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

  async function getFinanceReconciliations(params: FinanceListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: FinanceReconciliationItem[], pagination: FinancePagination, summary: any }>('/admin/finance/reconciliation/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          status: params.status || '',
          currency: params.currency || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
          provider: params.provider || '',
          order_number: params.orderNumber || '',
          reference: params.reference || '',
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

  async function updateFinanceReconciliation(reconciliationId: number | string, payload: { status: string, note?: string }) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ reconciliation: FinanceReconciliationItem }>(`/admin/finance/reconciliation/${reconciliationId}/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.reconciliation }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getFinanceSupplierPayables(params: FinanceListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: FinanceSupplierPayableItem[], pagination: FinancePagination, summary: any }>('/admin/finance/supplier-payables/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          status: params.status || '',
          currency: params.currency || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
          supplier_id: params.supplierId || '',
          account_manager_id: params.accountManagerId || '',
          order_number: params.orderNumber || '',
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

  async function getFinanceRefunds(params: FinanceListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: FinanceRefundLedgerItem[], pagination: FinancePagination, summary: any }>('/admin/finance/refunds/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          status: params.status || '',
          refund_type: params.refundType || '',
          currency: params.currency || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
          order_number: params.orderNumber || '',
          reference: params.reference || '',
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

  async function updateFinanceRefund(refundId: number | string, payload: { action: string, provider_reference?: string, notes?: string }) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ refund: FinanceRefundLedgerItem }>(`/admin/finance/refunds/${refundId}/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.refund }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getFinanceReturns(params: FinanceListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: FinanceReturnCaseItem[], pagination: FinancePagination, summary: any }>('/admin/finance/returns/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 50,
          q: params.search || '',
          status: params.status || '',
          restock_decision: params.restockDecision || '',
          currency: params.currency || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
          order_number: params.orderNumber || '',
          reference: params.reference || '',
          line_id: params.lineId || '',
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

  async function createFinanceReturn(payload: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ return_case: FinanceReturnCaseItem }>('/admin/finance/returns/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.return_case }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updateFinanceReturn(returnId: number | string, payload: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ return_case: FinanceReturnCaseItem }>(`/admin/finance/returns/${returnId}/`, {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.return_case }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getFinanceOrderDetail(orderNumber: string) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ order: FinanceOrderDetail }>(`/admin/finance/orders/${encodeURIComponent(orderNumber)}/`, {
        method: 'GET',
      })
      return { success: true, data: result.order }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function getPayoutBatches(params: FinanceListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ results: FinancePayoutBatch[], pagination: FinancePagination, summary: any }>('/admin/finance/payout-batches/', {
        method: 'GET',
        query: {
          page: params.page || 1,
          page_size: params.pageSize || 25,
          q: params.search || '',
          status: params.status || '',
          currency: params.currency || '',
          supplier_id: params.supplierId || '',
          date_from: params.dateFrom || '',
          date_to: params.dateTo || '',
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

  async function createPayoutBatch(payload: { payable_ids: number[], payout_method?: string, notes?: string }) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ batch: FinancePayoutBatch }>('/admin/finance/payout-batches/', {
        method: 'POST',
        body: payload,
      })
      return { success: true, data: result.batch }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function updatePayoutBatchStatus(batchId: number | string, action: string, payload: Record<string, any> = {}) {
    loading.value = true
    error.value = null
    try {
      let body: any = payload
      if (payload.evidence_file instanceof File) {
        const formData = new FormData()
        Object.entries(payload).forEach(([key, value]) => {
          if (value !== undefined && value !== null)
            formData.append(key, value as any)
        })
        body = formData
      }
      const result = await request<{ batch: FinancePayoutBatch }>(`/admin/finance/payout-batches/${batchId}/${action}/`, {
        method: 'POST',
        body,
      })
      return { success: true, data: result.batch }
    }
    catch (err: any) {
      error.value = readApiError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  function payoutBatchCsvUrl(batchId: number | string) {
    return `${apiBase}/admin/finance/payout-batches/${batchId}/csv/`
  }

  return {
    loading,
    error,
    getFinanceSummary,
    getFinanceReconciliations,
    updateFinanceReconciliation,
    getFinanceSupplierPayables,
    getFinanceRefunds,
    updateFinanceRefund,
    getFinanceReturns,
    createFinanceReturn,
    updateFinanceReturn,
    getFinanceOrderDetail,
    getPayoutBatches,
    createPayoutBatch,
    updatePayoutBatchStatus,
    payoutBatchCsvUrl,
  }
}
