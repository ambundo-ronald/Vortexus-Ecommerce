<script setup lang="ts">
import type { AdminEmailSuppressionItem } from '~/composables/useEmailConfig'

const toast = useToast()
const { createEmailSuppression, deleteEmailSuppression, getEmailSuppressions } = useEmailConfig()

const suppressions = ref<AdminEmailSuppressionItem[]>([])
const summary = ref<any>({})
const page = ref(1)
const pageSize = ref(50)
const totalItems = ref(0)
const numPages = ref(1)
const hasNext = ref(false)
const isLoading = ref(false)
const saving = ref(false)

const filters = reactive({
  search: '',
  reason: '',
})

const form = reactive({
  email: '',
  reason: 'manual',
  source: 'admin',
  note: '',
})

const reasonOptions = [
  { label: 'All reasons', value: '' },
  { label: 'Bounce', value: 'bounce' },
  { label: 'Complaint', value: 'complaint' },
  { label: 'Manual', value: 'manual' },
  { label: 'Unsubscribe', value: 'unsubscribe' },
]

function formatDate(value?: string) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function reasonColor(reason: string) {
  if (reason === 'bounce')
    return 'error'
  if (reason === 'complaint')
    return 'warning'
  if (reason === 'unsubscribe')
    return 'neutral'
  return 'primary'
}

async function loadSuppressions() {
  isLoading.value = true
  const result = await getEmailSuppressions({
    page: page.value,
    pageSize: pageSize.value,
    search: filters.search.trim(),
    reason: filters.reason,
  })
  if (result.success) {
    suppressions.value = result.data?.results ?? []
    summary.value = result.data?.summary ?? {}
    totalItems.value = result.data?.pagination?.total ?? suppressions.value.length
    numPages.value = result.data?.pagination?.num_pages ?? 1
    hasNext.value = !!result.data?.pagination?.has_next
  }
  else {
    toast.add({ title: 'Could not load suppressions', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

async function saveSuppression() {
  saving.value = true
  const result = await createEmailSuppression({ ...form })
  if (result.success) {
    toast.add({ title: 'Suppression saved', description: `${form.email} will be skipped by email delivery.`, color: 'success' })
    form.email = ''
    form.reason = 'manual'
    form.source = 'admin'
    form.note = ''
    await loadSuppressions()
  }
  else {
    toast.add({ title: 'Could not save suppression', description: result.error || 'Please check the email address.', color: 'error' })
  }
  saving.value = false
}

async function removeSuppression(item: AdminEmailSuppressionItem) {
  const result = await deleteEmailSuppression(item.id)
  if (result.success) {
    toast.add({ title: 'Suppression removed', description: `${item.email} can receive emails again.`, color: 'success' })
    await loadSuppressions()
  }
  else {
    toast.add({ title: 'Could not remove suppression', description: result.error || 'Please try again.', color: 'error' })
  }
}

function applyFilters() {
  page.value = 1
  loadSuppressions()
}

watch(page, loadSuppressions)
onMounted(loadSuppressions)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Email Suppressions</h1>
        <p class="mt-1 text-sm text-slate-500">Prevent delivery to bounced, complained, unsubscribed, or manually blocked recipients.</p>
      </div>
      <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadSuppressions">
        <UIcon name="i-lucide-refresh-cw" />
        Refresh
      </UButton>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <CardsKpiCard2 name="Total" :value="summary.total || 0" :budget="summary.total || 1" color="#3d7cff" icon="i-lucide-mail-x" :loading="isLoading" />
      <CardsKpiCard2 name="Bounces" :value="summary.bounce || 0" :budget="summary.total || 1" color="#dc2626" icon="i-lucide-octagon-alert" :loading="isLoading" />
      <CardsKpiCard2 name="Complaints" :value="summary.complaint || 0" :budget="summary.total || 1" color="#b45309" icon="i-lucide-message-square-warning" :loading="isLoading" />
      <CardsKpiCard2 name="Manual" :value="summary.manual || 0" :budget="summary.total || 1" color="#255be8" icon="i-lucide-user-x" :loading="isLoading" />
      <CardsKpiCard2 name="Unsubscribed" :value="summary.unsubscribe || 0" :budget="summary.total || 1" color="#64748b" icon="i-lucide-bell-off" :loading="isLoading" />
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div class="rounded-lg border border-slate-200 bg-white p-4 xl:col-span-1">
        <h2 class="mb-4 text-base font-black text-slate-950">Add Suppression</h2>
        <div class="space-y-3">
          <UFormField label="Email"><UInput v-model="form.email" type="email" placeholder="customer@example.com" /></UFormField>
          <UFormField label="Reason"><USelect v-model="form.reason" :items="reasonOptions.filter(option => option.value)" /></UFormField>
          <UFormField label="Source"><UInput v-model="form.source" placeholder="admin" /></UFormField>
          <UFormField label="Note"><UTextarea v-model="form.note" :rows="4" placeholder="Why this recipient should be suppressed" /></UFormField>
          <UButton block color="primary" :loading="saving" :disabled="!form.email" @click="saveSuppression">
            <UIcon name="i-lucide-plus" />
            Save Suppression
          </UButton>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-4 xl:col-span-2">
        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <UInput v-model="filters.search" class="md:col-span-2" icon="i-lucide-search" placeholder="Search suppressions..." @keyup.enter="applyFilters" />
          <USelect v-model="filters.reason" :items="reasonOptions" />
        </div>
        <div class="mb-4 flex justify-end">
          <UButton color="primary" :loading="isLoading" @click="applyFilters">
            <UIcon name="i-lucide-filter" />
            Apply Filters
          </UButton>
        </div>

        <div class="overflow-hidden rounded-lg border border-slate-200">
          <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase text-slate-500">
            <div class="col-span-4">Email</div>
            <div class="col-span-2">Reason</div>
            <div class="col-span-2">Source</div>
            <div class="col-span-3">Updated</div>
            <div class="col-span-1 text-right">Action</div>
          </div>
          <div v-if="isLoading" class="p-10 text-center text-sm font-semibold text-slate-500">
            <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
            Loading suppressions
          </div>
          <div v-else-if="suppressions.length === 0" class="p-10 text-center text-sm text-slate-500">No suppressed recipients found.</div>
          <div v-for="item in suppressions" v-else :key="item.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0">
            <div class="col-span-4 min-w-0">
              <p class="truncate text-sm font-semibold text-slate-950">{{ item.email }}</p>
              <p class="truncate text-xs text-slate-500">{{ item.note || 'No note' }}</p>
            </div>
            <div class="col-span-2"><UBadge :color="reasonColor(item.reason)" variant="soft">{{ item.reason }}</UBadge></div>
            <div class="col-span-2 truncate text-sm text-slate-700">{{ item.source || 'Not recorded' }}</div>
            <div class="col-span-3 text-sm text-slate-700">{{ formatDate(item.updated_at) }}</div>
            <div class="col-span-1 text-right">
              <UTooltip text="Remove suppression">
                <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="removeSuppression(item)" />
              </UTooltip>
            </div>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between">
          <UButton color="neutral" variant="outline" :disabled="page <= 1 || isLoading" @click="page -= 1"><UIcon name="i-lucide-chevron-left" />Previous</UButton>
          <span class="text-sm text-slate-500">Page {{ page }} of {{ numPages }} - {{ totalItems }} matches</span>
          <UButton color="neutral" variant="outline" :disabled="!hasNext || isLoading" @click="page += 1">Next<UIcon name="i-lucide-chevron-right" /></UButton>
        </div>
      </div>
    </div>
  </div>
</template>
