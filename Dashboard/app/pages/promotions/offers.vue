<script setup lang="ts">
import type {
  OfferBenefitItem,
  OfferComponentPayload,
  OfferConditionItem,
  OfferItem,
  OfferPayload,
} from '~/composables/useOffers'

const ALL_STATUSES = '__all_statuses__'
const ALL_TYPES = '__all_types__'

const toast = useToast()
const {
  createBenefit,
  createCondition,
  createOffer,
  deleteBenefit,
  deleteCondition,
  deleteOffer,
  getBenefits,
  getConditions,
  getOfferMeta,
  getOffers,
  updateBenefit,
  updateCondition,
  updateOffer,
  updateOfferStatus,
} = useOffers()

const offers = ref<OfferItem[]>([])
const conditions = ref<OfferConditionItem[]>([])
const benefits = ref<OfferBenefitItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const activeSection = ref<'offers' | 'conditions' | 'benefits'>('offers')
const searchQuery = ref('')
const statusFilter = ref(ALL_STATUSES)
const typeFilter = ref(ALL_TYPES)
const selectedOffer = ref<OfferItem | null>(null)
const editingOffer = ref<OfferItem | null>(null)
const editingCondition = ref<OfferConditionItem | null>(null)
const editingBenefit = ref<OfferBenefitItem | null>(null)
const pendingDelete = ref<{ kind: 'offer' | 'condition' | 'benefit', id: number, label: string } | null>(null)
const pendingStatusOffer = ref<OfferItem | null>(null)
const nextStatus = ref('')
const offerEditorOpen = ref(false)
const conditionEditorOpen = ref(false)
const benefitEditorOpen = ref(false)
const saveError = ref('')

const meta = reactive({
  offerTypes: [] as { label: string, value: string }[],
  offerStatuses: [] as { label: string, value: string }[],
  conditionTypes: [] as { label: string, value: string }[],
  benefitTypes: [] as { label: string, value: string }[],
})

const offerForm = reactive({
  name: '',
  slug: '',
  description: '',
  offer_type: '',
  status: '',
  priority: 0,
  exclusive: false,
  start_datetime: '',
  end_datetime: '',
  condition_id: null as number | null,
  benefit_id: null as number | null,
})

const conditionForm = reactive({
  type: '',
  range_id: null as number | null,
  value: '',
  proxy_class: '',
})

const benefitForm = reactive({
  type: '',
  range_id: null as number | null,
  value: '',
  max_affected_items: null as number | null,
  proxy_class: '',
})

const sectionOptions = [
  { label: 'Offers', value: 'offers', icon: 'i-lucide-badge-percent' },
  { label: 'Conditions', value: 'conditions', icon: 'i-lucide-list-checks' },
  { label: 'Benefits', value: 'benefits', icon: 'i-lucide-gift' },
] as const

const statusOptions = computed(() => [
  { label: 'All statuses', value: ALL_STATUSES },
  ...meta.offerStatuses,
])

const typeOptions = computed(() => [
  { label: 'All types', value: ALL_TYPES },
  ...meta.offerTypes,
])

const conditionSelectOptions = computed(() => conditions.value.map(condition => ({
  label: `#${condition.id} ${condition.name || condition.description || formatChoice(meta.conditionTypes, condition.type)}`,
  value: condition.id,
})))

const benefitSelectOptions = computed(() => benefits.value.map(benefit => ({
  label: `#${benefit.id} ${benefit.name || benefit.description || formatChoice(meta.benefitTypes, benefit.type)}`,
  value: benefit.id,
})))

const filteredOffers = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return offers.value.filter((offer) => {
    const matchesSearch = !search
      || offer.name.toLowerCase().includes(search)
      || offer.slug.toLowerCase().includes(search)
      || String(offer.id).includes(search)
      || String(offer.description || '').toLowerCase().includes(search)
    const matchesStatus = statusFilter.value === ALL_STATUSES || offer.status === statusFilter.value
    const matchesType = typeFilter.value === ALL_TYPES || offer.offer_type === typeFilter.value
    return matchesSearch && matchesStatus && matchesType
  })
})

