<script setup lang="ts">
import type { OfferItem } from '~/composables/useOffers'
import type { VoucherItem, VoucherPayload } from '~/composables/useVouchers'

const ALL_USAGE = '__all_usage__'
const ALL_STATE = '__all_state__'

const toast = useToast()
const {
  attachVoucherOffer,
  createVoucher,
  deleteVoucher,
  detachVoucherOffer,
  getVoucherStats,
  getVouchers,
  updateVoucher,
} = useVouchers()
const { getOffers } = useOffers()
const { firstRequiredError } = useAdminForm()

const vouchers = ref<VoucherItem[]>([])
const offers = ref<OfferItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const usageFilter = ref(ALL_USAGE)
const stateFilter = ref(ALL_STATE)
const editorOpen = ref(false)
const editingVoucher = ref<VoucherItem | null>(null)
const selectedVoucher = ref<VoucherItem | null>(null)
const statsVoucher = ref<VoucherItem | null>(null)
const pendingDeleteVoucher = ref<VoucherItem | null>(null)
const pendingDetach = ref<{ voucher: VoucherItem, offer: OfferItem } | null>(null)
const attachOfferId = ref<number | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  code: '',
  usage: 'Single use',
  start_datetime: '',
  end_datetime: '',
})

const usageOptions = [
  { label: 'All usage', value: ALL_USAGE },
  { label: 'Single use', value: 'Single use' },
  { label: 'Multi-use', value: 'Multi-use' },
  { label: 'Once per customer', value: 'Once per customer' },
]

const usageFormOptions = usageOptions.filter(option => option.value !== ALL_USAGE)

const stateOptions = [
  { label: 'All states', value: ALL_STATE },
  { label: 'Active', value: 'active' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Expired', value: 'expired' },
]

const attachOfferOptions = computed(() => {
  const linked = new Set((selectedVoucher.value?.offers || []).map(offer => offer.id))
  return offers.value
    .filter(offer => !linked.has(offer.id))
    .map(offer => ({
      label: `#${offer.id} ${offer.name}`,
      value: offer.id,
    }))
})

const filteredVouchers = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return vouchers.value.filter((voucher) => {
    const matchesSearch = !search
      || voucher.name.toLowerCase().includes(search)
      || voucher.code.toLowerCase().includes(search)
      || String(voucher.id).includes(search)
    const matchesUsage = usageFilter.value === ALL_USAGE || voucher.usage === usageFilter.value
    const matchesState = stateFilter.value === ALL_STATE || voucherState(voucher) === stateFilter.value
    return matchesSearch && matchesUsage && matchesState
  })
})

const activeCount = computed(() => vouchers.value.filter(voucher => voucherState(voucher) === 'active').length)
const expiredCount = computed(() => vouchers.value.filter(voucher => voucherState(voucher) === 'expired').length)
const linkedOfferCount = computed(() => vouchers.value.reduce((total, voucher) => total + (voucher.offers?.length || 0), 0))

function voucherState(voucher: VoucherItem) {
  const now = Date.now()
  const start = voucher.start_datetime ? new Date(voucher.start_datetime).getTime() : 0
  const end = voucher.end_datetime ? new Date(voucher.end_datetime).getTime() : 0

  if (start && start > now)
    return 'scheduled'
  if (end && end < now)
    return 'expired'
  return 'active'
}

function stateColor(voucher: VoucherItem) {
  const state = voucherState(voucher)
  if (state === 'active')
    return 'success'
  if (state === 'scheduled')
    return 'info'
  return 'neutral'
}

function formatState(voucher: VoucherItem) {
  const state = voucherState(voucher)
  return state.charAt(0).toUpperCase() + state.slice(1)
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

function formatMoney(value?: string | number | null) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    maximumFractionDigits: 0,
  }).format(amount)
}

function toDateTimeInput(value?: string | null) {
  if (!value)
    return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime()))
    return ''

  return date.toISOString().slice(0, 16)
}

