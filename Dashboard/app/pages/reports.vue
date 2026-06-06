<script setup lang="ts">
import type { ReportDefinition, ReportDetail } from '~/composables/useReports'

const toast = useToast()
const { getReport, getReports } = useReports()

const reports = ref<ReportDefinition[]>([])
const selectedReportCode = ref('orders')
const reportDetail = ref<ReportDetail | null>(null)
const searchQuery = ref('')
const page = ref(1)
const pageSize = ref(25)
const isLoading = ref(false)

const pageSizeOptions = [
  { label: '25 rows', value: 25 },
  { label: '50 rows', value: 50 },
  { label: '100 rows', value: 100 },
  { label: '200 rows', value: 200 },
]

const selectedReport = computed(() => reports.value.find(report => report.code === selectedReportCode.value) || null)

const columnsByReport: Record<string, Array<{ key: string, label: string, type?: string }>> = {
  orders: [
    { key: 'number', label: 'Order' },
    { key: 'status', label: 'Status' },
    { key: 'customer', label: 'Customer' },
    { key: 'total_incl_tax', label: 'Total', type: 'money' },
    { key: 'date_placed', label: 'Placed', type: 'date' },
  ],
  products: [
    { key: 'title', label: 'Product' },
    { key: 'upc', label: 'UPC' },
    { key: 'category', label: 'Category' },
    { key: 'stock', label: 'Stock', type: 'number' },
    { key: 'is_public', label: 'Public', type: 'boolean' },
    { key: 'date_updated', label: 'Updated', type: 'date' },
  ],
  customers: [
    { key: 'email', label: 'Email' },
    { key: 'username', label: 'Username' },
    { key: 'first_name', label: 'First name' },
    { key: 'last_name', label: 'Last name' },
    { key: 'is_staff', label: 'Staff', type: 'boolean' },
    { key: 'is_active', label: 'Active', type: 'boolean' },
    { key: 'date_joined', label: 'Joined', type: 'date' },
  ],
  vouchers: [
    { key: 'name', label: 'Voucher' },
    { key: 'code', label: 'Code' },
    { key: 'usage', label: 'Usage' },
    { key: 'num_orders', label: 'Orders', type: 'number' },
    { key: 'total_discount', label: 'Discount', type: 'money' },
    { key: 'start_datetime', label: 'Starts', type: 'date' },
    { key: 'end_datetime', label: 'Ends', type: 'date' },
  ],
}

const activeColumns = computed(() => columnsByReport[selectedReportCode.value] || inferColumns.value)

const inferColumns = computed(() => {
  const first = reportDetail.value?.results?.[0]
  if (!first)
    return []
  return Object.keys(first)
    .filter(key => typeof first[key] !== 'object')
    .slice(0, 8)
    .map(key => ({ key, label: key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) }))
})

const filteredRows = computed(() => {
  const rows = reportDetail.value?.results || []
  const search = searchQuery.value.trim().toLowerCase()
  if (!search)
    return rows
  return rows.filter(row => JSON.stringify(row).toLowerCase().includes(search))
})

const summaryCards = computed(() => {
  const summary = reportDetail.value?.summary || {}
  return Object.entries(summary)
    .filter(([, value]) => !Array.isArray(value) && value !== null && typeof value !== 'object')
    .map(([key, value]) => ({
      key,
      label: key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()),
      value,
      icon: summaryIcon(key),
      color: summaryColor(key),
    }))
})

const byStatus = computed(() => reportDetail.value?.summary?.by_status || [])

function summaryIcon(key: string) {
  if (key.includes('revenue') || key.includes('discount'))
    return 'i-lucide-banknote'
  if (key.includes('stock'))
    return 'i-lucide-boxes'
  if (key.includes('active') || key.includes('public'))
    return 'i-lucide-circle-check'
  if (key.includes('staff') || key.includes('customer'))
    return 'i-lucide-users'
  return 'i-lucide-chart-column'
}

function summaryColor(key: string) {
  if (key.includes('revenue') || key.includes('discount'))
    return '#059669'
  if (key.includes('draft') || key.includes('staff'))
    return '#f59e0b'
  if (key.includes('active') || key.includes('public'))
    return '#2563eb'
  return '#7c3aed'
}

function formatCell(row: any, column: { key: string, type?: string }) {
  const value = row[column.key]
  if (value === null || value === undefined || value === '')
    return 'Not recorded'
  if (column.type === 'money')
    return new Intl.NumberFormat('en', { style: 'currency', currency: row.currency || 'KES' }).format(Number(value || 0))
  if (column.type === 'date')
    return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  if (column.type === 'boolean')
    return value ? 'Yes' : 'No'
  if (column.type === 'number')
    return Number(value || 0).toLocaleString('en')
  return String(value)
}

function formatSummaryValue(value: any) {
  if (typeof value === 'number')
    return Number(value).toLocaleString('en', { maximumFractionDigits: 2 })
  return String(value)
}

async function loadReportList() {
  const result = await getReports()
  if (result.success && result.data?.length) {
    reports.value = result.data
    if (!reports.value.some(report => report.code === selectedReportCode.value))
      selectedReportCode.value = reports.value[0].code
  }
  else if (!result.success) {
    toast.add({ title: 'Could not load reports', description: result.error || 'Please try again.', color: 'error' })
  }
}

