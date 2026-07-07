<script setup lang="ts">
import type { AuditLogItem } from '~/composables/useAuditLogs'

const toast = useToast()
const { getAuditLog, getAuditLogs } = useAuditLogs()

const auditLogs = ref<AuditLogItem[]>([])
const selectedLog = ref<AuditLogItem | null>(null)
const totalItems = ref(0)
const page = ref(1)
const pageSize = ref(50)
const numPages = ref(1)
const hasNext = ref(false)
const isLoading = ref(false)
const detailOpen = ref(false)
const ALL_STATUSES = '__all_statuses__'

const filters = reactive({
  search: '',
  eventType: '',
  actorEmail: '',
  targetType: '',
  targetId: '',
  path: '',
  status: ALL_STATUSES,
  dateFrom: '',
  dateTo: '',
})

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Success', value: 'success' },
  { label: 'Failure', value: 'failure' },
]

const pageSizeOptions = [
  { label: '25 rows', value: 25 },
  { label: '50 rows', value: 50 },
  { label: '100 rows', value: 100 },
  { label: '200 rows', value: 200 },
]

const successCount = computed(() => auditLogs.value.filter(log => log.status === 'success').length)
const failureCount = computed(() => auditLogs.value.filter(log => log.status === 'failure').length)
const actorCount = computed(() => new Set(auditLogs.value.map(log => log.actor_email).filter(Boolean)).size)

function statusColor(status: string) {
  return status === 'failure' ? 'error' : 'success'
}