function defaultEndDate() {
  const date = new Date()
  date.setMonth(date.getMonth() + 1)
  return date.toISOString().slice(0, 16)
}

function resetForm() {
  editingVoucher.value = null
  saveError.value = ''
  form.name = ''
  form.code = ''
  form.usage = 'Single use'
  form.start_datetime = new Date().toISOString().slice(0, 16)
  form.end_datetime = defaultEndDate()
}

function openCreateVoucher() {
  resetForm()
  editorOpen.value = true
}

function openEditVoucher(voucher: VoucherItem) {
  editingVoucher.value = voucher
  saveError.value = ''
  form.name = voucher.name
  form.code = voucher.code
  form.usage = voucher.usage
  form.start_datetime = toDateTimeInput(voucher.start_datetime)
  form.end_datetime = toDateTimeInput(voucher.end_datetime)
  editorOpen.value = true
}

async function loadVouchers() {
  isLoading.value = true
  const [voucherResult, offerResult] = await Promise.all([
    getVouchers({ pageSize: 200 }),
    getOffers({ pageSize: 200 }),
  ])

  if (voucherResult.success) {
    vouchers.value = voucherResult.data?.results ?? []
    totalItems.value = voucherResult.data?.pagination?.total ?? vouchers.value.length
  }
  else {
    vouchers.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load vouchers',
      description: voucherResult.error || 'Please try again.',
      color: 'error',
    })
  }

  if (offerResult.success)
    offers.value = offerResult.data?.results ?? []

  isLoading.value = false
}

