<script setup lang="ts">
import type { BackupRun, BackupStatus } from '~/composables/useBackups'

const toast = useToast()
const { getBackups, createBackup, verifyBackup, downloadUrl } = useBackups()

const backups = ref<BackupRun[]>([])
const status = ref<BackupStatus | null>(null)
const page = ref(1)
const pageSize = ref(20)
const totalItems = ref(0)
const statusFilter = ref('')
const backupTypeFilter = ref('')
const isLoading = ref(false)
const isRunning = ref(false)
const verifyingId = ref<number | null>(null)

const statusOptions = [
  { label: 'All statuses', value: '__all__' },
  { label: 'Success', value: 'success' },
  { label: 'Failed', value: 'failed' },
  { label: 'Running', value: 'running' },
  { label: 'Pending', value: 'pending' },
]
const typeOptions = [
  { label: 'All backup types', value: '__all__' },
  { label: 'Full', value: 'full' },
  { label: 'Database', value: 'database' },
  { label: 'Media', value: 'media' },
]
const createOptions = [
  { label: 'Full backup', value: 'full', icon: 'i-lucide-archive' },
  { label: 'Database only', value: 'database', icon: 'i-lucide-database' },
  { label: 'Media only', value: 'media', icon: 'i-lucide-image' },
]

const numPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
const latestSuccessAge = computed(() => {
  const value = status.value?.latest_success?.finished_at
  if (!value)
    return 'No successful backup yet'
  return formatDate(value)
})

function badgeColor(value: string) {
  if (value === 'success')
    return 'success'
  if (value === 'failed')
    return 'error'
  if (value === 'running')
    return 'info'
  return 'warning'
}

function formatDate(value?: string | null) {
  if (!value)
    return '-'
  return new Intl.DateTimeFormat('en-KE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatSize(value: number) {
  if (!value)
    return '-'
  return `${Number(value / (1024 * 1024)).toLocaleString('en', { maximumFractionDigits: 2 })} MB`
}

async function loadBackups() {
  isLoading.value = true
  const result = await getBackups({
    page: page.value,
    pageSize: pageSize.value,
    status: statusFilter.value === '__all__' ? '' : statusFilter.value,
    backupType: backupTypeFilter.value === '__all__' ? '' : backupTypeFilter.value,
  })
  if (result.success && result.data) {
    backups.value = result.data.results
    status.value = result.data.status
    totalItems.value = result.data.pagination.total
  }
  else {
    backups.value = []
    toast.add({ title: 'Could not load backups', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

async function triggerBackup(type: BackupRun['backup_type']) {
  isRunning.value = true
  const result = await createBackup(type)
  if (result.success) {
    toast.add({ title: 'Backup started', description: `Created ${type} backup run #${result.data?.id}.`, color: 'success' })
    await loadBackups()
  }
  else {
    toast.add({ title: 'Backup failed', description: result.error || 'Please try again.', color: 'error' })
  }
  isRunning.value = false
}

async function handleVerify(backup: BackupRun) {
  verifyingId.value = backup.id
  const result = await verifyBackup(backup.id)
  if (result.success && result.data?.valid)
    toast.add({ title: 'Backup verified', description: 'Checksum matches the saved backup record.', color: 'success' })
  else
    toast.add({ title: 'Backup verification failed', description: result.error || 'Checksum mismatch.', color: 'error' })
  verifyingId.value = null
}

watch([page, pageSize, statusFilter, backupTypeFilter], () => loadBackups())
onMounted(loadBackups)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">
          Backups
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          Protect orders, payments, products, media, suppliers, and integration state.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <USelect v-model="backupTypeFilter" :items="typeOptions" class="w-44" />
        <USelect v-model="statusFilter" :items="statusOptions" class="w-40" />
        <UDropdownMenu :items="[createOptions.map(item => ({ ...item, onSelect: () => triggerBackup(item.value as BackupRun['backup_type']) }))]">
          <UButton icon="i-lucide-plus" :loading="isRunning">
            Create backup
          </UButton>
        </UDropdownMenu>
      </div>
    </div>

    <div class="mb-5 grid gap-4 md:grid-cols-4">
      <CardsKpiCard2 name="Latest success" :value="latestSuccessAge" :budget="totalItems || 1" color="#059669" icon="i-lucide-shield-check" :loading="isLoading" />
      <CardsKpiCard2 name="Successful" :value="status?.success_count || 0" :budget="Math.max(totalItems, 1)" color="#30328f" icon="i-lucide-check-check" :loading="isLoading" />
      <CardsKpiCard2 name="Failed" :value="status?.failed_count || 0" :budget="Math.max(totalItems, 1)" color="#dc2626" icon="i-lucide-circle-alert" :loading="isLoading" />
      <CardsKpiCard2 name="Running" :value="status?.running_count || 0" :budget="Math.max(totalItems, 1)" color="#f59e0b" icon="i-lucide-loader" :loading="isLoading" />
    </div>

    <UCard :ui="{ body: 'p-0' }">
      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        Loading backups...
      </div>
      <div v-else-if="!backups.length" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
          <UIcon name="i-lucide-archive" />
        </div>
        <h2 class="mt-3 text-base font-black text-slate-950">
          No backups yet
        </h2>
        <p class="mt-1 text-sm text-slate-500">
          Create a full backup before launch and test restore in staging.
        </p>
      </div>
      <div v-else>
        <div
          v-for="backup in backups"
          :key="backup.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
        >
          <div class="col-span-12 md:col-span-4">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-archive" />
              </div>
              <div class="min-w-0">
                <p class="truncate text-sm font-black text-slate-950">
                  #{{ backup.id }} {{ backup.backup_type }}
                </p>
                <p class="truncate text-xs text-slate-500">
                  {{ backup.message || 'No message' }}
                </p>
              </div>
            </div>
          </div>
          <div class="col-span-6 md:col-span-2">
            <UBadge :color="badgeColor(backup.status)" variant="soft">
              {{ backup.status }}
            </UBadge>
          </div>
          <div class="col-span-6 text-sm font-semibold text-slate-700 md:col-span-2">
            {{ formatSize(backup.size_bytes) }}
          </div>
          <div class="col-span-12 text-sm text-slate-500 md:col-span-2">
            {{ formatDate(backup.finished_at || backup.created_at) }}
          </div>
          <div class="col-span-12 flex items-center justify-end gap-2 md:col-span-2">
            <UButton icon="i-lucide-shield-check" color="neutral" variant="ghost" :loading="verifyingId === backup.id" @click="handleVerify(backup)" />
            <UButton
              v-if="backup.status === 'success'"
              icon="i-lucide-download"
              color="neutral"
              variant="ghost"
              :to="downloadUrl(backup.id)"
              external
            />
          </div>
        </div>
      </div>
    </UCard>

    <div class="mt-4 flex items-center justify-between text-sm text-slate-500">
      <span>Page {{ page }} of {{ numPages }} · {{ totalItems }} backups</span>
      <div class="flex items-center gap-2">
        <UButton icon="i-lucide-chevron-left" color="neutral" variant="outline" :disabled="page <= 1" @click="page--" />
        <UButton icon="i-lucide-chevron-right" color="neutral" variant="outline" :disabled="page >= numPages" @click="page++" />
      </div>
    </div>
  </div>
</template>
