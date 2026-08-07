<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { FinanceOrderDetail, FinancePayoutBatch, FinanceReconciliationItem, FinanceRefundLedgerItem, FinanceReturnCaseItem, FinanceSupplierPayableItem } from '~/composables/useFinance'
import type { SupplierItem } from '~/composables/useSuppliers'
import type { UserTableRow } from '~/types/UserTableRow'

const toast = useToast()
const route = useRoute()
const {
  createFinanceReturn,
  createPayoutBatch,
  getFinanceOrderDetail,
  getFinanceReconciliations,
  getFinanceRefunds,
  getFinanceReturns,
  getFinanceSummary,
  getFinanceSupplierPayables,
  getPayoutBatches,
  payoutBatchCsvUrl,
  updateFinanceReturn,
  updateFinanceRefund,
  updateFinanceReconciliation,
  updatePayoutBatchStatus,
} = useFinance()
const { getSuppliers } = useSuppliers()
const { getUsers } = useUser()

const ALL_STATUSES = '__all_statuses__'
const ALL_PROVIDERS = '__all_providers__'
const FINANCE_VIEW_META: Record<string, { title: string, description: string }> = {
  overview: {
    title: 'Finance Overview',
    description: 'Monitor collections, payment status, fees, supplier totals, refunds, and margin.',
  },
  reconciliation: {
    title: 'Payment Reconciliation',
    description: 'Match gateway collections against orders, investigate variances, and clear finance rows.',
  },
  'supplier-payables': {
    title: 'Supplier Payables',
    description: 'Track what each supplier is owed, payout readiness, margins, and account manager ownership.',
  },
  'payout-batches': {
    title: 'Supplier Payout Batches',
    description: 'Create, approve, export, and mark supplier payout batches as paid.',
  },
  refunds: {
    title: 'Refund And Reversal Ledger',
    description: 'Review full and partial refunds, gateway references, completion states, and finance sync.',
  },
  returns: {
    title: 'Return Intake And Restock',
    description: 'Create return cases, accept quantities, decide restock handling, and trigger refund workflow.',
  },
  order: {
    title: 'Order Finance Lookup',
    description: 'Inspect payments, payables, reconciliation rows, returns, refunds, fees, and margin for one order.',
  },
}

const activeView = computed(() => {
  const view = typeof route.query.view === 'string' ? route.query.view : 'overview'
  return FINANCE_VIEW_META[view] ? view : 'overview'
})
const activeViewMeta = computed(() => FINANCE_VIEW_META[activeView.value])
const isOverviewView = computed(() => activeView.value === 'overview')
const isView = (...views: string[]) => views.includes(activeView.value)

const isLoading = ref(false)
const isOrderFinanceLoading = ref(false)
const isPayoutLoading = ref(false)
const isReconLoading = ref(false)
const isPayablesLoading = ref(false)
const isRefundsLoading = ref(false)
const isReturnsLoading = ref(false)
const summary = ref<any | null>(null)
const reconciliations = ref<FinanceReconciliationItem[]>([])
const payables = ref<FinanceSupplierPayableItem[]>([])
const refunds = ref<FinanceRefundLedgerItem[]>([])
const returns = ref<FinanceReturnCaseItem[]>([])
const payoutBatches = ref<FinancePayoutBatch[]>([])
const orderFinance = ref<FinanceOrderDetail | null>(null)
const orderFinanceNumber = ref('')
const selectedPayableIds = ref<number[]>([])
const reconciliationSummary = ref<any>({})
const payableSummary = ref<any>({})
const refundSummary = ref<any>({})
const returnSummary = ref<any>({})
const reconciliationPage = ref(1)
const payablePage = ref(1)
const refundPage = ref(1)
const returnPage = ref(1)
const payoutPage = ref(1)
const pageSize = ref(25)
const reconciliationPagination = ref<any>({})
const payablePagination = ref<any>({})
const refundPagination = ref<any>({})
const returnPagination = ref<any>({})
const payoutPagination = ref<any>({})
const payoutSummary = ref<any>({})
const payoutEvidenceFile = ref<File | null>(null)
const supplierSearch = ref('')
const supplierOptions = ref<SupplierItem[]>([])
const supplierPickerOpen = ref(false)
const isSupplierPickerLoading = ref(false)
const accountManagerSearch = ref('')
const accountManagerOptions = ref<UserTableRow[]>([])
const accountManagerPickerOpen = ref(false)
const isAccountManagerPickerLoading = ref(false)
let supplierSearchTimer: ReturnType<typeof setTimeout> | null = null
let accountManagerSearchTimer: ReturnType<typeof setTimeout> | null = null

const reconciliationFilters = reactive({
  search: '',
  status: ALL_STATUSES,
  provider: ALL_PROVIDERS,
  currency: '',
  orderNumber: '',
  reference: '',
  dateFrom: '',
  dateTo: '',
})

const payableFilters = reactive({
  search: '',
  status: ALL_STATUSES,
  currency: '',
  supplierId: '',
  accountManagerId: '',
  orderNumber: '',
  dateFrom: '',
  dateTo: '',
})

const refundFilters = reactive({
  search: '',
  status: ALL_STATUSES,
  refundType: ALL_STATUSES,
  currency: '',
  orderNumber: '',
  reference: '',
  dateFrom: '',
  dateTo: '',
})

const returnFilters = reactive({
  search: '',
  status: ALL_STATUSES,
  restockDecision: ALL_STATUSES,
  currency: '',
  orderNumber: '',
  reference: '',
  lineId: '',
  dateFrom: '',
  dateTo: '',
})

const payoutFilters = reactive({
  search: '',
  status: ALL_STATUSES,
  currency: '',
  supplierId: '',
  dateFrom: '',
  dateTo: '',
})

const reconciliationActionForm = reactive({
  reconciliationId: '',
  status: 'manual_review',
  note: '',
})

const returnCreateForm = reactive({
  paymentReference: '',
  lineId: '',
  quantity: '1',
  refundAmount: '',
  reason: '',
  restockDecision: 'pending',
  conditionNote: '',
})
const returnLookupOrderNumber = ref('')
const returnLookup = ref<FinanceOrderDetail | null>(null)
const isReturnLookupLoading = ref(false)

const returnActionForm = reactive({
  returnId: '',
  action: 'approve',
  acceptedQuantity: '',
  restockDecision: 'restock',
  notes: '',
})

const refundActionForm = reactive({
  refundId: '',
  action: 'submit',
  providerReference: '',
  notes: '',
})

const payoutForm = reactive({
  payableIds: '',
  payoutMethod: '',
  notes: '',
  paidReference: '',
  evidenceUrl: '',
})

const moneyFormatter = computed(() => new Intl.NumberFormat('en-KE', {
  style: 'currency',
  currency: 'KES',
  maximumFractionDigits: 2,
}))

const collectionCards = computed(() => [
  {
    label: 'Customer collections',
    value: money(summary.value?.collections?.total),
    meta: `${summary.value?.collections?.count || 0} collectible payment(s), ${summary.value?.collections?.excluded_count || 0} excluded`,
    icon: 'i-lucide-banknote',
    tone: 'text-emerald-600',
  },
  {
    label: 'Matched payments',
    value: money(summary.value?.collections?.matched_total),
    meta: `${summary.value?.reconciliation?.total || 0} reconciliation row(s)`,
    icon: 'i-lucide-badge-check',
    tone: 'text-blue-600',
  },
  {
    label: 'Supplier payables',
    value: money(summary.value?.supplier_payables?.total),
    meta: `${money(summary.value?.supplier_payables?.ready_total)} ready`,
    icon: 'i-lucide-store',
    tone: 'text-indigo-600',
  },
  {
    label: 'Supplier paid out',
    value: money(summary.value?.supplier_payables?.paid_total),
    meta: `${money(summary.value?.supplier_payables?.pending_total)} pending`,
    icon: 'i-lucide-wallet-cards',
    tone: 'text-violet-600',
  },
  {
    label: 'Refunds',
    value: money(summary.value?.refunds?.total),
    meta: `${summary.value?.refunds?.count || 0} submitted/succeeded`,
    icon: 'i-lucide-undo-2',
    tone: 'text-amber-600',
  },
  {
    label: 'Net margin',
    value: money(summary.value?.margin?.net_margin_before_overheads),
    meta: `${money(summary.value?.fees?.gateway_fee_total)} gateway fees`,
    icon: 'i-lucide-chart-no-axes-combined',
    tone: 'text-slate-700',
  },
])

const selectedReturnLine = computed(() => {
  const lineId = Number(returnCreateForm.lineId)
  if (!Number.isInteger(lineId) || !returnLookup.value)
    return null
  return returnLookup.value.lines.find(line => Number(line.line_id) === lineId) || null
})

const returnPaymentOptions = computed(() => {
  const payments = returnLookup.value?.payments || []
  return payments.map(payment => ({
    label: `${formatLabel(payment.method)} - ${payment.reference} - ${money(payment.amount)}`,
    value: payment.reference,
  }))
})

const canCreateReturn = computed(() => Boolean(
  returnCreateForm.paymentReference.trim()
  && Number(returnCreateForm.lineId)
  && Number(returnCreateForm.quantity)
  && selectedReturnLine.value
  && Number(returnCreateForm.quantity) <= Number(selectedReturnLine.value.returnable_quantity ?? selectedReturnLine.value.quantity ?? 0),
))

const paymentStatusColumns: TableColumn<any>[] = [
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => formatLabel(row.original.status) },
  { accessorKey: 'count', header: 'Payments' },
  { accessorKey: 'total', header: 'Total', cell: ({ row }) => money(row.original.total) },
]

const paymentMethodColumns: TableColumn<any>[] = [
  { accessorKey: 'method', header: 'Method', cell: ({ row }) => formatLabel(row.original.method) },
  { accessorKey: 'count', header: 'Payments' },
  { accessorKey: 'total', header: 'Total', cell: ({ row }) => money(row.original.total) },
]

const reconciliationColumns: TableColumn<FinanceReconciliationItem>[] = [
  { accessorKey: 'id', header: 'ID' },
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => formatLabel(row.original.status) },
  { accessorKey: 'order_number', header: 'Order', cell: ({ row }) => row.original.order_number || 'Unlinked' },
  { accessorKey: 'payment_reference', header: 'Payment Ref' },
  { accessorKey: 'provider_reference', header: 'Provider Ref' },
  { accessorKey: 'provider', header: 'Provider', cell: ({ row }) => formatLabel(row.original.provider) },
  { accessorKey: 'paid_amount', header: 'Paid', cell: ({ row }) => money(row.original.paid_amount) },
  { accessorKey: 'expected_amount', header: 'Expected', cell: ({ row }) => money(row.original.expected_amount) },
  { accessorKey: 'fee_amount', header: 'Fee', cell: ({ row }) => money(row.original.fee_amount) },
  { accessorKey: 'issues', header: 'Issues', cell: ({ row }) => row.original.issues?.length ? row.original.issues.join(', ') : 'None' },
  { accessorKey: 'updated_at', header: 'Updated', cell: ({ row }) => formatDate(row.original.updated_at) },
]

