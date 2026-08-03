<script setup lang="ts">
const toast = useToast()
const {
  cancelBankTransaction,
  createBankTransaction,
  createJournal,
  getTrialBalance,
  importBankTransactionsCsv,
  listAccounts,
  listBankTransactions,
  listGeneralLedger,
  listJournals,
  listPaymentLedger,
  listReconciliationAllocations,
  listReconciliationCandidates,
  reconcileBankTransaction,
} = useAccounting()

const activeTab = ref('trial-balance')
const isLoading = ref(false)
const accounts = ref<any[]>([])
const trialBalance = ref<any[]>([])
const trialSummary = ref<any>({})
const journals = ref<any[]>([])
const generalLedger = ref<any[]>([])
const paymentLedger = ref<any[]>([])
const bankTransactions = ref<any[]>([])
const bankSummary = ref<any>({})
const reconciliationAllocations = ref<any[]>([])
const paymentCandidates = ref<any[]>([])
const orderCandidates = ref<any[]>([])
const search = ref('')
const accountCode = ref('')
const selectedBankTransaction = ref<any | null>(null)
const csvFile = ref<File | null>(null)
const importSummary = ref<any | null>(null)

const manualJournal = reactive({
  memo: '',
  postingDate: '',
  debitAccount: '',
  creditAccount: '',
  amount: '',
  remarks: '',
})

const bankForm = reactive({
  transactionDate: '',
  provider: 'bank_transfer',
  referenceNumber: '',
  transactionId: '',
  description: '',
  deposit: '',
  withdrawal: '',
  notes: '',
})

const csvImportForm = reactive({
  provider: 'mpesa',
  bankAccount: 'Cash and Bank',
  currency: 'KES',
})

const reconcileForm = reactive({
  candidateSearch: '',
  paymentReference: '',
  orderNumber: '',
  allocatedAmount: '',
  note: '',
})

const tabs = [
  { label: 'Trial Balance', value: 'trial-balance', icon: 'i-lucide-scale' },
  { label: 'Bank Reconciliation', value: 'bank-reconciliation', icon: 'i-lucide-landmark' },
  { label: 'Chart of Accounts', value: 'accounts', icon: 'i-lucide-list-tree' },
  { label: 'General Ledger', value: 'general-ledger', icon: 'i-lucide-book-open' },
  { label: 'Payment Ledger', value: 'payment-ledger', icon: 'i-lucide-receipt-text' },
  { label: 'Journal Entries', value: 'journals', icon: 'i-lucide-notebook-pen' },
]

const providerOptions = [
  { label: 'M-Pesa', value: 'mpesa' },
  { label: 'Pesapal', value: 'pesapal' },
  { label: 'Bank Transfer', value: 'bank_transfer' },
  { label: 'Cash on Delivery', value: 'cash_on_delivery' },
  { label: 'Card', value: 'card' },
]

const currencyOptions = [
  { label: 'KES', value: 'KES' },
  { label: 'USD', value: 'USD' },
]

const bankAccountOptions = computed(() => {
  const options = accounts.value
    .filter(account => ['asset', 'cash', 'bank'].includes(String(account.account_type || '').toLowerCase()) || /cash|bank/i.test(account.name || ''))
    .map(account => ({
      label: `${account.code} - ${account.name}`,
      value: account.name,
    }))
  return options.length ? options : [{ label: 'Cash and Bank', value: 'Cash and Bank' }]
})

function formatLabel(value: string) {
  return value ? value.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : '-'
}

function money(value: number | string | null | undefined) {
  return new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 2 }).format(Number(value || 0))
}

