export interface AccountingPagination {
  page: number
  page_size: number
  num_pages: number
  count: number
  has_next: boolean
  has_previous: boolean
}

export interface AccountingAccount {
  id: number
  code: string
  name: string
  account_type: string
  parent_id: number | null
  parent_code: string
  is_group: boolean
  currency: string
  is_active: boolean
}

export interface AccountingJournalEntry {
  id: number
  reference: string
  entry_type: string
  status: string
  posting_date: string
  memo: string
  source_type: string
  source_object_id: string
  total_debit: number
  total_credit: number
  currency: string
  submitted_by_email: string
  submitted_at: string | null
  created_at: string
  updated_at: string
  lines?: AccountingJournalLine[]
}

export interface AccountingJournalLine {
  id: number
  account_id: number
  account_code: string
  account_name: string
  debit: number
  credit: number
  currency: string
  party_type: string
  party_id: string
  party_name: string
  against_account: string
  remarks: string
  journal_id?: number
  journal_reference?: string
  entry_type?: string
  posting_date?: string
  memo?: string
}

export interface AccountingPaymentLedgerEntry {
  id: number
  account_type: string
  account_code: string
  account_name: string
  party_type: string
  party_id: string
  party_name: string
  voucher_type: string
  voucher_no: string
  against_voucher_type: string
  against_voucher_no: string
  amount: number
  currency: string
  posting_date: string
  journal_reference: string
  created_at: string
}

export interface TrialBalanceRow {
  code: string
  name: string
  account_type: string
  debit: number
  credit: number
  balance: number
  currency: string
}

export interface AccountingBankTransaction {
  id: number
  transaction_date: string
  bank_account: string
  provider: string
  reference_number: string
  transaction_id: string
  description: string
  deposit: number
  withdrawal: number
  amount: number
  currency: string
  status: string
  source: string
  matched_payment_reference: string
  matched_order_number: string
  clearance_date: string | null
  notes: string
  reconciled_by_email: string
  reconciled_at: string | null
  created_at: string
  updated_at: string
}

export interface AccountingReconciliationAllocation {
  id: number
  bank_transaction_id: number | null
  payment_reference: string
  order_number: string
  journal_reference: string
  allocated_amount: number
  currency: string
  status: string
  note: string
  reconciled_by_email: string
  reconciled_at: string | null
  created_at: string
}

export interface AccountingPaymentCandidate {
  id: number
  reference: string
  status: string
  method: string
  provider: string
  amount: number
  currency: string
  payer_email: string
  payer_phone: string
  external_reference: string
  order_number: string
  created_at: string
  paid_at: string | null
}

export interface AccountingOrderCandidate {
  id: number
  number: string
  status: string
  total_incl_tax: number
  currency: string
  email: string
  date_placed: string | null
}

export interface AccountingCsvImportSummary {
  created: number
  skipped: number
  errors: number
}

function readApiError(err: any) {
  return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
}

export function useAccounting() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { request } = useBackendApi()

  async function apiCall<T>(path: string, options: Record<string, any> = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await request<T>(path, options)
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

  function listAccounts(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingAccount[] }>('/admin/accounting/accounts/', {
      method: 'GET',
      query: params,
    })
  }

  function listJournals(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingJournalEntry[], pagination: AccountingPagination }>('/admin/accounting/journals/', {
      method: 'GET',
      query: params,
    })
  }

  function createJournal(payload: Record<string, any>) {
    return apiCall<{ journal_entry: AccountingJournalEntry }>('/admin/accounting/journals/', {
      method: 'POST',
      body: payload,
    })
  }

  function listGeneralLedger(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingJournalLine[], pagination: AccountingPagination, summary: { debit: number, credit: number } }>('/admin/accounting/general-ledger/', {
      method: 'GET',
      query: params,
    })
  }

  function listPaymentLedger(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingPaymentLedgerEntry[], pagination: AccountingPagination }>('/admin/accounting/payment-ledger/', {
      method: 'GET',
      query: params,
    })
  }

  function getTrialBalance(params: Record<string, any> = {}) {
    return apiCall<{ results: TrialBalanceRow[], summary: { debit: number, credit: number, balance: number } }>('/admin/accounting/trial-balance/', {
      method: 'GET',
      query: params,
    })
  }

  function listBankTransactions(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingBankTransaction[], pagination: AccountingPagination, summary: { deposit: number, withdrawal: number, unreconciled: number } }>('/admin/accounting/bank-transactions/', {
      method: 'GET',
      query: params,
    })
  }

  function createBankTransaction(payload: Record<string, any>) {
    return apiCall<{ bank_transaction: AccountingBankTransaction }>('/admin/accounting/bank-transactions/', {
      method: 'POST',
      body: payload,
    })
  }

  function importBankTransactionsCsv(payload: FormData) {
    return apiCall<{ created: AccountingBankTransaction[], summary: AccountingCsvImportSummary, skipped: any[], errors: any[] }>('/admin/accounting/bank-transactions/import/', {
      method: 'POST',
      body: payload,
    })
  }

  function reconcileBankTransaction(transactionId: number | string, payload: Record<string, any>) {
    return apiCall<{ bank_transaction: AccountingBankTransaction, allocation: AccountingReconciliationAllocation }>(`/admin/accounting/bank-transactions/${transactionId}/reconcile/`, {
      method: 'POST',
      body: payload,
    })
  }

  function cancelBankTransaction(transactionId: number | string, payload: Record<string, any>) {
    return apiCall<{ bank_transaction: AccountingBankTransaction }>(`/admin/accounting/bank-transactions/${transactionId}/cancel/`, {
      method: 'POST',
      body: payload,
    })
  }

  function listReconciliationCandidates(params: Record<string, any> = {}) {
    return apiCall<{ payments: AccountingPaymentCandidate[], orders: AccountingOrderCandidate[] }>('/admin/accounting/reconciliation/candidates/', {
      method: 'GET',
      query: params,
    })
  }

  function listReconciliationAllocations(params: Record<string, any> = {}) {
    return apiCall<{ results: AccountingReconciliationAllocation[], pagination: AccountingPagination }>('/admin/accounting/reconciliation/allocations/', {
      method: 'GET',
      query: params,
    })
  }

  return {
    loading,
    error,
    cancelBankTransaction,
    createBankTransaction,
    importBankTransactionsCsv,
    listAccounts,
    listBankTransactions,
    listJournals,
    createJournal,
    listGeneralLedger,
    listPaymentLedger,
    listReconciliationAllocations,
    listReconciliationCandidates,
    reconcileBankTransaction,
    getTrialBalance,
  }
}
