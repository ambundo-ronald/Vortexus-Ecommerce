<script setup lang="ts">
import type { AdminPaymentLogItem } from '~/composables/usePaymentConfig'

const toast = useToast()
const { getPaymentLogs } = usePaymentConfig()

const logs = ref<AdminPaymentLogItem[]>([])
const selectedLog = ref<AdminPaymentLogItem | null>(null)
const summary = ref<any>({})
const page = ref(1)
const pageSize = ref(50)
const totalItems = ref(0)
const numPages = ref(1)
const isLoading = ref(false)
const detailOpen = ref(false)

const filters = reactive({
  search: '',
  method: '',
  status: '',
})

const methodOptions = [
  { label: 'All methods', value: '' },
  { label: 'Pesapal', value: 'pesapal' },
  { label: 'M-Pesa', value: 'mpesa' },
  { label: 'Airtel Money', value: 'airtel_money' },
  { label: 'Credit Card', value: 'credit_card' },
  { label: 'Debit Card', value: 'debit_card' },
  { label: 'Bank Transfer', value: 'bank_transfer' },
  { label: 'Cash on Delivery', value: 'cash_on_delivery' },
]

const statusOptions = [
  { label: 'All statuses', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Paid', value: 'paid' },
  { label: 'Authorized', value: 'authorized' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
]

const pageSizeOptions = [
  { label: '25 rows', value: 25 },
  { label: '50 rows', value: 50 },
  { label: '100 rows', value: 100 },
]

function formatLabel(value: string) {
  return value ? value.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatMoney(amount: number, currency: string) {
  return new Intl.NumberFormat('en', { style: 'currency', currency: currency || 'KES' }).format(Number(amount || 0))
}

function statusColor(status: string) {
  if (status === 'paid' || status === 'authorized')
    return 'success'
  if (status === 'failed' || status === 'cancelled')
    return 'error'
  return 'warning'
}

function countForStatus(status: string) {
  return summary.value?.by_status?.find((item: any) => item.status === status)?.count || 0
}

function payloadPreview(payload: Record<string, any> | null | undefined) {
  if (!payload || Object.keys(payload).length === 0)
    return 'No provider payload'
  return JSON.stringify(payload, null, 2)
}

async function loadLogs() {
  isLoading.value = true
  const result = await getPaymentLogs({
    page: page.value,
    pageSize: pageSize.value,
    search: filters.search.trim(),
    method: filters.method,
    status: filters.status,
  })

  if (result.success) {
    logs.value = result.data?.results ?? []
    summary.value = result.data?.summary ?? {}
    totalItems.value = result.data?.pagination?.count ?? logs.value.length
    numPages.value = result.data?.pagination?.num_pages ?? 1
  }
  else {
    logs.value = []
    totalItems.value = 0
    toast.add({ title: 'Could not load payment logs', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

function openDetail(log: AdminPaymentLogItem) {
  selectedLog.value = log
  detailOpen.value = true
}

function applyFilters() {
  page.value = 1
  loadLogs()
}

function resetFilters() {
  filters.search = ''
  filters.method = ''
  filters.status = ''
  page.value = 1
  loadLogs()
}

watch(page, loadLogs)
watch(pageSize, () => {
  page.value = 1
  loadLogs()
})

onMounted(loadLogs)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Payment Logs</h1>
        <p class="mt-1 text-sm text-slate-500">Review checkout payment sessions, statuses, gateway references, and provider responses.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput v-model="filters.search" class="min-w-56 flex-1 lg:max-w-sm" icon="i-lucide-search" placeholder="Reference, order, email, phone..." @keyup.enter="applyFilters" />
        <USelect v-model="pageSize" :items="pageSizeOptions" class="w-32" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadLogs">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <CardsKpiCard2 name="Total payments" :value="summary.total || 0" :budget="summary.total || 1" color="#3d7cff" icon="i-lucide-credit-card" :loading="isLoading" />
      <CardsKpiCard2 name="Paid" :value="countForStatus('paid')" :budget="summary.total || 1" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Authorized" :value="countForStatus('authorized')" :budget="summary.total || 1" color="#0f766e" icon="i-lucide-shield-check" :loading="isLoading" />
      <CardsKpiCard2 name="Pending" :value="countForStatus('pending')" :budget="summary.total || 1" color="#b45309" icon="i-lucide-clock" :loading="isLoading" />
      <CardsKpiCard2 name="Failed" :value="countForStatus('failed')" :budget="summary.total || 1" color="#dc2626" icon="i-lucide-circle-x" :loading="isLoading" />
    </div>

    <div class="mb-6 rounded-lg border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <UFormField label="Method"><USelect v-model="filters.method" :items="methodOptions" /></UFormField>
        <UFormField label="Status"><USelect v-model="filters.status" :items="statusOptions" /></UFormField>
        <UFormField label="Search"><UInput v-model="filters.search" placeholder="PAY-..., order number, email" @keyup.enter="applyFilters" /></UFormField>
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <UButton color="neutral" variant="outline" @click="resetFilters">
          <UIcon name="i-lucide-rotate-ccw" />
          Reset
        </UButton>
        <UButton color="primary" :loading="isLoading" @click="applyFilters">
          <UIcon name="i-lucide-filter" />
          Apply Filters
        </UButton>
      </div>
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Payment</div>
        <div class="col-span-2">Customer</div>
        <div class="col-span-2">Gateway</div>
        <div class="col-span-2">Amount</div>
        <div class="col-span-2">Created</div>
        <div class="col-span-1 text-right">Action</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading payment logs
      </div>

      <div v-else-if="logs.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-credit-card" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No payment logs found</h2>
        <p class="mt-1 text-sm text-slate-500">Try broadening the filters.</p>
      </div>

      <div v-for="log in logs" v-else :key="log.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50">
        <div class="col-span-3 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <UBadge :color="statusColor(log.status)" variant="soft">{{ formatLabel(log.status) }}</UBadge>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ log.reference }}</p>
              <p class="truncate text-xs text-slate-500">{{ formatLabel(log.method) }} · {{ log.order_number || 'No order yet' }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.payer_email || 'No email' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.payer_phone || 'No phone' }}</p>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.provider }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.external_reference || 'No external reference' }}</p>
        </div>
        <div class="col-span-2 text-sm font-semibold text-slate-700">{{ formatMoney(log.amount, log.currency) }}</div>
        <div class="col-span-2 text-sm text-slate-700">{{ formatDate(log.created_at) }}</div>
        <div class="col-span-1 text-right">
          <UTooltip text="View detail">
            <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openDetail(log)" />
          </UTooltip>
        </div>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-between text-sm text-slate-500">
      <span>{{ totalItems }} payment{{ totalItems === 1 ? '' : 's' }} found</span>
      <div class="flex items-center gap-2">
        <UButton color="neutral" variant="outline" size="sm" :disabled="page <= 1" @click="page -= 1">Previous</UButton>
        <span>Page {{ page }} of {{ numPages }}</span>
        <UButton color="neutral" variant="outline" size="sm" :disabled="page >= numPages" @click="page += 1">Next</UButton>
      </div>
    </div>

    <USlideover v-model:open="detailOpen">
      <template #content>
        <div class="flex h-full flex-col">
          <div class="border-b border-slate-200 p-5">
            <h2 class="text-lg font-black text-slate-950">Payment Detail</h2>
            <p class="mt-1 text-sm text-slate-500">{{ selectedLog?.reference }}</p>
          </div>
          <div class="flex-1 space-y-5 overflow-y-auto p-5">
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div><span class="text-slate-500">Status</span><p class="font-semibold text-slate-950">{{ formatLabel(selectedLog?.status || '') }}</p></div>
              <div><span class="text-slate-500">Method</span><p class="font-semibold text-slate-950">{{ formatLabel(selectedLog?.method || '') }}</p></div>
              <div><span class="text-slate-500">Amount</span><p class="font-semibold text-slate-950">{{ formatMoney(selectedLog?.amount || 0, selectedLog?.currency || 'KES') }}</p></div>
              <div><span class="text-slate-500">Order</span><p class="font-semibold text-slate-950">{{ selectedLog?.order_number || 'No order yet' }}</p></div>
              <div><span class="text-slate-500">External reference</span><p class="break-all font-semibold text-slate-950">{{ selectedLog?.external_reference || 'None' }}</p></div>
              <div><span class="text-slate-500">Paid at</span><p class="font-semibold text-slate-950">{{ formatDate(selectedLog?.paid_at) }}</p></div>
            </div>
            <div>
              <h3 class="mb-2 text-sm font-bold text-slate-950">Provider payload</h3>
              <pre class="max-h-72 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{{ payloadPreview(selectedLog?.provider_payload) }}</pre>
            </div>
            <div>
              <h3 class="mb-2 text-sm font-bold text-slate-950">Metadata</h3>
              <pre class="max-h-72 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{{ payloadPreview(selectedLog?.metadata) }}</pre>
            </div>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