const supplierPayableColumns: TableColumn<FinanceSupplierPayableItem>[] = [
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => formatLabel(row.original.status) },
  { accessorKey: 'supplier_name', header: 'Supplier' },
  { accessorKey: 'account_manager_email', header: 'Account Manager', cell: ({ row }) => row.original.account_manager_email || 'Unassigned' },
  { accessorKey: 'order_number', header: 'Order' },
  { accessorKey: 'product_title', header: 'Product' },
  { accessorKey: 'quantity', header: 'Qty' },
  { accessorKey: 'net_payable_total', header: 'Net Payable', cell: ({ row }) => money(row.original.net_payable_total ?? row.original.payable_total) },
  { accessorKey: 'gross_margin', header: 'Margin', cell: ({ row }) => money(row.original.gross_margin) },
  { accessorKey: 'updated_at', header: 'Updated', cell: ({ row }) => formatDate(row.original.updated_at) },
]

const refundColumns: TableColumn<FinanceRefundLedgerItem>[] = [
  { accessorKey: 'id', header: 'ID' },
  { accessorKey: 'completion_state', header: 'Completion', cell: ({ row }) => formatLabel(row.original.completion_state || row.original.status) },
  { accessorKey: 'refund_scope', header: 'Scope', cell: ({ row }) => formatLabel(row.original.refund_scope) },
  { accessorKey: 'refund_type', header: 'Type', cell: ({ row }) => formatLabel(row.original.refund_type) },
  { accessorKey: 'order_number', header: 'Order', cell: ({ row }) => row.original.order_number || 'Unlinked' },
  { accessorKey: 'refund_reference', header: 'Refund Ref' },
  { accessorKey: 'payment_reference', header: 'Payment Ref' },
  { accessorKey: 'gateway', header: 'Gateway', cell: ({ row }) => formatLabel(row.original.gateway) },
  { accessorKey: 'amount', header: 'Amount', cell: ({ row }) => money(row.original.amount) },
  { accessorKey: 'erpnext_sync_status', header: 'Sync', cell: ({ row }) => formatLabel(row.original.erpnext_sync_status || 'pending') },
  { accessorKey: 'next_actions', header: 'Next', cell: ({ row }) => row.original.next_actions?.length ? row.original.next_actions.map(formatLabel).join(', ') : 'Done' },
  { accessorKey: 'reason', header: 'Reason', cell: ({ row }) => row.original.reason || 'No reason recorded' },
  { accessorKey: 'created_at', header: 'Created', cell: ({ row }) => formatDate(row.original.created_at) },
]

const returnColumns: TableColumn<FinanceReturnCaseItem>[] = [
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => formatLabel(row.original.status) },
  { accessorKey: 'return_reference', header: 'Return Ref' },
  { accessorKey: 'order_number', header: 'Order' },
  { accessorKey: 'line_title', header: 'Line' },
  { accessorKey: 'quantity', header: 'Requested' },
  { accessorKey: 'accepted_quantity', header: 'Accepted' },
  { accessorKey: 'refund_amount', header: 'Refund', cell: ({ row }) => money(row.original.refund_amount) },
  { accessorKey: 'restock_decision', header: 'Restock', cell: ({ row }) => formatLabel(row.original.restock_decision) },
  { accessorKey: 'refund_reference', header: 'Refund Ref', cell: ({ row }) => row.original.refund_reference || 'Not created' },
  { accessorKey: 'erpnext_rule', header: 'Return Rule', cell: ({ row }) => formatLabel(row.original.erpnext_rule) },
  { accessorKey: 'updated_at', header: 'Updated', cell: ({ row }) => formatDate(row.original.updated_at) },
]

const reconciliationStatusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Pending', value: 'pending' },
  { label: 'Matched', value: 'matched' },
  { label: 'Amount mismatch', value: 'amount_mismatch' },
  { label: 'Duplicate', value: 'duplicate' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Reversed', value: 'reversed' },
  { label: 'Refunded', value: 'refunded' },
  { label: 'Manual review', value: 'manual_review' },
]

const providerOptions = [
  { label: 'All providers', value: ALL_PROVIDERS },
  { label: 'M-Pesa', value: 'mpesa' },
  { label: 'Pesapal', value: 'pesapal' },
  { label: 'Airtel Money', value: 'airtel_money' },
  { label: 'Card', value: 'card' },
  { label: 'Offline', value: 'offline' },
]

const payableStatusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Ready unpaid', value: 'ready' },
  { label: 'Pending', value: 'pending' },
  { label: 'Payable', value: 'payable' },
  { label: 'On hold', value: 'on_hold' },
  { label: 'Approved', value: 'approved' },
  { label: 'Paid', value: 'paid' },
  { label: 'Disputed', value: 'disputed' },
  { label: 'Reversed', value: 'reversed' },
]

const refundStatusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Requested', value: 'requested' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Succeeded', value: 'succeeded' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
]

const refundActionOptions = [
  { label: 'Submit refund', value: 'submit' },
  { label: 'Mark succeeded', value: 'succeed' },
  { label: 'Mark failed', value: 'fail' },
  { label: 'Cancel request', value: 'cancel' },
]

const refundTypeOptions = [
  { label: 'All types', value: ALL_STATUSES },
  { label: 'Refund', value: 'refund' },
  { label: 'Cancellation', value: 'cancellation' },
  { label: 'Return', value: 'return' },
  { label: 'Adjustment', value: 'adjustment' },
]

const returnStatusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Requested', value: 'requested' },
  { label: 'Approved', value: 'approved' },
  { label: 'Received', value: 'received' },
  { label: 'Accepted', value: 'accepted' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Refunded', value: 'refunded' },
  { label: 'Cancelled', value: 'cancelled' },
]

const returnActionOptions = [
  { label: 'Approve', value: 'approve' },
  { label: 'Receive', value: 'receive' },
  { label: 'Accept', value: 'accept' },
  { label: 'Mark refunded', value: 'refund' },
  { label: 'Reject', value: 'reject' },
  { label: 'Cancel', value: 'cancel' },
]

const restockDecisionOptions = [
  { label: 'Pending', value: 'pending' },
  { label: 'Restock', value: 'restock' },
  { label: 'Quarantine', value: 'quarantine' },
  { label: 'Scrap', value: 'scrap' },
  { label: 'Rejected', value: 'rejected' },
]

const restockFilterOptions = [
  { label: 'All decisions', value: ALL_STATUSES },
  ...restockDecisionOptions,
]

const payoutStatusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Draft', value: 'draft' },
  { label: 'Pending approval', value: 'pending_approval' },
  { label: 'Approved', value: 'approved' },
  { label: 'Paid', value: 'paid' },
  { label: 'Cancelled', value: 'cancelled' },
]

const pageSizeOptions = [
  { label: '25 rows', value: 25 },
  { label: '50 rows', value: 50 },
  { label: '100 rows', value: 100 },
]

function money(value: unknown) {
  return moneyFormatter.value.format(Number(value || 0))
}

