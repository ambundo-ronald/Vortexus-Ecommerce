<script setup lang="ts">
import type { StockAlertItem } from '~/composables/useStockAlerts'

const ALL_STATUSES = '__all_statuses__'

const toast = useToast()
const { getStockAlerts, updateStockAlert } = useStockAlerts()

const alerts = ref<StockAlertItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const statusFilter = ref(ALL_STATUSES)
const selectedAlert = ref<StockAlertItem | null>(null)
const pendingStatusAlert = ref<StockAlertItem | null>(null)
const nextStatus = ref('')

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Open', value: 'open' },
  { label: 'Closed', value: 'closed' },
]

const actionStatusOptions = [
  { label: 'Open', value: 'open' },
  { label: 'Closed', value: 'closed' },
]

const filteredAlerts = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return alerts.value.filter((alert) => {
    const stockrecord = alert.stockrecord || {}
    const matchesSearch = !search
      || String(alert.id).includes(search)
      || String(stockrecord.product_id || '').includes(search)
      || String(stockrecord.id || '').includes(search)
      || String(stockrecord.partner_sku || '').toLowerCase().includes(search)
      || String(stockrecord.product_title || '').toLowerCase().includes(search)
    const matchesStatus = statusFilter.value === ALL_STATUSES || normalizeStatus(alert.status) === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

const openCount = computed(() => alerts.value.filter(alert => normalizeStatus(alert.status) !== 'closed').length)
const closedCount = computed(() => alerts.value.filter(alert => normalizeStatus(alert.status) === 'closed').length)
const criticalCount = computed(() => alerts.value.filter(alert => Number(alert.stockrecord?.num_in_stock || 0) <= 0).length)

function normalizeStatus(status?: string) {
  return String(status || 'open').toLowerCase()
}

function statusColor(status?: string) {
  return normalizeStatus(status) === 'closed' ? 'neutral' : 'warning'
}

function formatStatus(status?: string) {
  const value = String(status || 'open')
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not set'

  return new Intl.DateTimeFormat('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function openStatusDialog(alert: StockAlertItem, status: string) {
  pendingStatusAlert.value = alert
  nextStatus.value = status
}

async function loadStockAlerts() {
  isLoading.value = true
  const result = await getStockAlerts({ pageSize: 200 })

  if (result.success) {
    alerts.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? alerts.value.length
  }
  else {
    alerts.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load stock alerts',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function confirmStatusUpdate() {
  if (!pendingStatusAlert.value || !nextStatus.value)
    return

  isSaving.value = true
  const alert = pendingStatusAlert.value
  const result = await updateStockAlert(alert.id, { status: nextStatus.value })

  if (result.success) {
    toast.add({
      title: 'Stock alert updated',
      description: `Alert #${alert.id} was marked ${nextStatus.value}.`,
      color: 'success',
    })
    pendingStatusAlert.value = null
    nextStatus.value = ''
    await loadStockAlerts()
  }
  else {
    toast.add({
      title: 'Update failed',
      description: result.error || 'Could not update stock alert.',
      color: 'error',
    })
  }

  isSaving.value = false
}

onMounted(loadStockAlerts)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Stock Alerts</h1>
        <p class="mt-1 text-sm text-slate-500">Review stock records that crossed their low-stock thresholds.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search alerts..."
        />
        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadStockAlerts">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total alerts" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-bell-ring" :loading="isLoading" />
      <CardsKpiCard2 name="Open" :value="openCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-bell" :loading="isLoading" />
      <CardsKpiCard2 name="Closed" :value="closedCount" :budget="totalItems" color="#64748b" icon="i-lucide-check-check" :loading="isLoading" />
      <CardsKpiCard2 name="Out of stock" :value="criticalCount" :budget="totalItems" color="#dc2626" icon="i-lucide-circle-alert" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-4">Product</div>
        <div class="col-span-2">SKU</div>
        <div class="col-span-1 text-right">Stock</div>
        <div class="col-span-1 text-right">Threshold</div>
        <div class="col-span-1">Status</div>
        <div class="col-span-1">Created</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading stock alerts
      </div>

      <div v-else-if="filteredAlerts.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
          <UIcon name="i-lucide-bell-ring" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No stock alerts found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear the status filter, or wait for stock thresholds to trigger.</p>
      </div>

      <div
        v-for="alert in filteredAlerts"
        v-else
        :key="alert.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-4 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              <UIcon name="i-lucide-package" />
            </div>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ alert.stockrecord.product_title || 'Untitled product' }}</p>
              <p class="truncate text-xs text-slate-500">Product #{{ alert.stockrecord.product_id }} · Stock record #{{ alert.stockrecord.id }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2 truncate text-sm text-slate-600">{{ alert.stockrecord.partner_sku || 'No SKU' }}</div>
        <div class="col-span-1 text-right text-sm font-semibold" :class="Number(alert.stockrecord.num_in_stock || 0) <= 0 ? 'text-red-700' : 'text-slate-700'">
          {{ alert.stockrecord.num_in_stock }}
        </div>
        <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ alert.threshold }}</div>
        <div class="col-span-1">
          <UBadge :color="statusColor(alert.status)" variant="soft">{{ formatStatus(alert.status) }}</UBadge>
        </div>
        <div class="col-span-1 text-xs text-slate-500">{{ formatDate(alert.date_created) }}</div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="View alert">
            <UButton icon="i-lucide-eye" color="neutral" variant="ghost" square @click="selectedAlert = alert" />
          </UTooltip>
          <UTooltip v-if="normalizeStatus(alert.status) !== 'closed'" text="Close alert">
            <UButton icon="i-lucide-check" color="success" variant="ghost" square @click="openStatusDialog(alert, 'closed')" />
          </UTooltip>
          <UTooltip v-else text="Reopen alert">
            <UButton icon="i-lucide-rotate-ccw" color="warning" variant="ghost" square @click="openStatusDialog(alert, 'open')" />
          </UTooltip>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">
      Showing {{ filteredAlerts.length }} of {{ totalItems }} alerts.
    </p>

    <div
      v-if="selectedAlert"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">Stock alert #{{ selectedAlert.id }}</h3>
              <p class="text-sm text-dimmed">{{ selectedAlert.stockrecord.product_title || 'Untitled product' }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="selectedAlert = null" />
          </div>
        </template>

        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Status</p>
            <p class="mt-1 font-semibold text-slate-950">{{ formatStatus(selectedAlert.status) }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Partner SKU</p>
            <p class="mt-1 font-semibold text-slate-950">{{ selectedAlert.stockrecord.partner_sku || 'No SKU' }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Current stock</p>
            <p class="mt-1 font-semibold text-slate-950">{{ selectedAlert.stockrecord.num_in_stock }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Threshold</p>
            <p class="mt-1 font-semibold text-slate-950">{{ selectedAlert.threshold }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Created</p>
            <p class="mt-1 font-semibold text-slate-950">{{ formatDate(selectedAlert.date_created) }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-bold uppercase tracking-wide text-slate-500">Closed</p>
            <p class="mt-1 font-semibold text-slate-950">{{ formatDate(selectedAlert.date_closed) }}</p>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" @click="selectedAlert = null">
              Close
            </UButton>
            <UButton
              v-for="option in actionStatusOptions"
              :key="option.value"
              :color="option.value === 'closed' ? 'success' : 'warning'"
              variant="solid"
              :disabled="normalizeStatus(selectedAlert.status) === option.value"
              @click="openStatusDialog(selectedAlert, option.value)"
            >
              Mark {{ option.label }}
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div
      v-if="pendingStatusAlert"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-warning/10 p-2 text-warning">
              <UIcon name="i-lucide-bell-ring" />
            </div>
            <div>
              <h3 class="font-semibold text-default">Update stock alert</h3>
              <p class="text-sm text-dimmed">This changes the alert workflow status.</p>
            </div>
          </div>
        </template>

        <p class="text-sm text-default">
          Mark alert #{{ pendingStatusAlert.id }} as
          <span class="font-semibold">{{ nextStatus }}</span>?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingStatusAlert = null">
              Cancel
            </UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="confirmStatusUpdate">
              Update alert
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