const openOffersCount = computed(() => offers.value.filter(offer => normalizeStatus(offer.status) === 'open').length)
const suspendedOffersCount = computed(() => offers.value.filter(offer => normalizeStatus(offer.status) === 'suspended').length)
const voucherOffersCount = computed(() => offers.value.filter(offer => offer.voucher_ids?.length).length)

function normalizeStatus(status?: string) {
  return String(status || '').toLowerCase()
}

function formatChoice(choices: { label: string, value: string }[], value?: string | null) {
  return choices.find(choice => choice.value === value)?.label || value || 'Not set'
}

function statusColor(status?: string) {
  const value = normalizeStatus(status)
  if (value === 'open')
    return 'success'
  if (value === 'suspended')
    return 'warning'
  if (value === 'consumed')
    return 'neutral'
  return 'info'
}

function formatMoney(value?: string | number | null) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    maximumFractionDigits: 0,
  }).format(amount)
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

function toDateTimeInput(value?: string | null) {
  if (!value)
    return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime()))
    return ''

  return date.toISOString().slice(0, 16)
}

function blankToNull(value: string) {
  return value.trim() ? value.trim() : null
}

function resetOfferForm() {
  editingOffer.value = null
  saveError.value = ''
  offerForm.name = ''
  offerForm.slug = ''
  offerForm.description = ''
  offerForm.offer_type = meta.offerTypes[0]?.value || ''
  offerForm.status = meta.offerStatuses[0]?.value || 'Open'
  offerForm.priority = 0
  offerForm.exclusive = false
  offerForm.start_datetime = ''
  offerForm.end_datetime = ''
  offerForm.condition_id = conditions.value[0]?.id ?? null
  offerForm.benefit_id = benefits.value[0]?.id ?? null
}

function resetConditionForm() {
  editingCondition.value = null
  saveError.value = ''
  conditionForm.type = meta.conditionTypes[0]?.value || ''
  conditionForm.range_id = null
  conditionForm.value = ''
  conditionForm.proxy_class = ''
}

function resetBenefitForm() {
  editingBenefit.value = null
  saveError.value = ''
  benefitForm.type = meta.benefitTypes[0]?.value || ''
  benefitForm.range_id = null
  benefitForm.value = ''
  benefitForm.max_affected_items = null
  benefitForm.proxy_class = ''
}

function openCreateOffer() {
  resetOfferForm()
  offerEditorOpen.value = true
}

function openEditOffer(offer: OfferItem) {
  editingOffer.value = offer
  saveError.value = ''
  offerForm.name = offer.name
  offerForm.slug = offer.slug
  offerForm.description = offer.description || ''
  offerForm.offer_type = offer.offer_type
  offerForm.status = offer.status
  offerForm.priority = Number(offer.priority || 0)
  offerForm.exclusive = Boolean(offer.exclusive)
  offerForm.start_datetime = toDateTimeInput(offer.start_datetime)
  offerForm.end_datetime = toDateTimeInput(offer.end_datetime)
  offerForm.condition_id = offer.condition_id
  offerForm.benefit_id = offer.benefit_id
  offerEditorOpen.value = true
}

function openCreateCondition() {
  resetConditionForm()
  conditionEditorOpen.value = true
}

function openEditCondition(condition: OfferConditionItem) {
  editingCondition.value = condition
  saveError.value = ''
  conditionForm.type = condition.type
  conditionForm.range_id = condition.range_id
  conditionForm.value = String(condition.value ?? '')
  conditionForm.proxy_class = condition.proxy_class || ''
  conditionEditorOpen.value = true
}

function openCreateBenefit() {
  resetBenefitForm()
  benefitEditorOpen.value = true
}

function openEditBenefit(benefit: OfferBenefitItem) {
  editingBenefit.value = benefit
  saveError.value = ''
  benefitForm.type = benefit.type
  benefitForm.range_id = benefit.range_id
  benefitForm.value = String(benefit.value ?? '')
  benefitForm.max_affected_items = benefit.max_affected_items
  benefitForm.proxy_class = benefit.proxy_class || ''
  benefitEditorOpen.value = true
}

