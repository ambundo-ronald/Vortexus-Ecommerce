<script setup lang="ts">
import type { AdminEmailLogItem } from '~/composables/useEmailConfig'

const toast = useToast()
const { getEmailLog, getEmailLogs, retryEmailLog } = useEmailConfig()

const logs = ref<AdminEmailLogItem[]>([])
const selectedLog = ref<AdminEmailLogItem | null>(null)
const summary = ref<any>({})
const totalItems = ref(0)
const page = ref(1)
const pageSize = ref(50)
const numPages = ref(1)
const hasNext = ref(false)
const isLoading = ref(false)
const detailOpen = ref(false)
const retryingId = ref<number | null>(null)
const ALL_STATUSES = '__all_statuses__'

const filters = reactive({
  search: '',
  eventType: '',
  status: ALL_STATUSES,
  recipient: '',
  relatedObjectType: '',
  relatedObjectId: '',
  dateFrom: '',
  dateTo: '',
})

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Sent', value: 'sent' },
  { label: 'Failed', value: 'failed' },
  { label: 'Skipped', value: 'skipped' },
  { label: 'Pending', value: 'pending' },
]

const pageSizeOptions = [
  { label: '25 rows', value: 25 },
  { label: '50 rows', value: 50 },
  { label: '100 rows', value: 100 },
  { label: '200 rows', value: 200 },
]

function statusColor(status: string) {
  if (status === 'failed')
    return 'error'
  if (status === 'skipped')
    return 'warning'
  if (status === 'sent')
    return 'success'
  return 'neutral'
}