async function loadReport() {
  if (!selectedReportCode.value)
    return

  isLoading.value = true
  const result = await getReport(selectedReportCode.value, { page: page.value, pageSize: pageSize.value })
  if (result.success && result.data) {
    reportDetail.value = result.data
  }
  else {
    reportDetail.value = null
    toast.add({ title: 'Could not load report', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

function selectReport(code: string) {
  selectedReportCode.value = code
  page.value = 1
  searchQuery.value = ''
  loadReport()
}

function csvEscape(value: any) {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function exportCsv() {
  const rows = filteredRows.value
  if (!rows.length) {
    toast.add({ title: 'No rows to export', color: 'warning' })
    return
  }

  const headers = activeColumns.value.map(column => column.label)
  const body = rows.map(row => activeColumns.value.map(column => csvEscape(formatCell(row, column))).join(','))
  const csv = [headers.map(csvEscape).join(','), ...body].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedReportCode.value}-report.csv`
  link.click()
  URL.revokeObjectURL(url)
}

watch(pageSize, () => {
  page.value = 1
  loadReport()
})

watch(page, loadReport)

onMounted(async () => {
  await loadReportList()
  await loadReport()
})
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Reports</h1>
        <p class="mt-1 text-sm text-slate-500">View operational reports for orders, products, customers, and vouchers.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search loaded rows..."
        />
        <USelect v-model="pageSize" :items="pageSizeOptions" class="w-32" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadReport">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="exportCsv">
          <UIcon name="i-lucide-download" />
          Export
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      <button
        v-for="report in reports"
        :key="report.code"
        type="button"
        class="rounded-lg border bg-white p-4 text-left transition hover:border-blue-300 hover:bg-blue-50/40"
        :class="selectedReportCode === report.code ? 'border-blue-500 ring-2 ring-blue-100' : 'border-slate-200'"
        @click="selectReport(report.code)"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate font-black text-slate-950">{{ report.name }}</p>
            <p class="mt-1 line-clamp-2 text-sm text-slate-500">{{ report.description }}</p>
          </div>
          <UIcon name="i-lucide-file-chart-column" class="mt-1 shrink-0 text-slate-400" />
        </div>
      </button>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2
        v-for="card in summaryCards"
        :key="card.key"
        :name="card.label"
        :value="formatSummaryValue(card.value)"
        :budget="formatSummaryValue(card.value)"
        :color="card.color"
        :icon="card.icon"
        :loading="isLoading"
      />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-4">
        <div class="flex flex-col gap-2 border-b border-slate-200 bg-slate-50 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 class="font-black text-slate-950">{{ selectedReport?.name || 'Report' }}</h2>
            <p class="text-sm text-slate-500">Showing {{ filteredRows.length }} loaded rows of {{ reportDetail?.pagination?.total || 0 }} total.</p>
          </div>
          <UBadge color="neutral" variant="soft">Page {{ reportDetail?.pagination?.page || page }} of {{ reportDetail?.pagination?.num_pages || 1 }}</UBadge>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-white">
              <tr>
                <th v-for="column in activeColumns" :key="column.key" class="whitespace-nowrap px-4 py-3 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                  {{ column.label }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-if="isLoading">
                <td :colspan="activeColumns.length || 1" class="px-4 py-12 text-center text-sm font-semibold text-slate-500">
                  <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
                  Loading report
                </td>
              </tr>
              <tr v-else-if="filteredRows.length === 0">
                <td :colspan="activeColumns.length || 1" class="px-4 py-12 text-center text-sm text-slate-500">No rows found.</td>
              </tr>
              <tr v-for="row in filteredRows" v-else :key="`${selectedReportCode}-${row.id || JSON.stringify(row)}`" class="hover:bg-slate-50">
                <td v-for="column in activeColumns" :key="column.key" class="max-w-xs truncate px-4 py-3 text-slate-700">
                  {{ formatCell(row, column) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
          <UButton color="neutral" variant="outline" :disabled="page <= 1 || isLoading" @click="page -= 1">
            <UIcon name="i-lucide-chevron-left" />
            Previous
          </UButton>
          <span class="text-sm text-slate-500">Page {{ page }}</span>
          <UButton color="neutral" variant="outline" :disabled="!reportDetail?.pagination?.has_next || isLoading" @click="page += 1">
            Next
            <UIcon name="i-lucide-chevron-right" />
          </UButton>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Breakdown</h2>
          <p class="mt-1 text-sm text-slate-500">Additional summary data returned by the report.</p>
        </div>
        <div v-if="byStatus.length === 0" class="p-6 text-sm text-slate-500">No breakdown available.</div>
        <div v-else class="divide-y divide-slate-100">
          <div v-for="item in byStatus" :key="item.status || 'blank'" class="flex items-center justify-between gap-3 px-4 py-3">
            <span class="min-w-0 truncate text-sm font-semibold text-slate-700">{{ item.status || 'No status' }}</span>
            <UBadge color="neutral" variant="soft">{{ item.count }}</UBadge>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