async function loadOffers() {
  isLoading.value = true
  const [metaResult, offersResult, conditionsResult, benefitsResult] = await Promise.all([
    getOfferMeta(),
    getOffers({ pageSize: 200 }),
    getConditions({ pageSize: 200 }),
    getBenefits({ pageSize: 200 }),
  ])

  if (metaResult.success && metaResult.data) {
    meta.offerTypes = metaResult.data.offer_types ?? []
    meta.offerStatuses = metaResult.data.offer_statuses ?? []
    meta.conditionTypes = metaResult.data.condition_types ?? []
    meta.benefitTypes = metaResult.data.benefit_types ?? []
  }

  if (offersResult.success) {
    offers.value = offersResult.data?.results ?? []
    totalItems.value = offersResult.data?.pagination?.total ?? offers.value.length
  }
  else {
    offers.value = []
    totalItems.value = 0
    toast.add({ title: 'Could not load offers', description: offersResult.error || 'Please try again.', color: 'error' })
  }

  if (conditionsResult.success)
    conditions.value = conditionsResult.data?.results ?? []

  if (benefitsResult.success)
    benefits.value = benefitsResult.data?.results ?? []

  if (!metaResult.success || !conditionsResult.success || !benefitsResult.success) {
    toast.add({
      title: 'Some promotion data could not load',
      description: metaResult.error || conditionsResult.error || benefitsResult.error || 'Please try again.',
      color: 'warning',
    })
  }

  isLoading.value = false
}