async function submitVoucher() {
  saveError.value = ''
  const validationError = firstRequiredError([
    { label: 'Voucher name', value: form.name },
    { label: 'Voucher code', value: form.code },
    { label: 'Start date', value: form.start_datetime },
    { label: 'End date', value: form.end_datetime },
  ])
  if (validationError) {
    saveError.value = validationError
    return
  }

  isSaving.value = true
  const payload: VoucherPayload = {
    name: form.name.trim(),
    code: form.code.trim(),
    usage: form.usage,
    start_datetime: form.start_datetime,
    end_datetime: form.end_datetime,
  }
  const result = editingVoucher.value
    ? await updateVoucher(editingVoucher.value.id, payload)
    : await createVoucher(payload)

  if (result.success) {
    toast.add({
      title: editingVoucher.value ? 'Voucher updated' : 'Voucher created',
      description: `${payload.code} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadVouchers()
  }
  else {
    saveError.value = result.error || 'Could not save voucher.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function openVoucherDetail(voucher: VoucherItem) {
  selectedVoucher.value = voucher
  statsVoucher.value = null
  attachOfferId.value = null
  const result = await getVoucherStats(voucher.id)
  statsVoucher.value = result.success && result.data ? result.data : voucher
}

async function confirmDeleteVoucher() {
  if (!pendingDeleteVoucher.value)
    return

  isSaving.value = true
  const voucher = pendingDeleteVoucher.value
  const result = await deleteVoucher(voucher.id)

  if (result.success) {
    toast.add({ title: 'Voucher deleted', description: `${voucher.code} was removed.`, color: 'success' })
    pendingDeleteVoucher.value = null
    await loadVouchers()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete voucher.', color: 'error' })
  }

  isSaving.value = false
}

async function attachOffer() {
  if (!selectedVoucher.value || !attachOfferId.value)
    return

  isSaving.value = true
  const result = await attachVoucherOffer(selectedVoucher.value.id, attachOfferId.value)

  if (result.success && result.data) {
    toast.add({ title: 'Offer attached', color: 'success' })
    selectedVoucher.value = result.data
    statsVoucher.value = result.data
    attachOfferId.value = null
    await loadVouchers()
  }
  else {
    toast.add({ title: 'Attach failed', description: result.error || 'Could not attach offer.', color: 'error' })
  }

  isSaving.value = false
}

async function confirmDetachOffer() {
  if (!pendingDetach.value)
    return

  isSaving.value = true
  const { voucher, offer } = pendingDetach.value
  const result = await detachVoucherOffer(voucher.id, offer.id)

  if (result.success && result.data) {
    toast.add({ title: 'Offer removed', color: 'success' })
    selectedVoucher.value = result.data
    statsVoucher.value = result.data
    pendingDetach.value = null
    await loadVouchers()
  }
  else {
    toast.add({ title: 'Remove failed', description: result.error || 'Could not remove offer.', color: 'error' })
  }

  isSaving.value = false
}

onMounted(loadVouchers)
</script>

<template>
  <div>
    <AdminTableToolbar
      v-model:search="searchQuery"
      title="Vouchers"
      description="Create coupon codes, link offers, and monitor redemption totals."
      search-placeholder="Search vouchers..."
      create-label="New Voucher"
      :loading="isLoading"
      @refresh="loadVouchers"
      @create="openCreateVoucher"
    >
      <template #filters>
        <USelect v-model="usageFilter" :items="usageOptions" value-attribute="value" option-attribute="label" class="min-w-44" color="neutral" variant="outline" size="lg" />
        <USelect v-model="stateFilter" :items="stateOptions" value-attribute="value" option-attribute="label" class="min-w-40" color="neutral" variant="outline" size="lg" />
      </template>
    </AdminTableToolbar>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total vouchers" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-ticket-percent" :loading="isLoading" />
      <CardsKpiCard2 name="Active" :value="activeCount" :budget="totalItems" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Expired" :value="expiredCount" :budget="totalItems" color="#64748b" icon="i-lucide-clock" :loading="isLoading" />
      <CardsKpiCard2 name="Linked offers" :value="linkedOfferCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-badge-percent" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Voucher</div>
        <div class="col-span-2">Usage</div>
        <div class="col-span-1">State</div>
        <div class="col-span-1 text-right">Baskets</div>
        <div class="col-span-1 text-right">Orders</div>
        <div class="col-span-2">Window</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <AdminTableState
        :loading="isLoading"
        :empty="filteredVouchers.length === 0"
        loading-label="Loading vouchers"
        empty-icon="i-lucide-ticket-percent"
        empty-title="No vouchers found"
        empty-description="Try another search, clear the filters, or create a new voucher."
      >
        <div
          v-for="voucher in filteredVouchers"
          :key="voucher.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
        >
          <div class="col-span-3 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-ticket-percent" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ voucher.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ voucher.code }} / #{{ voucher.id }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-2"><UBadge color="info" variant="soft">{{ voucher.usage }}</UBadge></div>
          <div class="col-span-1"><UBadge :color="stateColor(voucher)" variant="soft">{{ formatState(voucher) }}</UBadge></div>
          <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ voucher.num_basket_additions }}</div>
          <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ voucher.num_orders }}</div>
          <div class="col-span-2 min-w-0 text-xs text-slate-500">
            <p class="truncate">{{ formatDate(voucher.start_datetime) }}</p>
            <p class="truncate">{{ formatDate(voucher.end_datetime) }}</p>
          </div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="View voucher">
              <UButton icon="i-lucide-eye" color="neutral" variant="ghost" square @click="openVoucherDetail(voucher)" />
            </UTooltip>
            <UTooltip text="Edit voucher">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditVoucher(voucher)" />
            </UTooltip>
            <UTooltip text="Delete voucher">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteVoucher = voucher" />
            </UTooltip>
          </div>
        </div>
      </AdminTableState>
    </div>

    <AdminTableFooter :shown="filteredVouchers.length" :total="totalItems" label="vouchers" />

    <AdminFormModal
      v-if="editorOpen"
      :title="editingVoucher ? 'Edit voucher' : 'New voucher'"
      description="Configure the coupon code and validity window."
      :error="saveError"
      :saving="isSaving"
      save-label="Save voucher"
      @close="editorOpen = false"
      @submit="submitVoucher"
    >
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <UFormField label="Name" required><UInput v-model="form.name" autocomplete="off" /></UFormField>
        <UFormField label="Code" required><UInput v-model="form.code" autocomplete="off" /></UFormField>
        <UFormField label="Usage" required><USelect v-model="form.usage" :items="usageFormOptions" value-attribute="value" option-attribute="label" /></UFormField>
        <div />
        <UFormField label="Start datetime" required><UInput v-model="form.start_datetime" type="datetime-local" /></UFormField>
        <UFormField label="End datetime" required><UInput v-model="form.end_datetime" type="datetime-local" /></UFormField>
      </div>
    </AdminFormModal>

    <div v-if="selectedVoucher" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[92vh] w-full max-w-3xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ selectedVoucher.name }}</h3>
              <p class="text-sm text-dimmed">{{ selectedVoucher.code }} / {{ selectedVoucher.usage }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="selectedVoucher = null" />
          </div>
        </template>

        <div class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-4">
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Baskets</p><p class="mt-1 font-semibold">{{ statsVoucher?.num_basket_additions ?? selectedVoucher.num_basket_additions }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Orders</p><p class="mt-1 font-semibold">{{ statsVoucher?.num_orders ?? selectedVoucher.num_orders }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Discount</p><p class="mt-1 font-semibold">{{ formatMoney(statsVoucher?.total_discount ?? selectedVoucher.total_discount) }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Offers</p><p class="mt-1 font-semibold">{{ selectedVoucher.offers?.length || 0 }}</p></div>
        </div>

        <div class="mb-4 flex flex-col gap-2 md:flex-row md:items-center">
          <USelect v-model="attachOfferId" :items="attachOfferOptions" value-attribute="value" option-attribute="label" class="min-w-0 flex-1" placeholder="Select offer to attach" />
          <UButton color="primary" variant="solid" :loading="isSaving" :disabled="!attachOfferId" @click="attachOffer">
            <UIcon name="i-lucide-link" />
            Attach Offer
          </UButton>
        </div>

        <div class="overflow-hidden rounded-lg border border-slate-200">
          <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
            <div class="col-span-5">Offer</div>
            <div class="col-span-3">Type</div>
            <div class="col-span-2">Status</div>
            <div class="col-span-2 text-right">Actions</div>
          </div>
          <div v-if="!selectedVoucher.offers?.length" class="p-8 text-center text-sm text-slate-500">No offers linked to this voucher.</div>
          <div v-for="offer in selectedVoucher.offers" :key="offer.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0">
            <div class="col-span-5 min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ offer.name }}</p>
              <p class="truncate text-xs text-slate-500">#{{ offer.id }}</p>
            </div>
            <div class="col-span-3 text-sm text-slate-600">{{ offer.offer_type }}</div>
            <div class="col-span-2"><UBadge color="info" variant="soft">{{ offer.status }}</UBadge></div>
            <div class="col-span-2 flex justify-end">
              <UButton icon="i-lucide-unlink" color="error" variant="ghost" square @click="pendingDetach = { voucher: selectedVoucher, offer }" />
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" @click="selectedVoucher = null">Close</UButton>
            <UButton color="primary" variant="solid" @click="openEditVoucher(selectedVoucher)">Edit voucher</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <AdminConfirmDialog
      v-if="pendingDeleteVoucher"
      title="Delete voucher"
      confirm-label="Delete voucher"
      icon="i-lucide-trash-2"
      :loading="isSaving"
      @cancel="pendingDeleteVoucher = null"
      @confirm="confirmDeleteVoucher"
    >
      <p class="text-sm text-default">Delete <span class="font-semibold">{{ pendingDeleteVoucher.code }}</span>?</p>
    </AdminConfirmDialog>

    <div v-if="pendingDetach" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Remove offer</h3></template>
        <p class="text-sm text-default">Remove <span class="font-semibold">{{ pendingDetach.offer.name }}</span> from this voucher?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDetach = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDetachOffer">Remove offer</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