function formatLabel(value: string) {
  return value ? value.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function metadataPreview(metadata: Record<string, any> | null | undefined) {
  if (!metadata || Object.keys(metadata).length === 0)
    return 'No metadata'
  return JSON.stringify(metadata, null, 2)
}

function canRetry(log: AdminEmailLogItem) {
  return log.event_type !== 'email_two_factor' && log.status !== 'sent'
}

async function loadLogs() {
  isLoading.value = true
  const result = await getEmailLogs({
    page: page.value,
    pageSize: pageSize.value,
    search: filters.search.trim(),
    eventType: filters.eventType.trim(),
    status: filters.status === ALL_STATUSES ? '' : filters.status,
    recipient: filters.recipient.trim(),
    relatedObjectType: filters.relatedObjectType.trim(),
    relatedObjectId: filters.relatedObjectId.trim(),
    dateFrom: filters.dateFrom,
    dateTo: filters.dateTo,
  })

  if (result.success) {
    logs.value = result.data?.results ?? []
    summary.value = result.data?.summary ?? {}
    totalItems.value = result.data?.pagination?.total ?? logs.value.length
    numPages.value = result.data?.pagination?.num_pages ?? 1
    hasNext.value = !!result.data?.pagination?.has_next
  }
  else {
    logs.value = []
    totalItems.value = 0
    toast.add({ title: 'Could not load email logs', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

async function openDetail(log: AdminEmailLogItem) {
  selectedLog.value = log
  detailOpen.value = true
  const result = await getEmailLog(log.id)
  if (result.success && result.data)
    selectedLog.value = result.data
  else if (!result.success)
    toast.add({ title: 'Could not load email log', description: result.error || 'Please try again.', color: 'error' })
}

async function retryLog(log: AdminEmailLogItem) {
  retryingId.value = log.id
  const result = await retryEmailLog(log.id)
  if (result.success) {
    toast.add({ title: 'Email retry sent', description: result.data?.detail || 'A fresh email was queued/sent.', color: 'success' })
    await loadLogs()
    if (selectedLog.value?.id === log.id) {
      const detail = await getEmailLog(log.id)
      if (detail.success && detail.data)
        selectedLog.value = detail.data
    }
  }
  else {
    toast.add({ title: 'Retry failed', description: result.error || 'This email could not be retried.', color: 'error' })
  }
  retryingId.value = null
}

function applyFilters() {
  page.value = 1
  loadLogs()
}

function resetFilters() {
  filters.search = ''
  filters.eventType = ''
  filters.status = ALL_STATUSES
  filters.recipient = ''
  filters.relatedObjectType = ''
  filters.relatedObjectId = ''
  filters.dateFrom = ''
  filters.dateTo = ''
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
        <h1 class="text-2xl font-black text-slate-950">Email Logs</h1>
        <p class="mt-1 text-sm text-slate-500">Review sent, failed, skipped, and pending email notifications.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput v-model="filters.search" class="min-w-56 flex-1 lg:max-w-sm" icon="i-lucide-search" placeholder="Search email logs..." @keyup.enter="applyFilters" />
        <USelect v-model="pageSize" :items="pageSizeOptions" class="w-32" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadLogs">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <CardsKpiCard2 name="Total emails" :value="summary.total || 0" :budget="summary.total || 1" color="#3d7cff" icon="i-lucide-mails" :loading="isLoading" />
      <CardsKpiCard2 name="Sent" :value="summary.sent || 0" :budget="summary.total || 1" color="#059669" icon="i-lucide-mail-check" :loading="isLoading" />
      <CardsKpiCard2 name="Failed" :value="summary.failed || 0" :budget="summary.total || 1" color="#dc2626" icon="i-lucide-mail-x" :loading="isLoading" />
      <CardsKpiCard2 name="Skipped" :value="summary.skipped || 0" :budget="summary.total || 1" color="#b45309" icon="i-lucide-mail-minus" :loading="isLoading" />
      <CardsKpiCard2 name="Pending" :value="summary.pending || 0" :budget="summary.total || 1" color="#64748b" icon="i-lucide-clock" :loading="isLoading" />
    </div>

    <div class="mb-6 rounded-lg border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <UFormField label="Event type"><UInput v-model="filters.eventType" placeholder="password_reset" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Status"><USelect v-model="filters.status" :items="statusOptions" /></UFormField>
        <UFormField label="Recipient"><UInput v-model="filters.recipient" placeholder="customer@example.com" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Related type"><UInput v-model="filters.relatedObjectType" placeholder="order" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="Related ID"><UInput v-model="filters.relatedObjectId" placeholder="100001" @keyup.enter="applyFilters" /></UFormField>
        <UFormField label="From"><UInput v-model="filters.dateFrom" type="date" /></UFormField>
        <UFormField label="To"><UInput v-model="filters.dateTo" type="date" /></UFormField>
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
        <div class="col-span-3">Email</div>
        <div class="col-span-2">Recipient</div>
        <div class="col-span-2">Related</div>
        <div class="col-span-2">Sent</div>
        <div class="col-span-2">Created</div>
        <div class="col-span-1 text-right">Action</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading email logs
      </div>

      <div v-else-if="logs.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-mail-search" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No email logs found</h2>
        <p class="mt-1 text-sm text-slate-500">Try broadening the filters.</p>
      </div>

      <div v-for="log in logs" v-else :key="log.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50">
        <div class="col-span-3 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <UBadge :color="statusColor(log.status)" variant="soft">{{ formatLabel(log.status) }}</UBadge>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ formatLabel(log.event_type) }}</p>
              <p class="truncate text-xs text-slate-500">{{ log.subject || 'No subject' }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.recipient || 'No recipient' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.error_message || 'No error' }}</p>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ log.related_object_type || 'No related type' }}</p>
          <p class="truncate text-xs text-slate-500">{{ log.related_object_id || 'No related ID' }}</p>
        </div>
        <div class="col-span-2 text-sm text-slate-700">{{ formatDate(log.sent_at) }}</div>
        <div class="col-span-2 text-sm text-slate-700">{{ formatDate(log.created_at) }}</div>
        <div class="col-span-1 text-right">
          <div class="flex justify-end gap-1">
            <UTooltip v-if="canRetry(log)" text="Retry email">
              <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" square :loading="retryingId === log.id" @click="retryLog(log)" />
            </UTooltip>
            <UTooltip text="View detail">
              <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openDetail(log)" />
            </UTooltip>
          </div>
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
              <h3 class="truncate font-semibold text-default">{{ selectedLog.subject || formatLabel(selectedLog.event_type) }}</h3>
              <p class="text-sm text-dimmed">Email log #{{ selectedLog.id }} · {{ formatDate(selectedLog.created_at) }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="detailOpen = false" />
          </div>
        </template>

        <div class="mb-4 flex justify-end" v-if="canRetry(selectedLog)">
          <UButton color="primary" variant="solid" icon="i-lucide-refresh-cw" :loading="retryingId === selectedLog.id" @click="retryLog(selectedLog)">
            Retry Email
          </UButton>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Delivery</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Status</dt><dd><UBadge :color="statusColor(selectedLog.status)" variant="soft">{{ formatLabel(selectedLog.status) }}</UBadge></dd></div>
              <div><dt class="font-semibold text-slate-500">Event</dt><dd class="text-slate-950">{{ selectedLog.event_type }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Recipient</dt><dd class="break-all text-slate-950">{{ selectedLog.recipient }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Sent at</dt><dd class="text-slate-950">{{ formatDate(selectedLog.sent_at) }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Related Object</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Type</dt><dd class="break-all text-slate-950">{{ selectedLog.related_object_type || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">ID</dt><dd class="break-all text-slate-950">{{ selectedLog.related_object_id || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Created</dt><dd class="text-slate-950">{{ formatDate(selectedLog.created_at) }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Updated</dt><dd class="text-slate-950">{{ formatDate(selectedLog.updated_at) }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4 md:col-span-2">
            <h4 class="mb-3 font-black text-slate-950">Subject</h4>
            <p class="break-all text-sm text-slate-950">{{ selectedLog.subject || 'No subject' }}</p>
          </div>

          <div v-if="selectedLog.error_message" class="rounded-lg border border-red-200 bg-red-50 p-4 md:col-span-2">
            <h4 class="mb-3 font-black text-red-900">Error</h4>
            <p class="break-all text-sm text-red-900">{{ selectedLog.error_message }}</p>
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