async function submitOffer() {
  saveError.value = ''
  if (!offerForm.name.trim()) {
    saveError.value = 'Offer name is required.'
    return
  }
  if (!offerForm.condition_id || !offerForm.benefit_id) {
    saveError.value = 'Select a condition and benefit before saving the offer.'
    return
  }

  isSaving.value = true
  const payload: OfferPayload = {
    name: offerForm.name.trim(),
    slug: offerForm.slug.trim() || undefined,
    description: offerForm.description.trim(),
    offer_type: offerForm.offer_type,
    status: offerForm.status,
    priority: Number(offerForm.priority || 0),
    exclusive: offerForm.exclusive,
    start_datetime: blankToNull(offerForm.start_datetime),
    end_datetime: blankToNull(offerForm.end_datetime),
    condition_id: offerForm.condition_id,
    benefit_id: offerForm.benefit_id,
  }

  const result = editingOffer.value
    ? await updateOffer(editingOffer.value.id, payload)
    : await createOffer(payload)

  if (result.success) {
    toast.add({
      title: editingOffer.value ? 'Offer updated' : 'Offer created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    offerEditorOpen.value = false
    resetOfferForm()
    await loadOffers()
  }
  else {
    saveError.value = result.error || 'Could not save offer.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function submitCondition() {
  saveError.value = ''
  if (!conditionForm.type) {
    saveError.value = 'Condition type is required.'
    return
  }

  isSaving.value = true
  const payload: OfferComponentPayload = {
    type: conditionForm.type,
    range_id: conditionForm.range_id,
    value: blankToNull(conditionForm.value),
    proxy_class: blankToNull(conditionForm.proxy_class),
  }
  const result = editingCondition.value
    ? await updateCondition(editingCondition.value.id, payload)
    : await createCondition(payload)

  if (result.success) {
    toast.add({ title: editingCondition.value ? 'Condition updated' : 'Condition created', color: 'success' })
    conditionEditorOpen.value = false
    resetConditionForm()
    await loadOffers()
  }
  else {
    saveError.value = result.error || 'Could not save condition.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function submitBenefit() {
  saveError.value = ''
  if (!benefitForm.type) {
    saveError.value = 'Benefit type is required.'
    return
  }

  isSaving.value = true
  const payload: OfferComponentPayload = {
    type: benefitForm.type,
    range_id: benefitForm.range_id,
    value: blankToNull(benefitForm.value),
    max_affected_items: benefitForm.max_affected_items,
    proxy_class: blankToNull(benefitForm.proxy_class),
  }
  const result = editingBenefit.value
    ? await updateBenefit(editingBenefit.value.id, payload)
    : await createBenefit(payload)

  if (result.success) {
    toast.add({ title: editingBenefit.value ? 'Benefit updated' : 'Benefit created', color: 'success' })
    benefitEditorOpen.value = false
    resetBenefitForm()
    await loadOffers()
  }
  else {
    saveError.value = result.error || 'Could not save benefit.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

function openStatusDialog(offer: OfferItem, status: string) {
  pendingStatusOffer.value = offer
  nextStatus.value = status
}

async function confirmStatusUpdate() {
  if (!pendingStatusOffer.value || !nextStatus.value)
    return

  isSaving.value = true
  const result = await updateOfferStatus(pendingStatusOffer.value.id, nextStatus.value)

  if (result.success) {
    toast.add({ title: 'Offer status updated', color: 'success' })
    pendingStatusOffer.value = null
    nextStatus.value = ''
    await loadOffers()
  }
  else {
    toast.add({ title: 'Update failed', description: result.error || 'Could not update offer status.', color: 'error' })
  }

  isSaving.value = false
}

async function confirmDelete() {
  if (!pendingDelete.value)
    return

  isSaving.value = true
  const target = pendingDelete.value
  const result = target.kind === 'offer'
    ? await deleteOffer(target.id)
    : target.kind === 'condition'
      ? await deleteCondition(target.id)
      : await deleteBenefit(target.id)

  if (result.success) {
    toast.add({ title: `${target.label} deleted`, color: 'success' })
    pendingDelete.value = null
    await loadOffers()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || `Could not delete ${target.label}.`, color: 'error' })
  }

  isSaving.value = false
}

onMounted(loadOffers)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Offers</h1>
        <p class="mt-1 text-sm text-slate-500">Manage Oscar conditional offers, their conditions, and benefits.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search offers..."
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
        <USelect
          v-model="typeFilter"
          :items="typeOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadOffers">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateOffer">
          <UIcon name="i-lucide-plus" />
          New Offer
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total offers" :value="totalItems" :budget="totalItems" color="#3d7cff" icon="i-lucide-badge-percent" :loading="isLoading" />
      <CardsKpiCard2 name="Open" :value="openOffersCount" :budget="totalItems" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Suspended" :value="suspendedOffersCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-pause-circle" :loading="isLoading" />
      <CardsKpiCard2 name="Voucher linked" :value="voucherOffersCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-ticket-percent" :loading="isLoading" />
    </div>

    <div class="mb-4 flex flex-wrap gap-2">
      <UButton
        v-for="section in sectionOptions"
        :key="section.value"
        :color="activeSection === section.value ? 'primary' : 'neutral'"
        :variant="activeSection === section.value ? 'solid' : 'outline'"
        @click="activeSection = section.value"
      >
        <UIcon :name="section.icon" />
        {{ section.label }}
      </UButton>
      <UButton v-if="activeSection === 'conditions'" color="primary" variant="solid" class="ml-auto" @click="openCreateCondition">
        <UIcon name="i-lucide-plus" />
        New Condition
      </UButton>
      <UButton v-if="activeSection === 'benefits'" color="primary" variant="solid" class="ml-auto" @click="openCreateBenefit">
        <UIcon name="i-lucide-plus" />
        New Benefit
      </UButton>
    </div>

    <div v-if="activeSection === 'offers'" class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Offer</div>
        <div class="col-span-2">Type</div>
        <div class="col-span-1">Status</div>
        <div class="col-span-2">Condition</div>
        <div class="col-span-2">Benefit</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading offers
      </div>

      <div v-else-if="filteredOffers.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-badge-percent" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No offers found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear filters, or create a new offer.</p>
      </div>

      <div
        v-for="offer in filteredOffers"
        v-else
        :key="offer.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-3 min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ offer.name }}</p>
          <p class="truncate text-xs text-slate-500">#{{ offer.id }} / {{ offer.slug || 'no-slug' }}</p>
        </div>
        <div class="col-span-2">
          <UBadge color="info" variant="soft">{{ formatChoice(meta.offerTypes, offer.offer_type) }}</UBadge>
        </div>
        <div class="col-span-1">
          <UBadge :color="statusColor(offer.status)" variant="soft">{{ formatChoice(meta.offerStatuses, offer.status) }}</UBadge>
        </div>
        <div class="col-span-2 min-w-0 text-sm text-slate-600">
          <p class="truncate">{{ offer.condition?.name || offer.condition?.description || 'No condition' }}</p>
          <p class="text-xs text-slate-400">{{ formatChoice(meta.conditionTypes, offer.condition?.type) }}</p>
        </div>
        <div class="col-span-2 min-w-0 text-sm text-slate-600">
          <p class="truncate">{{ offer.benefit?.name || offer.benefit?.description || 'No benefit' }}</p>
          <p class="text-xs text-slate-400">{{ formatChoice(meta.benefitTypes, offer.benefit?.type) }}</p>
        </div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="View offer">
            <UButton icon="i-lucide-eye" color="neutral" variant="ghost" square @click="selectedOffer = offer" />
          </UTooltip>
          <UTooltip text="Edit offer">
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditOffer(offer)" />
          </UTooltip>
          <UTooltip text="Suspend offer">
            <UButton icon="i-lucide-pause" color="warning" variant="ghost" square @click="openStatusDialog(offer, 'Suspended')" />
          </UTooltip>
          <UTooltip text="Delete offer">
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDelete = { kind: 'offer', id: offer.id, label: offer.name }" />
          </UTooltip>
        </div>
      </div>
    </div>

    <div v-else-if="activeSection === 'conditions'" class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-4">Condition</div>
        <div class="col-span-2">Type</div>
        <div class="col-span-2">Value</div>
        <div class="col-span-2">Range</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>
      <div v-for="condition in conditions" :key="condition.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50">
        <div class="col-span-4 min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ condition.name || condition.description }}</p>
          <p class="truncate text-xs text-slate-500">#{{ condition.id }}</p>
        </div>
        <div class="col-span-2"><UBadge color="info" variant="soft">{{ formatChoice(meta.conditionTypes, condition.type) }}</UBadge></div>
        <div class="col-span-2 text-sm font-semibold text-slate-700">{{ condition.value ?? 'Not set' }}</div>
        <div class="col-span-2 truncate text-sm text-slate-600">{{ condition.range_name || 'All products' }}</div>
        <div class="col-span-2 flex justify-end gap-1">
          <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditCondition(condition)" />
          <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDelete = { kind: 'condition', id: condition.id, label: 'Condition' }" />
        </div>
      </div>
    </div>

    <div v-else class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-4">Benefit</div>
        <div class="col-span-2">Type</div>
        <div class="col-span-2">Value</div>
        <div class="col-span-2">Range</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>
      <div v-for="benefit in benefits" :key="benefit.id" class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50">
        <div class="col-span-4 min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ benefit.name || benefit.description }}</p>
          <p class="truncate text-xs text-slate-500">#{{ benefit.id }} / max items {{ benefit.max_affected_items ?? 'not set' }}</p>
        </div>
        <div class="col-span-2"><UBadge color="info" variant="soft">{{ formatChoice(meta.benefitTypes, benefit.type) }}</UBadge></div>
        <div class="col-span-2 text-sm font-semibold text-slate-700">{{ benefit.value ?? 'Not set' }}</div>
        <div class="col-span-2 truncate text-sm text-slate-600">{{ benefit.range_name || 'All products' }}</div>
        <div class="col-span-2 flex justify-end gap-1">
          <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditBenefit(benefit)" />
          <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDelete = { kind: 'benefit', id: benefit.id, label: 'Benefit' }" />
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">
      Showing {{ activeSection === 'offers' ? filteredOffers.length : activeSection === 'conditions' ? conditions.length : benefits.length }} records.
    </p>

    <div v-if="offerEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[92vh] w-full max-w-3xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ editingOffer ? 'Edit offer' : 'New offer' }}</h3>
              <p class="text-sm text-dimmed">Choose an Oscar condition and benefit before saving.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="offerEditorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required><UInput v-model="offerForm.name" autocomplete="off" /></UFormField>
          <UFormField label="Slug"><UInput v-model="offerForm.slug" autocomplete="off" placeholder="Auto-generated when empty" /></UFormField>
          <UFormField label="Offer type" required><USelect v-model="offerForm.offer_type" :items="meta.offerTypes" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Status" required><USelect v-model="offerForm.status" :items="meta.offerStatuses" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Condition" required><USelect v-model="offerForm.condition_id" :items="conditionSelectOptions" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Benefit" required><USelect v-model="offerForm.benefit_id" :items="benefitSelectOptions" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Priority"><UInput v-model.number="offerForm.priority" type="number" /></UFormField>
          <label class="rounded-lg border border-slate-200 bg-white p-4">
            <UCheckbox v-model="offerForm.exclusive" label="Exclusive offer" />
          </label>
          <UFormField label="Start datetime"><UInput v-model="offerForm.start_datetime" type="datetime-local" /></UFormField>
          <UFormField label="End datetime"><UInput v-model="offerForm.end_datetime" type="datetime-local" /></UFormField>
          <UFormField label="Description" class="md:col-span-2"><UTextarea v-model="offerForm.description" :rows="4" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="offerEditorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitOffer">Save offer</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="conditionEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header><h3 class="font-semibold text-default">{{ editingCondition ? 'Edit condition' : 'New condition' }}</h3></template>
        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Condition type" required><USelect v-model="conditionForm.type" :items="meta.conditionTypes" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Value"><UInput v-model="conditionForm.value" autocomplete="off" /></UFormField>
          <UFormField label="Range ID"><UInput v-model.number="conditionForm.range_id" type="number" min="1" /></UFormField>
          <UFormField label="Proxy class"><UInput v-model="conditionForm.proxy_class" autocomplete="off" /></UFormField>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="conditionEditorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitCondition">Save condition</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="benefitEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header><h3 class="font-semibold text-default">{{ editingBenefit ? 'Edit benefit' : 'New benefit' }}</h3></template>
        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Benefit type" required><USelect v-model="benefitForm.type" :items="meta.benefitTypes" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Value"><UInput v-model="benefitForm.value" autocomplete="off" /></UFormField>
          <UFormField label="Range ID"><UInput v-model.number="benefitForm.range_id" type="number" min="1" /></UFormField>
          <UFormField label="Max affected items"><UInput v-model.number="benefitForm.max_affected_items" type="number" min="1" /></UFormField>
          <UFormField label="Proxy class" class="md:col-span-2"><UInput v-model="benefitForm.proxy_class" autocomplete="off" /></UFormField>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="benefitEditorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitBenefit">Save benefit</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="selectedOffer" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ selectedOffer.name }}</h3>
              <p class="text-sm text-dimmed">Offer #{{ selectedOffer.id }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="selectedOffer = null" />
          </div>
        </template>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Applications</p><p class="mt-1 font-semibold">{{ selectedOffer.num_applications }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Orders</p><p class="mt-1 font-semibold">{{ selectedOffer.num_orders }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Discount</p><p class="mt-1 font-semibold">{{ formatMoney(selectedOffer.total_discount) }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Vouchers</p><p class="mt-1 font-semibold">{{ selectedOffer.voucher_ids?.length || 0 }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Starts</p><p class="mt-1 font-semibold">{{ formatDate(selectedOffer.start_datetime) }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Ends</p><p class="mt-1 font-semibold">{{ formatDate(selectedOffer.end_datetime) }}</p></div>
        </div>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" @click="selectedOffer = null">Close</UButton>
            <UButton color="primary" variant="solid" @click="openEditOffer(selectedOffer)">Edit offer</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingStatusOffer" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Update offer status</h3></template>
        <p class="text-sm text-default">Mark <span class="font-semibold">{{ pendingStatusOffer.name }}</span> as {{ formatChoice(meta.offerStatuses, nextStatus) }}?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingStatusOffer = null">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="confirmStatusUpdate">Update status</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDelete" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete {{ pendingDelete.label }}</h3></template>
        <p class="text-sm text-default">This action may fail if Oscar records still depend on this item.</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDelete = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDelete">Delete</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