async function loadAccounting() {
  isLoading.value = true
  const [accountResult, tbResult, journalResult, glResult, paymentResult, bankResult, allocationResult] = await Promise.all([
    listAccounts({ q: search.value }),
    getTrialBalance(),
    listJournals({ q: search.value, page_size: 50 }),
    listGeneralLedger({ q: search.value, account_code: accountCode.value, page_size: 50 }),
    listPaymentLedger({ q: search.value, page_size: 50 }),
    listBankTransactions({ q: search.value, page_size: 50 }),
    listReconciliationAllocations({ q: search.value, page_size: 25 }),
  ])
  if (accountResult.success)
    accounts.value = accountResult.data?.results || []
  if (tbResult.success) {
    trialBalance.value = tbResult.data?.results || []
    trialSummary.value = tbResult.data?.summary || {}
  }
  if (journalResult.success)
    journals.value = journalResult.data?.results || []
  if (glResult.success)
    generalLedger.value = glResult.data?.results || []
  if (paymentResult.success)
    paymentLedger.value = paymentResult.data?.results || []
  if (bankResult.success) {
    bankTransactions.value = bankResult.data?.results || []
    bankSummary.value = bankResult.data?.summary || {}
  }
  if (allocationResult.success)
    reconciliationAllocations.value = allocationResult.data?.results || []
  const firstError = [accountResult, tbResult, journalResult, glResult, paymentResult, bankResult, allocationResult].find(result => !result.success)
  if (firstError)
    toast.add({ title: 'Could not load accounting', description: firstError.error || 'Please try again.', color: 'error' })
  isLoading.value = false
}

async function submitBankTransaction() {
  const deposit = Number(bankForm.deposit || 0)
  const withdrawal = Number(bankForm.withdrawal || 0)
  if (deposit <= 0 && withdrawal <= 0) {
    toast.add({ title: 'Amount needed', description: 'Enter a deposit for collections or withdrawal for money out.', color: 'warning' })
    return
  }
  const result = await createBankTransaction({
    transaction_date: bankForm.transactionDate || undefined,
    provider: bankForm.provider,
    reference_number: bankForm.referenceNumber,
    transaction_id: bankForm.transactionId,
    description: bankForm.description,
    deposit: deposit || undefined,
    withdrawal: withdrawal || undefined,
    currency: 'KES',
    notes: bankForm.notes,
  })
  if (result.success) {
    toast.add({ title: 'Bank row added', description: result.data?.bank_transaction?.reference_number || 'Ready for reconciliation.', color: 'success' })
    bankForm.referenceNumber = ''
    bankForm.transactionId = ''
    bankForm.description = ''
    bankForm.deposit = ''
    bankForm.withdrawal = ''
    bankForm.notes = ''
    await loadAccounting()
  }
  else {
    toast.add({ title: 'Could not add bank row', description: result.error || 'Please review the details.', color: 'error' })
  }
}

function handleCsvFile(event: Event) {
  const input = event.target as HTMLInputElement
  csvFile.value = input.files?.[0] || null
}

async function submitCsvImport() {
  if (!csvFile.value) {
    toast.add({ title: 'CSV file needed', description: 'Choose a bank, M-Pesa, or Pesapal statement CSV first.', color: 'warning' })
    return
  }
  const payload = new FormData()
  payload.append('file', csvFile.value)
  payload.append('provider', csvImportForm.provider)
  payload.append('bank_account', csvImportForm.bankAccount)
  payload.append('currency', csvImportForm.currency)
  isLoading.value = true
  const result = await importBankTransactionsCsv(payload)
  isLoading.value = false
  if (result.success) {
    importSummary.value = result.data
    const summary = result.data?.summary
    toast.add({
      title: 'CSV imported',
      description: `${summary?.created || 0} row(s) added, ${summary?.skipped || 0} skipped, ${summary?.errors || 0} error(s).`,
      color: summary?.errors ? 'warning' : 'success',
    })
    csvFile.value = null
    await loadAccounting()
  }
  else {
    toast.add({ title: 'Could not import CSV', description: result.error || 'Please check the file columns.', color: 'error' })
  }
}

async function loadCandidates() {
  const amount = selectedBankTransaction.value?.deposit || selectedBankTransaction.value?.amount || ''
  const result = await listReconciliationCandidates({ q: reconcileForm.candidateSearch, amount })
  if (result.success) {
    paymentCandidates.value = result.data?.payments || []
    orderCandidates.value = result.data?.orders || []
  }
  else {
    toast.add({ title: 'Could not load candidates', description: result.error || 'Please try again.', color: 'error' })
  }
}

async function selectBankTransaction(row: any) {
  selectedBankTransaction.value = row
  reconcileForm.allocatedAmount = String(row.deposit || row.amount || '')
  reconcileForm.paymentReference = row.matched_payment_reference || ''
  reconcileForm.orderNumber = row.matched_order_number || ''
  reconcileForm.candidateSearch = row.reference_number || row.transaction_id || ''
  await loadCandidates()
}