function formatStatus(status: string) {
  return status ? status.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function formatDate(value: string) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function metadataPreview(metadata: Record<string, any> | null | undefined) {
  if (!metadata || Object.keys(metadata).length === 0)
    return 'No metadata'
  return JSON.stringify(metadata)
}

function resetFilters() {
  filters.search = ''
  filters.eventType = ''
  filters.actorEmail = ''
  filters.targetType = ''
  filters.targetId = ''
  filters.path = ''
  filters.status = ALL_STATUSES
  filters.dateFrom = ''
  filters.dateTo = ''
  page.value = 1
  loadAuditLogs()
}

async function loadAuditLogs() {
  isLoading.value = true
  const result = await getAuditLogs({
    page: page.value,
    pageSize: pageSize.value,
    search: filters.search.trim(),
    eventType: filters.eventType.trim(),
    actorEmail: filters.actorEmail.trim(),
    targetType: filters.targetType.trim(),
    targetId: filters.targetId.trim(),
    path: filters.path.trim(),
    status: filters.status === ALL_STATUSES ? '' : filters.status,
    dateFrom: filters.dateFrom,
    dateTo: filters.dateTo,
  })

  if (result.success) {
    auditLogs.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? auditLogs.value.length
    numPages.value = result.data?.pagination?.num_pages ?? 1
    hasNext.value = !!result.data?.pagination?.has_next
  }
  else {
    auditLogs.value = []
    totalItems.value = 0
    toast.add({ title: 'Could not load audit logs', description: result.error || 'Please try again.', color: 'error' })
  }

  isLoading.value = false
}

async function openDetail(log: AuditLogItem) {
  selectedLog.value = log
  detailOpen.value = true
  const result = await getAuditLog(log.id)
  if (result.success && result.data)
    selectedLog.value = result.data
  else if (!result.success)
    toast.add({ title: 'Could not load audit log detail', description: result.error || 'Please try again.', color: 'error' })
}

function applyFilters() {
  page.value = 1
  loadAuditLogs()
}

watch(page, loadAuditLogs)
watch(pageSize, () => {
  page.value = 1
  loadAuditLogs()
})

onMounted(loadAuditLogs)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Audit Logs</h1>
        <p class="mt-1 text-sm text-slate-500">Inspect admin and system activity across accounts, catalog, orders, and integrations.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="filters.search"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search logs..."
          @keyup.enter="applyFilters"
        />
        <USelect v-model="pageSize" :items="pageSizeOptions" class="w-32" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadAuditLogs">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total matches" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-list-checks" :loading="isLoading" />
      <CardsKpiCard2 name="Loaded success" :value="successCount" :budget="auditLogs.length || 1" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Loaded failure" :value="failureCount" :budget="auditLogs.length || 1" color="#dc2626" icon="i-lucide-circle-x" :loading="isLoading" />
      <CardsKpiCard2 name="Loaded actors" :value="actorCount" :budget="auditLogs.length || 1" color="#7c3aed" icon="i-lucide-users" :loading="isLoading" />
    </div>

    <div class="mb-6 rounded-lg border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <UFormField label="Event type"><UInput v-model="filters.eventType" placeholder="orders.status_changed" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Actor email"><UInput v-model="filters.actorEmail" placeholder="operator@example.com" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Target model"><UInput v-model="filters.targetType" placeholder="order.Order" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Target ID"><UInput v-model="filters.targetId" placeholder="123" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Path"><UInput v-model="filters.path" placeholder="/api/v1/admin/orders/" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Status"><USelect v-model="filters.status" :items="statusOptions" /></UFormField>
        <UFormField label="From"><UInput v-model="filters.dateFrom" type="date" /></UFormField>
        <UFormField label="To"><UInput v-model="filters.dateTo" type="date" /></UFormField>
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <UButton color="neutral" variant="outline" @click="resetFilters">
          <UIcon name="i-lucide-rotate-ccw" />
          Reset
        </UButton>
        <UButton color="primary" variant="solid" :loading="isLoading" @click="applyFilters">
          <UIcon name="i-lucide-filter" />
          Apply Filters
        </UButton>
      </div>
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Event</div>
        <div class="col-span-2">Actor</div>
        <div class="col-span-2">Target</div>
        <div class="col-span-2">Request</div>
        <div class="col-span-2">Created</div>
        <div class="col-span-1 text-right">Action</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading audit logs
      </div>

      <div v-else-if="auditLogs.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
          <UIcon name="i-lucide-list-checks" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No audit logs found</h2>
        <p class="mt-1 text-sm text-slate-500">Try broadening the filters.</p>
      </div>

      <div
        v-for="log in auditLogs"
        v-else
        :key="log.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-3 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <UBadge :color="statusColor(log.status)" variant="soft">{{ formatStatus(log.status) }}</UBadge>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ log.event_type }}</p>
              <p class="truncate text-xs text-slate-500">{{ log.message || 'No message' }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.actor_email || 'Anonymous' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.actor_role || 'No role' }}</p>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.target_type || 'No target' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.target_id || log.target_repr || 'No ID' }}</p>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.request_method || 'System' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.path || 'No path' }}</p>
        </div>
        <div class="col-span-2 text-sm text-slate-700">{{ formatDate(log.created_at) }}</div>
        <div class="col-span-1 text-right">
          <UTooltip text="View detail">
            <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openDetail(log)" />
          </UTooltip>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
        <UButton color="neutral" variant="outline" :disabled="page <= 1 || isLoading" @click="page -= 1">
          <UIcon name="i-lucide-chevron-left" />
          Previous
        </UButton>
        <span class="text-sm text-slate-500">Page {{ page }} of {{ numPages }} · {{ totalItems }} matches</span>
        <UButton color="neutral" variant="outline" :disabled="!hasNext || isLoading" @click="page += 1">
          Next
          <UIcon name="i-lucide-chevron-right" />
        </UButton>
      </div>
    </div>

    <div v-if="detailOpen && selectedLog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[90vh] w-full max-w-4xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-default">{{ selectedLog.event_type }}</h3>
              <p class="text-sm text-dimmed">Audit log #{{ selectedLog.id }} · {{ formatDate(selectedLog.created_at) }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="detailOpen = false" />
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Actor</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Email</dt><dd class="break-all text-slate-950">{{ selectedLog.actor_email || 'Anonymous' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Role</dt><dd class="text-slate-950">{{ selectedLog.actor_role || 'No role' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Actor ID</dt><dd class="text-slate-950">{{ selectedLog.actor_id || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">IP address</dt><dd class="text-slate-950">{{ selectedLog.ip_address || 'Not recorded' }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Target</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Type</dt><dd class="break-all text-slate-950">{{ selectedLog.target_type || 'No target' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">ID</dt><dd class="text-slate-950">{{ selectedLog.target_id || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Label</dt><dd class="break-all text-slate-950">{{ selectedLog.target_repr || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Status</dt><dd><UBadge :color="statusColor(selectedLog.status)" variant="soft">{{ formatStatus(selectedLog.status) }}</UBadge></dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4 md:col-span-2">
            <h4 class="mb-3 font-black text-slate-950">Request</h4>
            <dl class="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div><dt class="font-semibold text-slate-500">Method</dt><dd class="text-slate-950">{{ selectedLog.request_method || 'System' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Path</dt><dd class="break-all text-slate-950">{{ selectedLog.path || 'No path' }}</dd></div>
              <div class="md:col-span-2"><dt class="font-semibold text-slate-500">User agent</dt><dd class="break-all text-slate-950">{{ selectedLog.user_agent || 'Not recorded' }}</dd></div>
              <div class="md:col-span-2"><dt class="font-semibold text-slate-500">Message</dt><dd class="text-slate-950">{{ selectedLog.message || 'No message' }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4 md:col-span-2">
            <h4 class="mb-3 font-black text-slate-950">Metadata</h4>
            <pre class="max-h-80 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-50">{{ metadataPreview(selectedLog.metadata) }}</pre>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