function formatLabel(value?: string | null) {
  return value ? value.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en-KE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatSupplierOption(supplier: SupplierItem) {
  const company = supplier.company_name || supplier.partner?.name || 'Unnamed supplier'
  const contact = supplier.contact_name || supplier.user?.email || ''
  return contact ? `${company} - ${contact}` : company
}

function formatAccountManagerOption(manager: UserTableRow | { email?: string, name?: string }) {
  const email = manager.email || ''
  const name = manager.name && manager.name !== email ? manager.name : ''
  return name ? `${name} (${email})` : email || 'Unassigned'
}

function syncSupplierPickerFromPayables() {
  if (supplierSearch.value || !payableFilters.supplierId)
    return
  const row = payables.value.find(payable => String(payable.supplier_id || '') === String(payableFilters.supplierId))
  if (row)
    supplierSearch.value = row.supplier_name || row.partner_name || ''
}

function syncAccountManagerPickerFromPayables() {
  if (accountManagerSearch.value || !payableFilters.accountManagerId)
    return
  const row = payables.value.find(payable => String(payable.account_manager_id || '') === String(payableFilters.accountManagerId))
  if (row)
    accountManagerSearch.value = row.account_manager_email || ''
}

function reconciliationStatusColor() {
  const unresolved = Number(summary.value?.reconciliation?.unresolved_count || 0)
  const issues = Number(summary.value?.reconciliation?.issues_count || 0)
  if (unresolved || issues)
    return 'warning'
  return 'success'
}

function readStatusFilter(value: string) {
  return value === ALL_STATUSES ? '' : value
}

function readProviderFilter(value: string) {
  return value === ALL_PROVIDERS ? '' : value
}

async function loadSummary() {
  const result = await getFinanceSummary()
  if (result.success)
    summary.value = result.data
  else
    toast.add({
      title: 'Could not load finance summary',
      description: result.error || 'Please try again.',
      color: 'error',
    })
}

async function loadSupplierOptions(search = '') {
  isSupplierPickerLoading.value = true
  const result = await getSuppliers({ search })
  supplierOptions.value = result.success ? result.data?.results ?? [] : []
  isSupplierPickerLoading.value = false
}

async function openSupplierPicker() {
  supplierPickerOpen.value = true
  await loadSupplierOptions(supplierSearch.value.trim())
}

function queueSupplierSearch() {
  payableFilters.supplierId = ''
  supplierPickerOpen.value = true
  if (supplierSearchTimer)
    clearTimeout(supplierSearchTimer)
  supplierSearchTimer = setTimeout(() => {
    loadSupplierOptions(supplierSearch.value.trim())
  }, 250)
}

function selectSupplierFilter(supplier: SupplierItem) {
  payableFilters.supplierId = String(supplier.id)
  supplierSearch.value = formatSupplierOption(supplier)
  supplierPickerOpen.value = false
  if (supplier.account_manager?.id) {
    payableFilters.accountManagerId = String(supplier.account_manager.id)
    accountManagerSearch.value = formatAccountManagerOption(supplier.account_manager)
  }
  else {
    payableFilters.accountManagerId = ''
    accountManagerSearch.value = ''
  }
  applyPayableFilters()
}

function clearSupplierFilter() {
  payableFilters.supplierId = ''
  supplierSearch.value = ''
  supplierPickerOpen.value = false
}

async function loadAccountManagerOptions(search = '') {
  isAccountManagerPickerLoading.value = true
  const result = await getUsers({
    role: 'staff',
    status: 'active',
    search,
    pageSize: 20,
    sortBy: 'name',
  })
  accountManagerOptions.value = result.success ? result.data?.results ?? [] : []
  isAccountManagerPickerLoading.value = false
}

async function openAccountManagerPicker() {
  accountManagerPickerOpen.value = true
  await loadAccountManagerOptions(accountManagerSearch.value.trim())
}

function queueAccountManagerSearch() {
  payableFilters.accountManagerId = ''
  accountManagerPickerOpen.value = true
  if (accountManagerSearchTimer)
    clearTimeout(accountManagerSearchTimer)
  accountManagerSearchTimer = setTimeout(() => {
    loadAccountManagerOptions(accountManagerSearch.value.trim())
  }, 250)
}

function selectAccountManagerFilter(manager: UserTableRow) {
  payableFilters.accountManagerId = String(manager.id)
  accountManagerSearch.value = formatAccountManagerOption(manager)
  accountManagerPickerOpen.value = false
  applyPayableFilters()
}

function clearAccountManagerFilter() {
  payableFilters.accountManagerId = ''
  accountManagerSearch.value = ''
  accountManagerPickerOpen.value = false
}

async function loadReconciliations() {
  isReconLoading.value = true
  const result = await getFinanceReconciliations({
    page: reconciliationPage.value,
    pageSize: pageSize.value,
    search: reconciliationFilters.search.trim(),
    status: readStatusFilter(reconciliationFilters.status),
    provider: readProviderFilter(reconciliationFilters.provider),
    currency: reconciliationFilters.currency.trim().toUpperCase(),
    orderNumber: reconciliationFilters.orderNumber.trim(),
    reference: reconciliationFilters.reference.trim(),
    dateFrom: reconciliationFilters.dateFrom,
    dateTo: reconciliationFilters.dateTo,
  })

  if (result.success) {
    reconciliations.value = result.data?.results ?? []
    reconciliationSummary.value = result.data?.summary ?? {}
    reconciliationPagination.value = result.data?.pagination ?? {}
  }
  else {
    reconciliations.value = []
    toast.add({ title: 'Could not load reconciliation rows', description: result.error || 'Please try again.', color: 'error' })
  }
  isReconLoading.value = false
}

async function loadPayables() {
  isPayablesLoading.value = true
  const result = await getFinanceSupplierPayables({
    page: payablePage.value,
    pageSize: pageSize.value,
    search: payableFilters.search.trim(),
    status: readStatusFilter(payableFilters.status),
    currency: payableFilters.currency.trim().toUpperCase(),
    supplierId: payableFilters.supplierId.trim(),
    accountManagerId: payableFilters.accountManagerId.trim(),
    orderNumber: payableFilters.orderNumber.trim(),
    dateFrom: payableFilters.dateFrom,
    dateTo: payableFilters.dateTo,
  })

  if (result.success) {
    payables.value = result.data?.results ?? []
    payableSummary.value = result.data?.summary ?? {}
    payablePagination.value = result.data?.pagination ?? {}
    syncSupplierPickerFromPayables()
    syncAccountManagerPickerFromPayables()
  }
  else {
    payables.value = []
    toast.add({ title: 'Could not load supplier payable rows', description: result.error || 'Please try again.', color: 'error' })
  }
  isPayablesLoading.value = false
}

async function loadRefunds() {
  isRefundsLoading.value = true
  const result = await getFinanceRefunds({
    page: refundPage.value,
    pageSize: pageSize.value,
    search: refundFilters.search.trim(),
    status: readStatusFilter(refundFilters.status),
    refundType: readStatusFilter(refundFilters.refundType),
    currency: refundFilters.currency.trim().toUpperCase(),
    orderNumber: refundFilters.orderNumber.trim(),
    reference: refundFilters.reference.trim(),
    dateFrom: refundFilters.dateFrom,
    dateTo: refundFilters.dateTo,
  })

  if (result.success) {
    refunds.value = result.data?.results ?? []
    refundSummary.value = result.data?.summary ?? {}
    refundPagination.value = result.data?.pagination ?? {}
  }
  else {
    refunds.value = []
    toast.add({ title: 'Could not load refund ledger', description: result.error || 'Please try again.', color: 'error' })
  }
  isRefundsLoading.value = false
}

async function loadReturns() {
  isReturnsLoading.value = true
  const result = await getFinanceReturns({
    page: returnPage.value,
    pageSize: pageSize.value,
    search: returnFilters.search.trim(),
    status: readStatusFilter(returnFilters.status),
    restockDecision: readStatusFilter(returnFilters.restockDecision),
    currency: returnFilters.currency.trim().toUpperCase(),
    orderNumber: returnFilters.orderNumber.trim(),
    reference: returnFilters.reference.trim(),
    lineId: returnFilters.lineId.trim(),
    dateFrom: returnFilters.dateFrom,
    dateTo: returnFilters.dateTo,
  })

  if (result.success) {
    returns.value = result.data?.results ?? []
    returnSummary.value = result.data?.summary ?? {}
    returnPagination.value = result.data?.pagination ?? {}
  }
  else {
    returns.value = []
    toast.add({ title: 'Could not load return cases', description: result.error || 'Please try again.', color: 'error' })
  }
  isReturnsLoading.value = false
}

async function loadPayoutBatches() {
  isPayoutLoading.value = true
  const result = await getPayoutBatches({
    page: payoutPage.value,
    pageSize: pageSize.value,
    search: payoutFilters.search.trim(),
    status: readStatusFilter(payoutFilters.status),
    currency: payoutFilters.currency.trim().toUpperCase(),
    supplierId: payoutFilters.supplierId.trim(),
    dateFrom: payoutFilters.dateFrom,
    dateTo: payoutFilters.dateTo,
  })

  if (result.success) {
    payoutBatches.value = result.data?.results ?? []
    payoutSummary.value = result.data?.summary ?? {}
    payoutPagination.value = result.data?.pagination ?? {}
  }
  else {
    payoutBatches.value = []
    toast.add({ title: 'Could not load payout batches', description: result.error || 'Please try again.', color: 'error' })
  }
  isPayoutLoading.value = false
}

async function loadFinance() {
  isLoading.value = true
  await Promise.all([loadSummary(), loadReconciliations(), loadPayables(), loadRefunds(), loadReturns(), loadPayoutBatches()])
  isLoading.value = false
}

async function loadOrderFinance() {
  const orderNumber = orderFinanceNumber.value.trim()
  if (!orderNumber) {
    toast.add({ title: 'Enter an order number', description: 'Use the order number from reconciliation or supplier payables.', color: 'warning' })
    return
  }
  isOrderFinanceLoading.value = true
  const result = await getFinanceOrderDetail(orderNumber)
  if (result.success && result.data)
    orderFinance.value = result.data
  else {
    orderFinance.value = null
    toast.add({ title: 'Could not load order finance', description: result.error || 'Please confirm the order number.', color: 'error' })
  }
  isOrderFinanceLoading.value = false
}

async function loadReturnOrder() {
  const orderNumber = returnLookupOrderNumber.value.trim()
  if (!orderNumber) {
    toast.add({ title: 'Enter an order number', description: 'Use the order number from Orders, Payment Logs, or the customer request.', color: 'warning' })
    return
  }
  isReturnLookupLoading.value = true
  const result = await getFinanceOrderDetail(orderNumber)
  if (result.success && result.data) {
    returnLookup.value = result.data
    returnFilters.orderNumber = result.data.number
    const firstPayment = result.data.payments.find(payment => ['authorized', 'paid', 'succeeded', 'confirmed'].includes((payment.status || '').toLowerCase())) || result.data.payments[0]
    if (firstPayment)
      returnCreateForm.paymentReference = firstPayment.reference
    if (result.data.lines.length === 1)
      useReturnLine(result.data.lines[0])
    toast.add({ title: 'Order loaded', description: `Choose the item being returned from order #${result.data.number}.`, color: 'success' })
  }
  else {
    returnLookup.value = null
    toast.add({ title: 'Could not load order', description: result.error || 'Please confirm the order number.', color: 'error' })
  }
  isReturnLookupLoading.value = false
}

async function refreshReturnLookup() {
  const orderNumber = returnLookup.value?.number || returnLookupOrderNumber.value.trim()
  if (!orderNumber)
    return
  const result = await getFinanceOrderDetail(orderNumber)
  if (result.success && result.data)
    returnLookup.value = result.data
}

function useReturnLine(line: FinanceOrderDetail['lines'][number]) {
  const returnableQuantity = Number(line.returnable_quantity ?? line.quantity ?? 0)
  if (returnableQuantity <= 0) {
    toast.add({ title: 'Line already returned', description: line.return_locked_reason || 'This item has no remaining quantity available for return.', color: 'warning' })
    return
  }
  returnCreateForm.lineId = String(line.line_id)
  returnCreateForm.quantity = '1'
  const unitAmount = Number(line.line_price_incl_tax || 0) / Math.max(Number(line.quantity || 1), 1)
  returnCreateForm.refundAmount = unitAmount > 0 ? unitAmount.toFixed(2) : ''
  returnCreateForm.reason ||= 'Customer return request'
}

function autofillReturnAmount() {
  const line = selectedReturnLine.value
  if (!line)
    return
  const returnableQuantity = Number(line.returnable_quantity ?? line.quantity ?? 1)
  const quantity = Math.min(Math.max(Number(returnCreateForm.quantity || 1), 1), Math.max(returnableQuantity, 1))
  const unitAmount = Number(line.line_price_incl_tax || 0) / Math.max(Number(line.quantity || 1), 1)
  returnCreateForm.refundAmount = (unitAmount * quantity).toFixed(2)
}

function applyReconciliationFilters() {
  reconciliationPage.value = 1
  loadReconciliations()
}

function resetReconciliationFilters() {
  reconciliationFilters.search = ''
  reconciliationFilters.status = ALL_STATUSES
  reconciliationFilters.provider = ALL_PROVIDERS
  reconciliationFilters.currency = ''
  reconciliationFilters.orderNumber = ''
  reconciliationFilters.reference = ''
  reconciliationFilters.dateFrom = ''
  reconciliationFilters.dateTo = ''
  applyReconciliationFilters()
}

async function updateReconciliationFromForm() {
  const reconciliationId = Number(reconciliationActionForm.reconciliationId)
  if (!Number.isInteger(reconciliationId) || reconciliationId <= 0) {
    toast.add({ title: 'Reconciliation ID needed', description: 'Enter the reconciliation row ID from the table.', color: 'warning' })
    return
  }
  isReconLoading.value = true
  const result = await updateFinanceReconciliation(reconciliationId, {
    status: reconciliationActionForm.status,
    note: reconciliationActionForm.note.trim(),
  })
  if (result.success) {
    toast.add({ title: 'Reconciliation updated', description: `Row ${reconciliationId} is now ${formatLabel(result.data?.status)}.`, color: 'success' })
    reconciliationActionForm.reconciliationId = ''
    reconciliationActionForm.note = ''
    await Promise.all([loadReconciliations(), loadPayables(), loadSummary()])
  }
  else {
    toast.add({ title: 'Could not update reconciliation', description: result.error || 'Please review the row status.', color: 'error' })
  }
  isReconLoading.value = false
}

async function reviewReconciliation(row: FinanceReconciliationItem, status = 'matched') {
  reconciliationActionForm.reconciliationId = String(row.id)
  reconciliationActionForm.status = status
  reconciliationActionForm.note = row.issues?.length ? `Reviewed: ${row.issues.join(', ')}` : 'Reviewed from finance table.'
  await updateReconciliationFromForm()
}

function canQuickMatchReconciliation(row: FinanceReconciliationItem) {
  return Boolean(row.order_number) && !row.issues?.length && row.status !== 'matched'
}

function applyPayableFilters() {
  payablePage.value = 1
  loadPayables()
}

function resetPayableFilters() {
  payableFilters.search = ''
  payableFilters.status = ALL_STATUSES
  payableFilters.currency = ''
  payableFilters.supplierId = ''
  payableFilters.accountManagerId = ''
  payableFilters.orderNumber = ''
  payableFilters.dateFrom = ''
  payableFilters.dateTo = ''
  supplierSearch.value = ''
  accountManagerSearch.value = ''
  supplierPickerOpen.value = false
  accountManagerPickerOpen.value = false
  applyPayableFilters()
}

function fetchReadyUnpaidPayables() {
  payableFilters.status = 'ready'
  payableFilters.orderNumber = ''
  payablePage.value = 1
  selectedPayableIds.value = []
  loadPayables()
}

function togglePayableSelection(payableId: number, checked: boolean) {
  const selected = new Set(selectedPayableIds.value)
  if (checked)
    selected.add(payableId)
  else
    selected.delete(payableId)
  selectedPayableIds.value = [...selected]
}

function isPayableSelected(payableId: number) {
  return selectedPayableIds.value.includes(payableId)
}

function selectablePayable(payable: FinanceSupplierPayableItem) {
  return ['payable', 'approved'].includes(payable.status)
}

function applyRefundFilters() {
  refundPage.value = 1
  loadRefunds()
}

function resetRefundFilters() {
  refundFilters.search = ''
  refundFilters.status = ALL_STATUSES
  refundFilters.refundType = ALL_STATUSES
  refundFilters.currency = ''
  refundFilters.orderNumber = ''
  refundFilters.reference = ''
  refundFilters.dateFrom = ''
  refundFilters.dateTo = ''
  applyRefundFilters()
}

function applyReturnFilters() {
  returnPage.value = 1
  loadReturns()
}

function resetReturnFilters() {
  returnFilters.search = ''
  returnFilters.status = ALL_STATUSES
  returnFilters.restockDecision = ALL_STATUSES
  returnFilters.currency = ''
  returnFilters.orderNumber = ''
  returnFilters.reference = ''
  returnFilters.lineId = ''
  returnFilters.dateFrom = ''
  returnFilters.dateTo = ''
  applyReturnFilters()
}

function applyPayoutFilters() {
  payoutPage.value = 1
  loadPayoutBatches()
}

function resetPayoutFilters() {
  payoutFilters.search = ''
  payoutFilters.status = ALL_STATUSES
  payoutFilters.currency = ''
  payoutFilters.supplierId = ''
  payoutFilters.dateFrom = ''
  payoutFilters.dateTo = ''
  applyPayoutFilters()
}

async function createReturnFromForm() {
  const lineId = Number(returnCreateForm.lineId)
  const quantity = Number(returnCreateForm.quantity)
  if (!returnCreateForm.paymentReference.trim() || !Number.isInteger(lineId) || !Number.isInteger(quantity)) {
    toast.add({ title: 'Return details needed', description: 'Add payment reference, line ID, and quantity.', color: 'warning' })
    return
  }
  const line = selectedReturnLine.value
  const returnableQuantity = Number(line?.returnable_quantity ?? line?.quantity ?? 0)
  if (!line || returnableQuantity <= 0) {
    toast.add({ title: 'Line already returned', description: line?.return_locked_reason || 'This item has no remaining quantity available for return.', color: 'warning' })
    return
  }
  if (quantity > returnableQuantity) {
    toast.add({ title: 'Quantity too high', description: `Only ${returnableQuantity} item(s) remain available for return.`, color: 'warning' })
    return
  }
  isReturnsLoading.value = true
  const payload: Record<string, any> = {
    payment_reference: returnCreateForm.paymentReference.trim(),
    line_id: lineId,
    quantity,
    reason: returnCreateForm.reason.trim(),
    restock_decision: returnCreateForm.restockDecision,
    condition_note: returnCreateForm.conditionNote.trim(),
  }
  if (returnCreateForm.refundAmount.trim())
    payload.refund_amount = returnCreateForm.refundAmount.trim()
  const result = await createFinanceReturn(payload)
  if (result.success) {
    toast.add({ title: 'Return case created', description: result.data?.return_reference || 'Ready for review.', color: 'success' })
    returnCreateForm.paymentReference = ''
    returnCreateForm.lineId = ''
    returnCreateForm.quantity = '1'
    returnCreateForm.refundAmount = ''
    returnCreateForm.reason = ''
    returnCreateForm.conditionNote = ''
    await Promise.all([loadReturns(), loadRefunds(), loadPayables(), loadSummary(), refreshReturnLookup()])
  }
  else {
    toast.add({ title: 'Could not create return', description: result.error || 'Please check the order line.', color: 'error' })
  }
  isReturnsLoading.value = false
}

async function actionReturnFromForm() {
  const returnId = Number(returnActionForm.returnId)
  if (!Number.isInteger(returnId) || returnId <= 0) {
    toast.add({ title: 'Return ID needed', description: 'Enter the return case ID from the table.', color: 'warning' })
    return
  }
  isReturnsLoading.value = true
  const payload: Record<string, any> = {
    action: returnActionForm.action,
    restock_decision: returnActionForm.restockDecision,
    notes: returnActionForm.notes.trim(),
  }
  if (returnActionForm.acceptedQuantity.trim())
    payload.accepted_quantity = Number(returnActionForm.acceptedQuantity)
  const result = await updateFinanceReturn(returnId, payload)
  if (result.success) {
    toast.add({ title: 'Return case updated', description: result.data?.return_reference || 'Return workflow advanced.', color: 'success' })
    returnActionForm.returnId = ''
    returnActionForm.acceptedQuantity = ''
    returnActionForm.notes = ''
    await Promise.all([loadReturns(), loadRefunds(), loadPayables(), loadSummary(), refreshReturnLookup()])
  }
  else {
    toast.add({ title: 'Could not update return', description: result.error || 'Please review the action.', color: 'error' })
  }
  isReturnsLoading.value = false
}

async function actionRefundFromForm() {
  const refundId = Number(refundActionForm.refundId)
  if (!Number.isInteger(refundId) || refundId <= 0) {
    toast.add({ title: 'Refund ID needed', description: 'Enter the refund ID from the table.', color: 'warning' })
    return
  }
  isRefundsLoading.value = true
  const result = await updateFinanceRefund(refundId, {
    action: refundActionForm.action,
    provider_reference: refundActionForm.providerReference.trim(),
    notes: refundActionForm.notes.trim(),
  })
  if (result.success) {
    toast.add({ title: 'Refund updated', description: result.data?.refund_reference || 'Refund workflow advanced.', color: 'success' })
    refundActionForm.refundId = ''
    refundActionForm.providerReference = ''
    refundActionForm.notes = ''
    await Promise.all([loadRefunds(), loadReconciliations(), loadSummary(), refreshReturnLookup()])
  }
  else {
    toast.add({ title: 'Could not update refund', description: result.error || 'Please review the action.', color: 'error' })
  }
  isRefundsLoading.value = false
}

async function createBatchFromForm() {
  const payableIds = selectedPayableIds.value.length
    ? selectedPayableIds.value
    : payoutForm.payableIds
        .split(',')
        .map(value => Number(value.trim()))
        .filter(value => Number.isInteger(value) && value > 0)
  if (!payableIds.length) {
    toast.add({ title: 'Add payable IDs', description: 'Enter payable ledger IDs separated by commas.', color: 'warning' })
    return
  }
  isPayoutLoading.value = true
  const result = await createPayoutBatch({
    payable_ids: payableIds,
    payout_method: payoutForm.payoutMethod.trim(),
    notes: payoutForm.notes.trim(),
  })
  if (result.success) {
    toast.add({ title: 'Payout batch created', description: result.data?.batch_reference || 'The batch is ready for review.', color: 'success' })
    payoutForm.payableIds = ''
    selectedPayableIds.value = []
    payoutForm.payoutMethod = ''
    payoutForm.notes = ''
    await Promise.all([loadPayables(), loadPayoutBatches()])
  }
  else {
    toast.add({ title: 'Could not create payout batch', description: result.error || 'Please check selected payable rows.', color: 'error' })
  }
  isPayoutLoading.value = false
}

async function updateBatch(batch: FinancePayoutBatch, action: string) {
  const payload: Record<string, any> = {}
  if (action === 'paid') {
    payload.payout_reference = payoutForm.paidReference.trim()
    payload.evidence_url = payoutForm.evidenceUrl.trim()
    if (payoutEvidenceFile.value)
      payload.evidence_file = payoutEvidenceFile.value
  }
  isPayoutLoading.value = true
  const result = await updatePayoutBatchStatus(batch.id, action, payload)
  if (result.success) {
    toast.add({ title: 'Payout batch updated', description: `${batch.batch_reference} is now ${formatLabel(result.data?.status)}.`, color: 'success' })
    if (action === 'paid') {
      payoutForm.paidReference = ''
      payoutForm.evidenceUrl = ''
      payoutEvidenceFile.value = null
    }
    await Promise.all([loadPayables(), loadPayoutBatches()])
  }
  else {
    toast.add({ title: 'Could not update payout batch', description: result.error || 'Please try again.', color: 'error' })
  }
  isPayoutLoading.value = false
}

function openPayoutCsv(batch: FinancePayoutBatch) {
  window.open(payoutBatchCsvUrl(batch.id), '_blank', 'noopener,noreferrer')
}

function handlePayoutEvidenceChange(event: Event) {
  const input = event.target as HTMLInputElement
  payoutEvidenceFile.value = input.files?.[0] || null
}

function moveReconciliationPage(direction: number) {
  const nextPage = Math.max(1, reconciliationPage.value + direction)
  if (nextPage === reconciliationPage.value)
    return
  reconciliationPage.value = nextPage
  loadReconciliations()
}

function movePayablePage(direction: number) {
  const nextPage = Math.max(1, payablePage.value + direction)
  if (nextPage === payablePage.value)
    return
  payablePage.value = nextPage
  loadPayables()
}

function moveRefundPage(direction: number) {
  const nextPage = Math.max(1, refundPage.value + direction)
  if (nextPage === refundPage.value)
    return
  refundPage.value = nextPage
  loadRefunds()
}

function moveReturnPage(direction: number) {
  const nextPage = Math.max(1, returnPage.value + direction)
  if (nextPage === returnPage.value)
    return
  returnPage.value = nextPage
  loadReturns()
}

function movePayoutPage(direction: number) {
  const nextPage = Math.max(1, payoutPage.value + direction)
  if (nextPage === payoutPage.value)
    return
  payoutPage.value = nextPage
  loadPayoutBatches()
}

watch(pageSize, () => {
  reconciliationPage.value = 1
  payablePage.value = 1
  refundPage.value = 1
  returnPage.value = 1
  payoutPage.value = 1
  loadReconciliations()
  loadPayables()
  loadRefunds()
  loadReturns()
  loadPayoutBatches()
})

onMounted(loadFinance)
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 p-8 pb-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-xl font-semibold">{{ activeViewMeta.title }}</h1>
        <p class="text-sm text-toned">
          {{ activeViewMeta.description }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <USelect v-model="pageSize" :items="pageSizeOptions" class="w-32" />
        <UButton to="/payment-logs" variant="outline">
          <UIcon name="i-lucide-credit-card" />
          Payment logs
        </UButton>
        <UButton to="/suppliers" variant="outline">
          <UIcon name="i-lucide-store" />
          Suppliers
        </UButton>
        <UButton :loading="isLoading" @click="loadFinance">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div v-if="isOverviewView" class="grid grid-cols-1 gap-4 px-8 md:grid-cols-2 xl:grid-cols-6">
      <UCard v-for="card in collectionCards" :key="card.label">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-semibold uppercase text-toned">{{ card.label }}</p>
            <p class="mt-2 truncate text-2xl font-semibold">{{ card.value }}</p>
            <p class="mt-1 text-xs text-toned">{{ card.meta }}</p>
          </div>
          <UIcon :name="card.icon" class="size-6 shrink-0" :class="card.tone" />
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 gap-6 p-8 xl:grid-cols-2">
      <UCard v-if="isOverviewView">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-base font-semibold">Payment Status</h3>
            <UBadge color="neutral" variant="soft">{{ summary?.collections?.count || 0 }} confirmed</UBadge>
          </div>
        </template>
        <UTable :columns="paymentStatusColumns" :data="summary?.collections?.by_status || []" :loading="isLoading" />
      </UCard>

      <UCard v-if="isOverviewView">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-base font-semibold">Payment Methods</h3>
            <UBadge color="neutral" variant="soft">{{ money(summary?.collections?.total) }}</UBadge>
          </div>
        </template>
        <UTable :columns="paymentMethodColumns" :data="summary?.collections?.by_method || []" :loading="isLoading" />
      </UCard>

      <UCard v-if="isView('returns')" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Return Intake And Restock</h3>
              <p class="text-xs text-toned">
                {{ returnPagination.count || 0 }} case(s), {{ money(returnSummary.total) }} return value.
              </p>
            </div>
            <UBadge color="info" variant="soft">{{ returnSummary.accepted_quantity || 0 }} accepted item(s)</UBadge>
          </div>
        </template>

        <div class="mb-4 rounded-lg border border-default p-4">
          <div class="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p class="text-sm font-semibold">1. Load the order</p>
              <p class="text-xs text-toned">Enter the order number. Payment, item lines, quantities, and refund amount will be filled from the order.</p>
            </div>
            <div class="flex flex-col gap-2 md:flex-row md:items-end">
              <UFormField label="Order number" class="md:w-56">
                <UInput v-model="returnLookupOrderNumber" icon="i-lucide-receipt-text" placeholder="100017" @keyup.enter="loadReturnOrder" />
              </UFormField>
              <UButton :loading="isReturnLookupLoading" @click="loadReturnOrder">
                <UIcon name="i-lucide-file-search" />
                Load order
              </UButton>
            </div>
          </div>

          <div v-if="returnLookup" class="space-y-4">
            <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div class="rounded-md border border-default p-3">
                <p class="text-xs font-semibold uppercase text-toned">Order</p>
                <p class="mt-1 font-semibold">#{{ returnLookup.number }}</p>
                <p class="text-xs text-toned">{{ formatLabel(returnLookup.status) }}</p>
              </div>
              <div class="rounded-md border border-default p-3">
                <p class="text-xs font-semibold uppercase text-toned">Customer</p>
                <p class="mt-1 truncate font-semibold">{{ returnLookup.customer_email || 'Guest customer' }}</p>
              </div>
              <div class="rounded-md border border-default p-3">
                <p class="text-xs font-semibold uppercase text-toned">Paid</p>
                <p class="mt-1 font-semibold">{{ money(returnLookup.totals?.paid_total) }}</p>
              </div>
              <div class="rounded-md border border-default p-3">
                <p class="text-xs font-semibold uppercase text-toned">Existing returns</p>
                <p class="mt-1 font-semibold">{{ returnLookup.returns?.length || 0 }}</p>
              </div>
            </div>

            <div class="overflow-x-auto rounded-lg border border-default">
              <table class="min-w-full divide-y divide-default text-sm">
                <thead class="bg-muted">
                  <tr>
                    <th class="px-4 py-3 text-left font-semibold">Item</th>
                    <th class="px-4 py-3 text-left font-semibold">Qty bought</th>
                    <th class="px-4 py-3 text-left font-semibold">Returnable</th>
                    <th class="px-4 py-3 text-left font-semibold">Line total</th>
                    <th class="px-4 py-3 text-left font-semibold">Supplier payable</th>
                    <th class="px-4 py-3 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-default">
                  <tr v-for="line in returnLookup.lines" :key="line.line_id" :class="Number(returnCreateForm.lineId) === line.line_id ? 'bg-primary/10' : ''">
                    <td class="px-4 py-3">
                      <p class="font-semibold">{{ line.title }}</p>
                      <p class="text-xs text-toned">{{ line.sku || 'No SKU' }}</p>
                    </td>
                    <td class="px-4 py-3">{{ line.quantity }}</td>
                    <td class="px-4 py-3">
                      <p class="font-semibold">{{ line.returnable_quantity ?? line.quantity }}</p>
                      <p v-if="line.open_return_quantity || line.completed_return_quantity" class="text-xs text-toned">
                        {{ line.open_return_quantity || 0 }} open, {{ line.completed_return_quantity || 0 }} done
                      </p>
                    </td>
                    <td class="px-4 py-3">{{ money(line.line_price_incl_tax) }}</td>
                    <td class="px-4 py-3">{{ money(line.supplier_payable_total) }}</td>
                    <td class="px-4 py-3 text-right">
                      <UButton size="xs" color="neutral" variant="outline" :disabled="Number(line.returnable_quantity ?? line.quantity ?? 0) <= 0" @click="useReturnLine(line)">
                        Select
                      </UButton>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="mb-4 rounded-lg border border-default p-4">
          <div class="mb-4">
            <p class="text-sm font-semibold">2. Create the return case</p>
            <p class="text-xs text-toned">After selecting an item, only adjust quantity, reason, and restock decision if needed.</p>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <UFormField label="Payment">
              <USelect v-if="returnPaymentOptions.length" v-model="returnCreateForm.paymentReference" :items="returnPaymentOptions" />
              <UInput v-else v-model="returnCreateForm.paymentReference" placeholder="PAY-..." />
            </UFormField>
            <UFormField label="Selected item">
              <UInput :model-value="selectedReturnLine?.title || 'Load order and select an item'" disabled />
            </UFormField>
            <UFormField label="Quantity">
              <UInput v-model="returnCreateForm.quantity" type="number" min="1" @blur="autofillReturnAmount" @change="autofillReturnAmount" />
            </UFormField>
            <UFormField label="Refund amount">
              <UInput v-model="returnCreateForm.refundAmount" placeholder="Auto from selected item" />
            </UFormField>
            <UFormField label="Restock decision"><USelect v-model="returnCreateForm.restockDecision" :items="restockDecisionOptions" /></UFormField>
            <UFormField label="Condition"><UInput v-model="returnCreateForm.conditionNote" placeholder="Sealed, damaged, missing parts" /></UFormField>
            <UFormField label="Reason"><UInput v-model="returnCreateForm.reason" placeholder="Customer return reason" /></UFormField>
            <div class="flex items-end">
              <UButton class="w-full justify-center" :disabled="!canCreateReturn" :loading="isReturnsLoading" @click="createReturnFromForm">
                <UIcon name="i-lucide-rotate-ccw-square" />
                Create return
              </UButton>
            </div>
          </div>
        </div>

        <div class="mb-4 rounded-lg border border-default p-4">
          <div class="mb-4">
            <p class="text-sm font-semibold">3. Update return status</p>
            <p class="text-xs text-toned">Use this after the item is approved, received, accepted, refunded, rejected, or cancelled.</p>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
            <UFormField label="Return ID"><UInput v-model="returnActionForm.returnId" placeholder="ID from table" /></UFormField>
            <UFormField label="Action"><USelect v-model="returnActionForm.action" :items="returnActionOptions" /></UFormField>
            <UFormField label="Accepted qty"><UInput v-model="returnActionForm.acceptedQuantity" placeholder="Defaults to requested" /></UFormField>
            <UFormField label="Restock decision"><USelect v-model="returnActionForm.restockDecision" :items="restockDecisionOptions" /></UFormField>
            <UFormField label="Notes"><UInput v-model="returnActionForm.notes" placeholder="Review notes" @keyup.enter="actionReturnFromForm" /></UFormField>
          </div>
          <div class="mt-4 flex justify-end">
            <UButton color="neutral" variant="outline" :loading="isReturnsLoading" @click="actionReturnFromForm">
              <UIcon name="i-lucide-check-check" />
              Update return
            </UButton>
          </div>
        </div>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Search"><UInput v-model="returnFilters.search" icon="i-lucide-search" placeholder="Return, payment, line" @keyup.enter="applyReturnFilters" /></UFormField>
          <UFormField label="Status"><USelect v-model="returnFilters.status" :items="returnStatusOptions" /></UFormField>
          <UFormField label="Restock"><USelect v-model="returnFilters.restockDecision" :items="restockFilterOptions" /></UFormField>
          <UFormField label="Currency"><UInput v-model="returnFilters.currency" placeholder="KES" @keyup.enter="applyReturnFilters" /></UFormField>
          <UFormField label="Order"><UInput v-model="returnFilters.orderNumber" placeholder="100017" @keyup.enter="applyReturnFilters" /></UFormField>
          <UFormField label="Reference"><UInput v-model="returnFilters.reference" placeholder="RTN-..." @keyup.enter="applyReturnFilters" /></UFormField>
          <UFormField label="Line ID"><UInput v-model="returnFilters.lineId" placeholder="123" @keyup.enter="applyReturnFilters" /></UFormField>
          <UFormField label="From"><UInput v-model="returnFilters.dateFrom" type="date" /></UFormField>
          <UFormField label="To"><UInput v-model="returnFilters.dateTo" type="date" /></UFormField>
        </div>
        <div class="mb-4 flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="resetReturnFilters">
            <UIcon name="i-lucide-rotate-ccw" />
            Reset
          </UButton>
          <UButton :loading="isReturnsLoading" @click="applyReturnFilters">
            <UIcon name="i-lucide-filter" />
            Apply
          </UButton>
        </div>
        <UTable :columns="returnColumns" :data="returns" :loading="isReturnsLoading" />
        <div class="mt-4 flex items-center justify-between gap-3 text-sm text-toned">
          <span>Page {{ returnPagination.page || returnPage }} of {{ returnPagination.num_pages || 1 }}</span>
          <div class="flex gap-2">
            <UButton color="neutral" variant="outline" :disabled="!returnPagination.has_previous" @click="moveReturnPage(-1)">Previous</UButton>
            <UButton color="neutral" variant="outline" :disabled="!returnPagination.has_next" @click="moveReturnPage(1)">Next</UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="isView('refunds')" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Refund And Reversal Ledger</h3>
              <p class="text-xs text-toned">
                {{ refundPagination.count || 0 }} row(s), {{ money(refundSummary.total) }} total.
              </p>
            </div>
            <UBadge color="warning" variant="soft">{{ summary?.refunds?.count || 0 }} refund record(s)</UBadge>
          </div>
        </template>

        <div class="mb-4 rounded-lg border border-default p-4">
          <div class="mb-4">
            <p class="text-sm font-semibold">Refund workflow</p>
            <p class="text-xs text-toned">Use the refund ID from the table. Requested refunds can be submitted or cancelled; submitted refunds can be marked succeeded or failed.</p>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
            <UFormField label="Refund ID"><UInput v-model="refundActionForm.refundId" placeholder="ID from table" /></UFormField>
            <UFormField label="Action"><USelect v-model="refundActionForm.action" :items="refundActionOptions" /></UFormField>
            <UFormField label="Provider reference"><UInput v-model="refundActionForm.providerReference" placeholder="Gateway or bank ref" /></UFormField>
            <UFormField label="Notes"><UInput v-model="refundActionForm.notes" placeholder="Review notes" @keyup.enter="actionRefundFromForm" /></UFormField>
            <div class="flex items-end">
              <UButton class="w-full justify-center" :loading="isRefundsLoading" @click="actionRefundFromForm">
                <UIcon name="i-lucide-check-check" />
                Update refund
              </UButton>
            </div>
          </div>
        </div>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Search"><UInput v-model="refundFilters.search" icon="i-lucide-search" placeholder="Refund, payment, reason" @keyup.enter="applyRefundFilters" /></UFormField>
          <UFormField label="Status"><USelect v-model="refundFilters.status" :items="refundStatusOptions" /></UFormField>
          <UFormField label="Type"><USelect v-model="refundFilters.refundType" :items="refundTypeOptions" /></UFormField>
          <UFormField label="Currency"><UInput v-model="refundFilters.currency" placeholder="KES" @keyup.enter="applyRefundFilters" /></UFormField>
          <UFormField label="Order"><UInput v-model="refundFilters.orderNumber" placeholder="100017" @keyup.enter="applyRefundFilters" /></UFormField>
          <UFormField label="Reference"><UInput v-model="refundFilters.reference" placeholder="REFUND-..." @keyup.enter="applyRefundFilters" /></UFormField>
          <UFormField label="From"><UInput v-model="refundFilters.dateFrom" type="date" /></UFormField>
          <UFormField label="To"><UInput v-model="refundFilters.dateTo" type="date" /></UFormField>
        </div>
        <div class="mb-4 flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="resetRefundFilters">
            <UIcon name="i-lucide-rotate-ccw" />
            Reset
          </UButton>
          <UButton :loading="isRefundsLoading" @click="applyRefundFilters">
            <UIcon name="i-lucide-filter" />
            Apply
          </UButton>
        </div>
        <UTable :columns="refundColumns" :data="refunds" :loading="isRefundsLoading" />
        <div class="mt-4 flex items-center justify-between gap-3 text-sm text-toned">
          <span>Page {{ refundPagination.page || refundPage }} of {{ refundPagination.num_pages || 1 }}</span>
          <div class="flex gap-2">
            <UButton color="neutral" variant="outline" :disabled="!refundPagination.has_previous" @click="moveRefundPage(-1)">Previous</UButton>
            <UButton color="neutral" variant="outline" :disabled="!refundPagination.has_next" @click="moveRefundPage(1)">Next</UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="isView('reconciliation')" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Payment Reconciliation</h3>
              <p class="text-xs text-toned">
                {{ reconciliationPagination.count || 0 }} row(s), {{ money(reconciliationSummary.paid_total) }} paid.
              </p>
            </div>
            <UBadge :color="reconciliationStatusColor()" variant="soft">
              {{ summary?.reconciliation?.unresolved_count || 0 }} unresolved
            </UBadge>
          </div>
        </template>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Search"><UInput v-model="reconciliationFilters.search" icon="i-lucide-search" placeholder="Reference, order, email" @keyup.enter="applyReconciliationFilters" /></UFormField>
          <UFormField label="Status"><USelect v-model="reconciliationFilters.status" :items="reconciliationStatusOptions" /></UFormField>
          <UFormField label="Provider"><USelect v-model="reconciliationFilters.provider" :items="providerOptions" /></UFormField>
          <UFormField label="Currency"><UInput v-model="reconciliationFilters.currency" placeholder="KES" @keyup.enter="applyReconciliationFilters" /></UFormField>
          <UFormField label="Order"><UInput v-model="reconciliationFilters.orderNumber" placeholder="100017" @keyup.enter="applyReconciliationFilters" /></UFormField>
          <UFormField label="Reference"><UInput v-model="reconciliationFilters.reference" placeholder="PAY-..." @keyup.enter="applyReconciliationFilters" /></UFormField>
          <UFormField label="From"><UInput v-model="reconciliationFilters.dateFrom" type="date" /></UFormField>
          <UFormField label="To"><UInput v-model="reconciliationFilters.dateTo" type="date" /></UFormField>
        </div>
        <div class="mb-4 flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="resetReconciliationFilters">
            <UIcon name="i-lucide-rotate-ccw" />
            Reset
          </UButton>
          <UButton :loading="isReconLoading" @click="applyReconciliationFilters">
            <UIcon name="i-lucide-filter" />
            Apply
          </UButton>
        </div>
        <div class="overflow-x-auto rounded-lg border border-default">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead class="bg-muted">
              <tr>
                <th class="px-4 py-3 text-left font-semibold">Payment</th>
                <th class="px-4 py-3 text-left font-semibold">Order</th>
                <th class="px-4 py-3 text-left font-semibold">Provider</th>
                <th class="px-4 py-3 text-left font-semibold">Expected</th>
                <th class="px-4 py-3 text-left font-semibold">Paid</th>
                <th class="px-4 py-3 text-left font-semibold">Status</th>
                <th class="px-4 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-default">
              <tr v-for="row in reconciliations" :key="row.id">
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ row.payment_reference }}</p>
                  <p class="text-xs text-toned">{{ row.provider_reference || row.merchant_reference || 'No provider ref' }}</p>
                </td>
                <td class="px-4 py-3">{{ row.order_number || 'Unlinked' }}</td>
                <td class="px-4 py-3">{{ formatLabel(row.provider) }}</td>
                <td class="px-4 py-3">{{ money(row.expected_amount) }}</td>
                <td class="px-4 py-3">{{ money(row.paid_amount) }}</td>
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ formatLabel(row.status) }}</p>
                  <p class="max-w-xs truncate text-xs text-toned">{{ row.issues?.length ? row.issues.join(', ') : 'No issues' }}</p>
                </td>
                <td class="px-4 py-3">
                  <div class="flex justify-end gap-2">
                    <UTooltip :text="canQuickMatchReconciliation(row) ? 'Confirm this row as reconciled' : 'Unlinked or issue rows should stay in review until fixed'">
                      <UButton size="xs" color="success" variant="outline" :disabled="!canQuickMatchReconciliation(row)" @click="reviewReconciliation(row, 'matched')">Mark matched</UButton>
                    </UTooltip>
                    <UButton size="xs" color="warning" variant="outline" :disabled="row.status === 'manual_review'" @click="reviewReconciliation(row, 'manual_review')">Review</UButton>
                  </div>
                </td>
              </tr>
              <tr v-if="!isReconLoading && !reconciliations.length">
                <td class="px-4 py-8 text-center text-toned" colspan="7">No reconciliation rows found.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 flex items-center justify-between gap-3 text-sm text-toned">
          <span>Page {{ reconciliationPagination.page || reconciliationPage }} of {{ reconciliationPagination.num_pages || 1 }}</span>
          <div class="flex gap-2">
            <UButton color="neutral" variant="outline" :disabled="!reconciliationPagination.has_previous" @click="moveReconciliationPage(-1)">Previous</UButton>
            <UButton color="neutral" variant="outline" :disabled="!reconciliationPagination.has_next" @click="moveReconciliationPage(1)">Next</UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="isView('supplier-payables')" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Supplier Payables</h3>
              <p class="text-xs text-toned">
                {{ payablePagination.count || 0 }} row(s), {{ money(payableSummary.payable_total) }} net supplier payable.
              </p>
            </div>
            <UBadge color="primary" variant="soft">{{ money(summary?.supplier_payables?.ready_total) }} ready</UBadge>
          </div>
        </template>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Search"><UInput v-model="payableFilters.search" icon="i-lucide-search" placeholder="Supplier, order, product" @keyup.enter="applyPayableFilters" /></UFormField>
          <UFormField label="Status"><USelect v-model="payableFilters.status" :items="payableStatusOptions" /></UFormField>
          <UFormField label="Currency"><UInput v-model="payableFilters.currency" placeholder="KES" @keyup.enter="applyPayableFilters" /></UFormField>
          <UFormField label="Order"><UInput v-model="payableFilters.orderNumber" placeholder="100017" @keyup.enter="applyPayableFilters" /></UFormField>
          <UFormField label="Supplier">
            <div class="relative">
              <UInput
                v-model="supplierSearch"
                icon="i-lucide-store"
                placeholder="Search supplier name"
                autocomplete="off"
                @focus="openSupplierPicker"
                @input="queueSupplierSearch"
                @keyup.enter="applyPayableFilters"
                @keydown.esc="supplierPickerOpen = false"
              >
                <template v-if="payableFilters.supplierId || supplierSearch" #trailing>
                  <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-x" @click.stop="clearSupplierFilter" />
                </template>
              </UInput>
              <div
                v-if="supplierPickerOpen"
                class="absolute z-30 mt-1 max-h-64 w-full overflow-auto rounded-md border border-default bg-default shadow-lg"
              >
                <button
                  v-for="supplier in supplierOptions"
                  :key="supplier.id"
                  type="button"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-muted"
                  @mousedown.prevent="selectSupplierFilter(supplier)"
                >
                  <span class="block font-semibold">{{ supplier.company_name || supplier.partner?.name || 'Unnamed supplier' }}</span>
                  <span class="block text-xs text-toned">
                    {{ supplier.contact_name || supplier.user?.email || 'No contact' }}
                    <span v-if="supplier.account_manager"> · Manager: {{ supplier.account_manager.name || supplier.account_manager.email }}</span>
                  </span>
                </button>
                <div v-if="isSupplierPickerLoading" class="px-3 py-2 text-sm text-toned">
                  <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
                  Loading suppliers
                </div>
                <div v-else-if="!supplierOptions.length" class="px-3 py-2 text-sm text-toned">No suppliers found.</div>
              </div>
            </div>
          </UFormField>
          <UFormField label="Account Manager">
            <div class="relative">
              <UInput
                v-model="accountManagerSearch"
                icon="i-lucide-user-round"
                placeholder="Search account manager"
                autocomplete="off"
                @focus="openAccountManagerPicker"
                @input="queueAccountManagerSearch"
                @keyup.enter="applyPayableFilters"
                @keydown.esc="accountManagerPickerOpen = false"
              >
                <template v-if="payableFilters.accountManagerId || accountManagerSearch" #trailing>
                  <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-x" @click.stop="clearAccountManagerFilter" />
                </template>
              </UInput>
              <div
                v-if="accountManagerPickerOpen"
                class="absolute z-30 mt-1 max-h-64 w-full overflow-auto rounded-md border border-default bg-default shadow-lg"
              >
                <button
                  v-for="manager in accountManagerOptions"
                  :key="manager.id"
                  type="button"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-muted"
                  @mousedown.prevent="selectAccountManagerFilter(manager)"
                >
                  <span class="block font-semibold">{{ manager.name || manager.email }}</span>
                  <span class="block text-xs text-toned">{{ manager.email }}</span>
                </button>
                <div v-if="isAccountManagerPickerLoading" class="px-3 py-2 text-sm text-toned">
                  <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
                  Loading account managers
                </div>
                <div v-else-if="!accountManagerOptions.length" class="px-3 py-2 text-sm text-toned">No account managers found.</div>
              </div>
            </div>
          </UFormField>
          <UFormField label="From"><UInput v-model="payableFilters.dateFrom" type="date" /></UFormField>
          <UFormField label="To"><UInput v-model="payableFilters.dateTo" type="date" /></UFormField>
        </div>
        <div class="mb-4 flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="resetPayableFilters">
            <UIcon name="i-lucide-rotate-ccw" />
            Reset
          </UButton>
          <UButton color="primary" variant="soft" :loading="isPayablesLoading" @click="fetchReadyUnpaidPayables">
            <UIcon name="i-lucide-wallet-cards" />
            Fetch unpaid payouts
          </UButton>
          <UButton :loading="isPayablesLoading" @click="applyPayableFilters">
            <UIcon name="i-lucide-filter" />
            Apply
          </UButton>
        </div>
        <div class="mb-4 flex flex-col gap-3 rounded-lg border border-default p-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p class="text-sm font-semibold">Create payout from selected rows</p>
            <p class="text-xs text-toned">{{ selectedPayableIds.length }} payable row(s) selected. Only payable or approved rows can be selected.</p>
          </div>
          <div class="grid w-full grid-cols-1 gap-2 md:w-auto md:grid-cols-3">
            <UInput v-model="payoutForm.payoutMethod" placeholder="Payout method" />
            <UInput v-model="payoutForm.notes" placeholder="Notes" />
            <UButton :disabled="!selectedPayableIds.length" :loading="isPayoutLoading" @click="createBatchFromForm">
              <UIcon name="i-lucide-folder-plus" />
              Create batch
            </UButton>
          </div>
        </div>
        <div class="overflow-x-auto rounded-lg border border-default">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead class="bg-muted">
              <tr>
                <th class="px-4 py-3 text-left font-semibold">Select</th>
                <th class="px-4 py-3 text-left font-semibold">Supplier</th>
                <th class="px-4 py-3 text-left font-semibold">Order</th>
                <th class="px-4 py-3 text-left font-semibold">Product</th>
                <th class="px-4 py-3 text-left font-semibold">Qty</th>
                <th class="px-4 py-3 text-left font-semibold">Payable</th>
                <th class="px-4 py-3 text-left font-semibold">Margin</th>
                <th class="px-4 py-3 text-left font-semibold">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-default">
              <tr v-for="payable in payables" :key="payable.id">
                <td class="px-4 py-3">
                  <UCheckbox
                    :model-value="isPayableSelected(payable.id)"
                    :disabled="!selectablePayable(payable)"
                    @update:model-value="togglePayableSelection(payable.id, Boolean($event))"
                  />
                </td>
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ payable.supplier_name || payable.partner_name || 'Unknown supplier' }}</p>
                  <p class="text-xs text-toned">{{ payable.account_manager_email || 'Unassigned' }}</p>
                </td>
                <td class="px-4 py-3">{{ payable.order_number }}</td>
                <td class="px-4 py-3">{{ payable.product_title }}</td>
                <td class="px-4 py-3">{{ payable.quantity }}</td>
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ money(payable.net_payable_total ?? payable.payable_total) }}</p>
                  <p v-if="Number(payable.adjustment_debit_total || 0) || Number(payable.adjustment_reversal_total || 0)" class="text-xs text-toned">
                    Gross {{ money(payable.payable_total) }} less adjustments {{ money(Number(payable.adjustment_debit_total || 0) + Number(payable.adjustment_reversal_total || 0)) }}
                  </p>
                </td>
                <td class="px-4 py-3">{{ money(payable.gross_margin) }}</td>
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ formatLabel(payable.status) }}</p>
                  <p v-if="payable.reversal_reason" class="max-w-xs truncate text-xs text-toned">{{ payable.reversal_reason }}</p>
                </td>
              </tr>
              <tr v-if="!isPayablesLoading && !payables.length">
                <td class="px-4 py-8 text-center text-toned" colspan="8">No supplier payable rows found.</td>
              </tr>
              <tr v-if="isPayablesLoading">
                <td class="px-4 py-8 text-center text-toned" colspan="8">
                  <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
                  Loading supplier payables
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 flex items-center justify-between gap-3 text-sm text-toned">
          <span>Page {{ payablePagination.page || payablePage }} of {{ payablePagination.num_pages || 1 }}</span>
          <div class="flex gap-2">
            <UButton color="neutral" variant="outline" :disabled="!payablePagination.has_previous" @click="movePayablePage(-1)">Previous</UButton>
            <UButton color="neutral" variant="outline" :disabled="!payablePagination.has_next" @click="movePayablePage(1)">Next</UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="isView('payout-batches')" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Supplier Payout Batches</h3>
              <p class="text-xs text-toned">
                {{ payoutPagination.count || 0 }} batch(es), {{ money(payoutSummary.total_amount) }} total selected for payout.
              </p>
            </div>
            <UBadge color="neutral" variant="soft">CSV export ready</UBadge>
          </div>
        </template>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Payable IDs">
            <UInput v-model="payoutForm.payableIds" placeholder="12, 13, 14" @keyup.enter="createBatchFromForm" />
          </UFormField>
          <UFormField label="Payout method">
            <UInput v-model="payoutForm.payoutMethod" placeholder="Bank transfer, M-Pesa" @keyup.enter="createBatchFromForm" />
          </UFormField>
          <UFormField label="Notes">
            <UInput v-model="payoutForm.notes" placeholder="July supplier payout" @keyup.enter="createBatchFromForm" />
          </UFormField>
          <div class="flex items-end">
            <UButton class="w-full justify-center" :loading="isPayoutLoading" @click="createBatchFromForm">
              <UIcon name="i-lucide-folder-plus" />
              Create batch
            </UButton>
          </div>
        </div>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <UFormField label="Search"><UInput v-model="payoutFilters.search" icon="i-lucide-search" placeholder="Batch, supplier, reference" @keyup.enter="applyPayoutFilters" /></UFormField>
          <UFormField label="Status"><USelect v-model="payoutFilters.status" :items="payoutStatusOptions" /></UFormField>
          <UFormField label="Currency"><UInput v-model="payoutFilters.currency" placeholder="KES" @keyup.enter="applyPayoutFilters" /></UFormField>
          <UFormField label="Supplier ID"><UInput v-model="payoutFilters.supplierId" placeholder="12" @keyup.enter="applyPayoutFilters" /></UFormField>
          <UFormField label="From"><UInput v-model="payoutFilters.dateFrom" type="date" /></UFormField>
          <UFormField label="To"><UInput v-model="payoutFilters.dateTo" type="date" /></UFormField>
          <UFormField label="Paid reference"><UInput v-model="payoutForm.paidReference" placeholder="Bank/M-Pesa reference" /></UFormField>
          <UFormField label="Evidence URL"><UInput v-model="payoutForm.evidenceUrl" placeholder="https://..." /></UFormField>
          <UFormField label="Evidence file">
            <UInput type="file" accept="image/*,.pdf" @change="handlePayoutEvidenceChange" />
          </UFormField>
        </div>
        <div class="mb-4 flex justify-end gap-2">
          <UButton color="neutral" variant="outline" @click="resetPayoutFilters">
            <UIcon name="i-lucide-rotate-ccw" />
            Reset
          </UButton>
          <UButton :loading="isPayoutLoading" @click="applyPayoutFilters">
            <UIcon name="i-lucide-filter" />
            Apply
          </UButton>
        </div>

        <div class="overflow-x-auto rounded-lg border border-default">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead class="bg-muted">
              <tr>
                <th class="px-4 py-3 text-left font-semibold">Batch</th>
                <th class="px-4 py-3 text-left font-semibold">Supplier</th>
                <th class="px-4 py-3 text-left font-semibold">Status</th>
                <th class="px-4 py-3 text-left font-semibold">Entries</th>
                <th class="px-4 py-3 text-left font-semibold">Total</th>
                <th class="px-4 py-3 text-left font-semibold">Reference</th>
                <th class="px-4 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-default">
              <tr v-for="batch in payoutBatches" :key="batch.id">
                <td class="px-4 py-3">
                  <p class="font-semibold">{{ batch.batch_reference }}</p>
                  <p class="text-xs text-toned">{{ formatDate(batch.created_at) }}</p>
                </td>
                <td class="px-4 py-3">{{ batch.supplier_name || batch.partner_name || 'Unknown' }}</td>
                <td class="px-4 py-3">{{ formatLabel(batch.status) }}</td>
                <td class="px-4 py-3">{{ batch.entry_count }}</td>
                <td class="px-4 py-3">{{ money(batch.total_amount) }}</td>
                <td class="px-4 py-3">
                  <p>{{ batch.payout_reference || 'Not paid' }}</p>
                  <div v-if="batch.evidence_file_url || batch.evidence_url" class="mt-1 flex flex-wrap gap-2 text-xs">
                    <a v-if="batch.evidence_file_url" :href="batch.evidence_file_url" target="_blank" rel="noopener noreferrer" class="text-primary">Evidence file</a>
                    <a v-if="batch.evidence_url" :href="batch.evidence_url" target="_blank" rel="noopener noreferrer" class="text-primary">Evidence URL</a>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap justify-end gap-2">
                    <UButton v-if="batch.status === 'draft'" size="xs" color="neutral" variant="outline" @click="updateBatch(batch, 'submit')">Submit</UButton>
                    <UButton v-if="['draft', 'pending_approval'].includes(batch.status)" size="xs" color="primary" variant="outline" @click="updateBatch(batch, 'approve')">Approve</UButton>
                    <UButton v-if="batch.status === 'approved'" size="xs" color="success" variant="outline" @click="updateBatch(batch, 'paid')">Paid</UButton>
                    <UButton v-if="batch.status !== 'paid' && batch.status !== 'cancelled'" size="xs" color="error" variant="outline" @click="updateBatch(batch, 'cancel')">Cancel</UButton>
                    <UButton size="xs" color="neutral" variant="outline" @click="openPayoutCsv(batch)">CSV</UButton>
                  </div>
                </td>
              </tr>
              <tr v-if="!isPayoutLoading && !payoutBatches.length">
                <td class="px-4 py-8 text-center text-toned" colspan="7">No payout batches found.</td>
              </tr>
              <tr v-if="isPayoutLoading">
                <td class="px-4 py-8 text-center text-toned" colspan="7">
                  <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
                  Loading payout batches
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-4 flex items-center justify-between gap-3 text-sm text-toned">
          <span>Page {{ payoutPagination.page || payoutPage }} of {{ payoutPagination.num_pages || 1 }}</span>
          <div class="flex gap-2">
            <UButton color="neutral" variant="outline" :disabled="!payoutPagination.has_previous" @click="movePayoutPage(-1)">Previous</UButton>
            <UButton color="neutral" variant="outline" :disabled="!payoutPagination.has_next" @click="movePayoutPage(1)">Next</UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="isOverviewView" class="xl:col-span-2">
        <template #header>
          <h3 class="text-base font-semibold">Finance Controls</h3>
        </template>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Gross margin</p>
            <p class="mt-2 text-xl font-semibold">{{ money(summary?.margin?.gross_margin_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Gateway fees</p>
            <p class="mt-2 text-xl font-semibold">{{ money(summary?.fees?.gateway_fee_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Net before overheads</p>
            <p class="mt-2 text-xl font-semibold">{{ money(summary?.margin?.net_margin_before_overheads) }}</p>
          </div>
        </div>
      </UCard>

      <UCard v-if="activeView === 'order'" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Find Order Finance</h3>
              <p class="text-xs text-toned">Enter an order number to load its payment, refund, payable, return, and margin rows.</p>
            </div>
          </div>
        </template>
        <div class="flex flex-col gap-3 md:flex-row md:items-end">
          <UFormField label="Order number" class="w-full md:max-w-xs">
            <UInput v-model="orderFinanceNumber" icon="i-lucide-receipt-text" placeholder="100017" @keyup.enter="loadOrderFinance" />
          </UFormField>
          <UButton :loading="isOrderFinanceLoading" @click="loadOrderFinance">
            <UIcon name="i-lucide-file-search" />
            Load order finance
          </UButton>
        </div>
      </UCard>

      <UCard v-if="orderFinance && activeView === 'order'" class="xl:col-span-2">
        <template #header>
          <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-base font-semibold">Order Finance: #{{ orderFinance.number }}</h3>
              <p class="text-xs text-toned">
                {{ orderFinance.customer_email || 'Guest customer' }} · {{ formatLabel(orderFinance.status) }} · {{ formatDate(orderFinance.date_placed) }}
              </p>
            </div>
            <UBadge color="primary" variant="soft">{{ money(orderFinance.totals?.order_incl_tax) }}</UBadge>
          </div>
        </template>

        <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Paid by customer</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.paid_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Supplier payable</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.supplier_payable_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Gross margin</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.gross_margin_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Net before overheads</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.net_margin_before_overheads) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Shipping charged</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.shipping_incl_tax) }}</p>
            <p class="mt-1 text-xs text-toned">{{ orderFinance.shipping_method || 'No shipping method' }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Gateway fees</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.gateway_fee_total) }}</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Refunds</p>
            <p class="mt-2 text-xl font-semibold">{{ money(orderFinance.totals?.refund_total) }}</p>
            <p class="mt-1 text-xs text-toned">{{ orderFinance.refunds?.count || 0 }} request(s)</p>
          </div>
          <div class="rounded-lg border border-default p-4">
            <p class="text-xs font-semibold uppercase text-toned">Reconciliation rows</p>
            <p class="mt-2 text-xl font-semibold">{{ orderFinance.reconciliations?.length || 0 }}</p>
          </div>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
          <div class="rounded-lg border border-default">
            <div class="border-b border-default px-4 py-3">
              <h4 class="text-sm font-semibold">Payments</h4>
            </div>
            <div class="divide-y divide-default">
              <div v-for="payment in orderFinance.payments" :key="payment.id" class="grid grid-cols-1 gap-2 px-4 py-3 text-sm md:grid-cols-4">
                <div>
                  <p class="text-xs text-toned">Reference</p>
                  <p class="font-semibold">{{ payment.reference }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Method</p>
                  <p class="font-semibold">{{ formatLabel(payment.method) }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Status</p>
                  <p class="font-semibold">{{ formatLabel(payment.status) }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Amount</p>
                  <p class="font-semibold">{{ money(payment.amount) }}</p>
                </div>
              </div>
              <div v-if="!orderFinance.payments?.length" class="px-4 py-6 text-sm text-toned">No payments linked.</div>
            </div>
          </div>

          <div class="rounded-lg border border-default">
            <div class="border-b border-default px-4 py-3">
              <h4 class="text-sm font-semibold">Reconciliation</h4>
            </div>
            <div class="divide-y divide-default">
              <div v-for="row in orderFinance.reconciliations" :key="row.id" class="grid grid-cols-1 gap-2 px-4 py-3 text-sm md:grid-cols-4">
                <div>
                  <p class="text-xs text-toned">Status</p>
                  <p class="font-semibold">{{ formatLabel(row.status) }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Provider ref</p>
                  <p class="font-semibold">{{ row.provider_reference || row.payment_reference }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Paid</p>
                  <p class="font-semibold">{{ money(row.paid_amount) }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Issues</p>
                  <p class="font-semibold">{{ row.issues?.length ? row.issues.join(', ') : 'None' }}</p>
                </div>
              </div>
              <div v-if="!orderFinance.reconciliations?.length" class="px-4 py-6 text-sm text-toned">No reconciliation rows linked.</div>
            </div>
          </div>

          <div class="rounded-lg border border-default">
            <div class="border-b border-default px-4 py-3">
              <h4 class="text-sm font-semibold">Returns</h4>
            </div>
            <div class="divide-y divide-default">
              <div v-for="returnCase in orderFinance.returns" :key="returnCase.id" class="grid grid-cols-1 gap-2 px-4 py-3 text-sm md:grid-cols-4">
                <div>
                  <p class="text-xs text-toned">Reference</p>
                  <p class="font-semibold">{{ returnCase.return_reference }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Status</p>
                  <p class="font-semibold">{{ formatLabel(returnCase.status) }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Qty</p>
                  <p class="font-semibold">{{ returnCase.accepted_quantity || returnCase.quantity }}</p>
                </div>
                <div>
                  <p class="text-xs text-toned">Refund</p>
                  <p class="font-semibold">{{ money(returnCase.refund_amount) }}</p>
                </div>
              </div>
              <div v-if="!orderFinance.returns?.length" class="px-4 py-6 text-sm text-toned">No return cases linked.</div>
            </div>
          </div>
        </div>

        <div class="mt-6 overflow-hidden rounded-lg border border-default">
          <div class="border-b border-default px-4 py-3">
            <h4 class="text-sm font-semibold">Line Finance</h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-default text-sm">
              <thead class="bg-muted">
                <tr>
                  <th class="px-4 py-3 text-left font-semibold">Product</th>
                  <th class="px-4 py-3 text-left font-semibold">Qty</th>
                  <th class="px-4 py-3 text-left font-semibold">Customer line</th>
                  <th class="px-4 py-3 text-left font-semibold">Supplier payable</th>
                  <th class="px-4 py-3 text-left font-semibold">Margin</th>
                  <th class="px-4 py-3 text-left font-semibold">Supplier</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-default">
                <tr v-for="line in orderFinance.lines" :key="line.line_id">
                  <td class="px-4 py-3">
                    <p class="font-semibold">{{ line.title }}</p>
                    <p class="text-xs text-toned">{{ line.sku || 'No SKU' }}</p>
                  </td>
                  <td class="px-4 py-3">{{ line.quantity }}</td>
                  <td class="px-4 py-3">{{ money(line.line_price_incl_tax) }}</td>
                  <td class="px-4 py-3">{{ money(line.supplier_payable_total) }}</td>
                  <td class="px-4 py-3">{{ money(line.gross_margin_total) }}</td>
                  <td class="px-4 py-3">
                    <span v-if="line.payables?.length">
                      {{ line.payables.map(payable => payable.supplier_name).join(', ') }}
                    </span>
                    <span v-else class="text-toned">No supplier payable</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