function pickPayment(payment: any) {
  reconcileForm.paymentReference = payment.reference
  reconcileForm.orderNumber = payment.order_number || reconcileForm.orderNumber
  reconcileForm.allocatedAmount = String(payment.amount || reconcileForm.allocatedAmount)
}

function pickOrder(order: any) {
  reconcileForm.orderNumber = order.number
  reconcileForm.allocatedAmount = String(order.total_incl_tax || reconcileForm.allocatedAmount)
}

async function submitReconciliation() {
  if (!selectedBankTransaction.value) {
    toast.add({ title: 'Select a bank row', description: 'Choose the statement transaction first.', color: 'warning' })
    return
  }
  const result = await reconcileBankTransaction(selectedBankTransaction.value.id, {
    payment_reference: reconcileForm.paymentReference,
    order_number: reconcileForm.orderNumber,
    allocated_amount: reconcileForm.allocatedAmount || undefined,
    note: reconcileForm.note,
  })
  if (result.success) {
    toast.add({ title: 'Reconciled', description: result.data?.allocation?.journal_reference || 'Bank row has been matched.', color: 'success' })
    selectedBankTransaction.value = null
    reconcileForm.paymentReference = ''
    reconcileForm.orderNumber = ''
    reconcileForm.allocatedAmount = ''
    reconcileForm.note = ''
    await loadAccounting()
  }
  else {
    toast.add({ title: 'Could not reconcile', description: result.error || 'Please check the selected rows.', color: 'error' })
  }
}

async function submitCancelBankTransaction(row: any) {
  const result = await cancelBankTransaction(row.id, { note: 'Cancelled from accounting reconciliation.' })
  if (result.success) {
    toast.add({ title: 'Bank row cancelled', description: row.reference_number || 'Cancelled.', color: 'success' })
    if (selectedBankTransaction.value?.id === row.id)
      selectedBankTransaction.value = null
    await loadAccounting()
  }
  else {
    toast.add({ title: 'Could not cancel bank row', description: result.error || 'Reconciled rows cannot be cancelled.', color: 'error' })
  }
}

async function submitManualJournal() {
  const amount = Number(manualJournal.amount || 0)
  if (!manualJournal.debitAccount || !manualJournal.creditAccount || amount <= 0) {
    toast.add({ title: 'Journal details needed', description: 'Select debit account, credit account, and amount.', color: 'warning' })
    return
  }
  isLoading.value = true
  const result = await createJournal({
    posting_date: manualJournal.postingDate || undefined,
    memo: manualJournal.memo || 'Manual journal entry',
    currency: 'KES',
    lines: [
      { account_code: manualJournal.debitAccount, debit: amount, remarks: manualJournal.remarks },
      { account_code: manualJournal.creditAccount, credit: amount, remarks: manualJournal.remarks },
    ],
  })
  isLoading.value = false
  if (result.success) {
    toast.add({ title: 'Journal posted', description: result.data?.journal_entry?.reference || 'Entry submitted.', color: 'success' })
    manualJournal.memo = ''
    manualJournal.debitAccount = ''
    manualJournal.creditAccount = ''
    manualJournal.amount = ''
    manualJournal.remarks = ''
    await loadAccounting()
  }
  else {
    toast.add({ title: 'Could not post journal', description: result.error || 'Please review the journal lines.', color: 'error' })
  }
}

onMounted(loadAccounting)
</script>

<template>
  <div class="min-h-screen bg-default p-8">
    <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black">Accounting</h1>
        <p class="mt-1 text-sm text-toned">Reesolmart accounting workspace for chart of accounts, journals, GL, payment ledger, and trial balance.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <UInput v-model="search" icon="i-lucide-search" placeholder="Search accounting..." @keyup.enter="loadAccounting" />
        <UInput v-model="accountCode" class="w-36" placeholder="Account code" @keyup.enter="loadAccounting" />
        <UButton :loading="isLoading" @click="loadAccounting">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 flex flex-wrap gap-2">
      <UButton
        v-for="tab in tabs"
        :key="tab.value"
        :color="activeTab === tab.value ? 'primary' : 'neutral'"
        :variant="activeTab === tab.value ? 'solid' : 'outline'"
        @click="activeTab = tab.value"
      >
        <UIcon :name="tab.icon" />
        {{ tab.label }}
      </UButton>
    </div>

    <div v-if="activeTab === 'bank-reconciliation'" class="space-y-4">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <UCard><p class="text-xs uppercase text-toned">Statement deposits</p><p class="mt-2 text-xl font-black">{{ money(bankSummary.deposit) }}</p></UCard>
        <UCard><p class="text-xs uppercase text-toned">Statement withdrawals</p><p class="mt-2 text-xl font-black">{{ money(bankSummary.withdrawal) }}</p></UCard>
        <UCard><p class="text-xs uppercase text-toned">Unreconciled rows</p><p class="mt-2 text-xl font-black">{{ bankSummary.unreconciled || 0 }}</p></UCard>
      </div>

      <UCard>
        <template #header><h3 class="font-semibold">Add Statement Row</h3></template>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <UInput v-model="bankForm.transactionDate" type="date" />
          <USelect v-model="bankForm.provider" :items="providerOptions" />
          <UInput v-model="bankForm.referenceNumber" placeholder="Reference" />
          <UInput v-model="bankForm.description" placeholder="Description" />
          <UInput v-model="bankForm.deposit" type="number" min="0" step="0.01" placeholder="Deposit" />
          <UButton :loading="isLoading" @click="submitBankTransaction">
            <UIcon name="i-lucide-plus" />
            Add row
          </UButton>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-semibold">Import Statement CSV</h3>
            <UBadge color="info" variant="soft">CSV</UBadge>
          </div>
        </template>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <USelect v-model="csvImportForm.provider" :items="providerOptions" />
          <USelectMenu v-model="csvImportForm.bankAccount" :items="bankAccountOptions" value-key="value" searchable placeholder="Bank account" />
          <USelect v-model="csvImportForm.currency" :items="currencyOptions" />
          <input class="rounded-md border border-default bg-default px-3 py-2 text-sm" type="file" accept=".csv,text/csv" @change="handleCsvFile">
          <UButton :loading="isLoading" @click="submitCsvImport">
            <UIcon name="i-lucide-upload" />
            Import CSV
          </UButton>
        </div>
        <p class="mt-3 text-xs text-toned">
          Accepted columns include Date, Reference, Description, Deposit, Withdrawal, Amount, Currency.
        </p>
        <div v-if="importSummary" class="mt-3 grid grid-cols-1 gap-2 text-sm md:grid-cols-3">
          <div class="rounded-lg border border-default p-3">Created: <strong>{{ importSummary.summary?.created || 0 }}</strong></div>
          <div class="rounded-lg border border-default p-3">Skipped: <strong>{{ importSummary.summary?.skipped || 0 }}</strong></div>
          <div class="rounded-lg border border-default p-3">Errors: <strong>{{ importSummary.summary?.errors || 0 }}</strong></div>
        </div>
      </UCard>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold">Unreconciled Statement Rows</h3>
              <UBadge color="warning" variant="soft">{{ bankSummary.unreconciled || 0 }} open</UBadge>
            </div>
          </template>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-default text-sm">
              <thead><tr><th class="px-4 py-3 text-left">Date</th><th class="px-4 py-3 text-left">Reference</th><th class="px-4 py-3 text-right">Deposit</th><th class="px-4 py-3 text-left">Status</th><th class="px-4 py-3 text-right">Action</th></tr></thead>
              <tbody class="divide-y divide-default">
                <tr v-for="row in bankTransactions" :key="row.id" :class="selectedBankTransaction?.id === row.id ? 'bg-primary/10' : ''">
                  <td class="px-4 py-3">{{ row.transaction_date }}</td>
                  <td class="px-4 py-3">
                    <p class="font-semibold">{{ row.reference_number || row.transaction_id || `Row ${row.id}` }}</p>
                    <p class="text-xs text-toned">{{ row.description || row.provider }}</p>
                  </td>
                  <td class="px-4 py-3 text-right">{{ money(row.deposit) }}</td>
                  <td class="px-4 py-3">{{ formatLabel(row.status) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex justify-end gap-2">
                      <UButton size="xs" variant="outline" :disabled="row.status !== 'unreconciled'" @click="selectBankTransaction(row)">Match</UButton>
                      <UButton size="xs" color="error" variant="outline" :disabled="row.status !== 'unreconciled'" @click="submitCancelBankTransaction(row)">Cancel</UButton>
                    </div>
                  </td>
                </tr>
                <tr v-if="!bankTransactions.length"><td colspan="5" class="px-4 py-8 text-center text-toned">No statement rows yet.</td></tr>
              </tbody>
            </table>
          </div>
        </UCard>

        <UCard>
          <template #header><h3 class="font-semibold">Match Selected Row</h3></template>
          <div v-if="selectedBankTransaction" class="space-y-4">
            <div class="rounded-lg border border-default p-3 text-sm">
              <p class="font-semibold">{{ selectedBankTransaction.reference_number || selectedBankTransaction.transaction_id }}</p>
              <p class="text-toned">{{ selectedBankTransaction.description || 'No description' }}</p>
              <p class="mt-1">{{ money(selectedBankTransaction.deposit) }} {{ selectedBankTransaction.currency }}</p>
            </div>
            <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <UInput v-model="reconcileForm.candidateSearch" icon="i-lucide-search" placeholder="Search payment, order, customer" @keyup.enter="loadCandidates" />
              <UButton variant="outline" @click="loadCandidates">
                <UIcon name="i-lucide-search" />
                Find candidates
              </UButton>
              <UInput v-model="reconcileForm.paymentReference" placeholder="Payment reference" />
              <UInput v-model="reconcileForm.orderNumber" placeholder="Order number" />
              <UInput v-model="reconcileForm.allocatedAmount" type="number" min="0" step="0.01" placeholder="Allocated amount" />
              <UInput v-model="reconcileForm.note" placeholder="Review note" />
            </div>
            <UButton block @click="submitReconciliation">
              <UIcon name="i-lucide-check-check" />
              Reconcile selected row
            </UButton>
          </div>
          <div v-else class="rounded-lg border border-dashed border-default p-6 text-center text-sm text-toned">
            Select an unreconciled statement row to start matching.
          </div>
        </UCard>
      </div>

      <div v-if="selectedBankTransaction" class="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <UCard>
          <template #header><h3 class="font-semibold">Payment Candidates</h3></template>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-default text-sm">
              <thead><tr><th class="px-4 py-3 text-left">Reference</th><th class="px-4 py-3 text-left">Customer</th><th class="px-4 py-3 text-right">Amount</th><th class="px-4 py-3 text-right">Action</th></tr></thead>
              <tbody class="divide-y divide-default">
                <tr v-for="payment in paymentCandidates" :key="payment.id">
                  <td class="px-4 py-3"><p class="font-semibold">{{ payment.reference }}</p><p class="text-xs text-toned">{{ formatLabel(payment.status) }} - {{ payment.order_number || 'No order' }}</p></td>
                  <td class="px-4 py-3">{{ payment.payer_email || payment.payer_phone || '-' }}</td>
                  <td class="px-4 py-3 text-right">{{ money(payment.amount) }}</td>
                  <td class="px-4 py-3 text-right"><UButton size="xs" variant="outline" @click="pickPayment(payment)">Use</UButton></td>
                </tr>
                <tr v-if="!paymentCandidates.length"><td colspan="4" class="px-4 py-8 text-center text-toned">No payment candidates found.</td></tr>
              </tbody>
            </table>
          </div>
        </UCard>

        <UCard>
          <template #header><h3 class="font-semibold">Order Candidates</h3></template>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-default text-sm">
              <thead><tr><th class="px-4 py-3 text-left">Order</th><th class="px-4 py-3 text-left">Customer</th><th class="px-4 py-3 text-right">Total</th><th class="px-4 py-3 text-right">Action</th></tr></thead>
              <tbody class="divide-y divide-default">
                <tr v-for="order in orderCandidates" :key="order.id">
                  <td class="px-4 py-3"><p class="font-semibold">{{ order.number }}</p><p class="text-xs text-toned">{{ formatLabel(order.status) }}</p></td>
                  <td class="px-4 py-3">{{ order.email || '-' }}</td>
                  <td class="px-4 py-3 text-right">{{ money(order.total_incl_tax) }}</td>
                  <td class="px-4 py-3 text-right"><UButton size="xs" variant="outline" @click="pickOrder(order)">Use</UButton></td>
                </tr>
                <tr v-if="!orderCandidates.length"><td colspan="4" class="px-4 py-8 text-center text-toned">No order candidates found.</td></tr>
              </tbody>
            </table>
          </div>
        </UCard>
      </div>

      <UCard>
        <template #header><h3 class="font-semibold">Recent Allocations</h3></template>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead><tr><th class="px-4 py-3 text-left">Bank Row</th><th class="px-4 py-3 text-left">Payment</th><th class="px-4 py-3 text-left">Order</th><th class="px-4 py-3 text-left">Journal</th><th class="px-4 py-3 text-right">Amount</th><th class="px-4 py-3 text-left">By</th></tr></thead>
            <tbody class="divide-y divide-default">
              <tr v-for="row in reconciliationAllocations" :key="row.id">
                <td class="px-4 py-3">{{ row.bank_transaction_id || '-' }}</td>
                <td class="px-4 py-3">{{ row.payment_reference || '-' }}</td>
                <td class="px-4 py-3">{{ row.order_number || '-' }}</td>
                <td class="px-4 py-3">{{ row.journal_reference || '-' }}</td>
                <td class="px-4 py-3 text-right">{{ money(row.allocated_amount) }}</td>
                <td class="px-4 py-3">{{ row.reconciled_by_email || '-' }}</td>
              </tr>
              <tr v-if="!reconciliationAllocations.length"><td colspan="6" class="px-4 py-8 text-center text-toned">No allocations yet.</td></tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>

    <div v-if="activeTab === 'trial-balance'" class="space-y-4">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <UCard><p class="text-xs uppercase text-toned">Debit</p><p class="mt-2 text-xl font-black">{{ money(trialSummary.debit) }}</p></UCard>
        <UCard><p class="text-xs uppercase text-toned">Credit</p><p class="mt-2 text-xl font-black">{{ money(trialSummary.credit) }}</p></UCard>
        <UCard><p class="text-xs uppercase text-toned">Difference</p><p class="mt-2 text-xl font-black">{{ money(trialSummary.balance) }}</p></UCard>
      </div>
      <UCard>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead><tr><th class="px-4 py-3 text-left">Account</th><th class="px-4 py-3 text-left">Type</th><th class="px-4 py-3 text-right">Debit</th><th class="px-4 py-3 text-right">Credit</th><th class="px-4 py-3 text-right">Balance</th></tr></thead>
            <tbody class="divide-y divide-default">
              <tr v-for="row in trialBalance" :key="row.code">
                <td class="px-4 py-3 font-semibold">{{ row.code }} - {{ row.name }}</td>
                <td class="px-4 py-3">{{ formatLabel(row.account_type) }}</td>
                <td class="px-4 py-3 text-right">{{ money(row.debit) }}</td>
                <td class="px-4 py-3 text-right">{{ money(row.credit) }}</td>
                <td class="px-4 py-3 text-right">{{ money(row.balance) }}</td>
              </tr>
              <tr v-if="!trialBalance.length"><td colspan="5" class="px-4 py-8 text-center text-toned">No trial balance rows yet.</td></tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>

    <UCard v-if="activeTab === 'accounts'">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-default text-sm">
          <thead><tr><th class="px-4 py-3 text-left">Code</th><th class="px-4 py-3 text-left">Name</th><th class="px-4 py-3 text-left">Type</th><th class="px-4 py-3 text-left">Currency</th><th class="px-4 py-3 text-left">Status</th></tr></thead>
          <tbody class="divide-y divide-default">
            <tr v-for="account in accounts" :key="account.id">
              <td class="px-4 py-3 font-semibold">{{ account.code }}</td>
              <td class="px-4 py-3">{{ account.name }}</td>
              <td class="px-4 py-3">{{ formatLabel(account.account_type) }}</td>
              <td class="px-4 py-3">{{ account.currency }}</td>
              <td class="px-4 py-3">{{ account.is_active ? 'Active' : 'Inactive' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <UCard v-if="activeTab === 'general-ledger'">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-default text-sm">
          <thead><tr><th class="px-4 py-3 text-left">Date</th><th class="px-4 py-3 text-left">Journal</th><th class="px-4 py-3 text-left">Account</th><th class="px-4 py-3 text-right">Debit</th><th class="px-4 py-3 text-right">Credit</th><th class="px-4 py-3 text-left">Remarks</th></tr></thead>
          <tbody class="divide-y divide-default">
            <tr v-for="line in generalLedger" :key="line.id">
              <td class="px-4 py-3">{{ line.posting_date }}</td>
              <td class="px-4 py-3 font-semibold">{{ line.journal_reference }}</td>
              <td class="px-4 py-3">{{ line.account_code }} - {{ line.account_name }}</td>
              <td class="px-4 py-3 text-right">{{ money(line.debit) }}</td>
              <td class="px-4 py-3 text-right">{{ money(line.credit) }}</td>
              <td class="px-4 py-3">{{ line.remarks || line.memo }}</td>
            </tr>
            <tr v-if="!generalLedger.length"><td colspan="6" class="px-4 py-8 text-center text-toned">No GL entries yet.</td></tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <UCard v-if="activeTab === 'payment-ledger'">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-default text-sm">
          <thead><tr><th class="px-4 py-3 text-left">Date</th><th class="px-4 py-3 text-left">Type</th><th class="px-4 py-3 text-left">Party</th><th class="px-4 py-3 text-left">Voucher</th><th class="px-4 py-3 text-left">Against</th><th class="px-4 py-3 text-right">Amount</th></tr></thead>
          <tbody class="divide-y divide-default">
            <tr v-for="row in paymentLedger" :key="row.id">
              <td class="px-4 py-3">{{ row.posting_date }}</td>
              <td class="px-4 py-3">{{ formatLabel(row.account_type) }}</td>
              <td class="px-4 py-3">{{ row.party_name || row.party_id }}</td>
              <td class="px-4 py-3">{{ row.voucher_type }} {{ row.voucher_no }}</td>
              <td class="px-4 py-3">{{ row.against_voucher_no || '-' }}</td>
              <td class="px-4 py-3 text-right">{{ money(row.amount) }}</td>
            </tr>
            <tr v-if="!paymentLedger.length"><td colspan="6" class="px-4 py-8 text-center text-toned">No payment ledger entries yet.</td></tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <div v-if="activeTab === 'journals'" class="space-y-4">
      <UCard>
        <template #header><h3 class="font-semibold">Manual Journal Entry</h3></template>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <UInput v-model="manualJournal.postingDate" type="date" />
          <UInput v-model="manualJournal.debitAccount" placeholder="Debit account code" />
          <UInput v-model="manualJournal.creditAccount" placeholder="Credit account code" />
          <UInput v-model="manualJournal.amount" type="number" min="0" step="0.01" placeholder="Amount" />
          <UInput v-model="manualJournal.memo" placeholder="Memo" />
          <UButton :loading="isLoading" @click="submitManualJournal">
            <UIcon name="i-lucide-notebook-pen" />
            Post journal
          </UButton>
        </div>
      </UCard>
      <UCard>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-default text-sm">
            <thead><tr><th class="px-4 py-3 text-left">Date</th><th class="px-4 py-3 text-left">Reference</th><th class="px-4 py-3 text-left">Type</th><th class="px-4 py-3 text-left">Status</th><th class="px-4 py-3 text-right">Debit</th><th class="px-4 py-3 text-right">Credit</th><th class="px-4 py-3 text-left">Memo</th></tr></thead>
            <tbody class="divide-y divide-default">
              <tr v-for="entry in journals" :key="entry.id">
                <td class="px-4 py-3">{{ entry.posting_date }}</td>
                <td class="px-4 py-3 font-semibold">{{ entry.reference }}</td>
                <td class="px-4 py-3">{{ formatLabel(entry.entry_type) }}</td>
                <td class="px-4 py-3">{{ formatLabel(entry.status) }}</td>
                <td class="px-4 py-3 text-right">{{ money(entry.total_debit) }}</td>
                <td class="px-4 py-3 text-right">{{ money(entry.total_credit) }}</td>
                <td class="px-4 py-3">{{ entry.memo }}</td>
              </tr>
              <tr v-if="!journals.length"><td colspan="7" class="px-4 py-8 text-center text-toned">No journal entries yet.</td></tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>
  </div>
</template>
