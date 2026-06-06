<script setup lang="ts">
import type { WeightBandItem, WeightBasedMethodItem, WeightBasedMethodPayload } from '~/composables/useShipping'

const toast = useToast()
const {
  createWeightBand,
  createWeightBasedMethod,
  deleteWeightBand,
  deleteWeightBasedMethod,
  getWeightBasedMethod,
  getWeightBasedMethods,
  updateWeightBand,
  updateWeightBasedMethod,
} = useShipping()

const methods = ref<WeightBasedMethodItem[]>([])
const selectedMethod = ref<WeightBasedMethodItem | null>(null)
const editingMethod = ref<WeightBasedMethodItem | null>(null)
const editingBand = ref<WeightBandItem | null>(null)
const pendingDeleteMethod = ref<WeightBasedMethodItem | null>(null)
const pendingDeleteBand = ref<WeightBandItem | null>(null)
const totalItems = ref(0)
const searchQuery = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const methodEditorOpen = ref(false)
const bandEditorOpen = ref(false)
const saveError = ref('')

const methodForm = reactive({
  name: '',
  code: '',
  description: '',
  default_weight: '0',
})

const bandForm = reactive({
  upper_limit: '',
  charge: '',
})

const filteredMethods = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return methods.value.filter((method) => {
    return !search
      || method.name.toLowerCase().includes(search)
      || method.code.toLowerCase().includes(search)
      || method.description.toLowerCase().includes(search)
      || String(method.id).includes(search)
  })
})

const bandCount = computed(() => methods.value.reduce((total, method) => total + Number(method.bands?.length || 0), 0))
const methodWithBandsCount = computed(() => methods.value.filter(method => Number(method.bands?.length || 0) > 0).length)
const averageDefaultWeight = computed(() => {
  if (!methods.value.length)
    return 0
  const total = methods.value.reduce((sum, method) => sum + Number(method.default_weight || 0), 0)
  return Number((total / methods.value.length).toFixed(3))
})

const sortedBands = computed(() => {
  return [...(selectedMethod.value?.bands || [])].sort((a, b) => Number(a.upper_limit || 0) - Number(b.upper_limit || 0))
})

function resetMethodForm() {
  editingMethod.value = null
  saveError.value = ''
  methodForm.name = ''
  methodForm.code = ''
  methodForm.description = ''
  methodForm.default_weight = '0'
}

function resetBandForm() {
  editingBand.value = null
  saveError.value = ''
  bandForm.upper_limit = ''
  bandForm.charge = ''
}

function formatMoney(value: number | string) {
  return new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(Number(value || 0))
}

function formatWeight(value: number | string) {
  return `${Number(value || 0).toLocaleString('en', { maximumFractionDigits: 3 })} kg`
}

async function loadMethods() {
  isLoading.value = true
  const result = await getWeightBasedMethods({ pageSize: 200 })

  if (result.success) {
    methods.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? methods.value.length
    if (selectedMethod.value) {
      selectedMethod.value = methods.value.find(method => method.id === selectedMethod.value?.id) || null
    }
  }
  else {
    methods.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load shipping methods',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function openMethod(method: WeightBasedMethodItem) {
  selectedMethod.value = method
  const result = await getWeightBasedMethod(method.id)

  if (result.success && result.data)
    selectedMethod.value = result.data
  else if (!result.success)
    toast.add({ title: 'Could not load method detail', description: result.error || 'Please try again.', color: 'error' })
}

function openCreateMethod() {
  resetMethodForm()
  methodEditorOpen.value = true
}

function openEditMethod(method: WeightBasedMethodItem) {
  editingMethod.value = method
  saveError.value = ''
  methodForm.name = method.name || ''
  methodForm.code = method.code || ''
  methodForm.description = method.description || ''
  methodForm.default_weight = String(method.default_weight ?? 0)
  methodEditorOpen.value = true
}

async function submitMethod() {
  saveError.value = ''
  if (!methodForm.name.trim()) {
    saveError.value = 'Method name is required.'
    return
  }

  isSaving.value = true
  const payload: WeightBasedMethodPayload = {
    name: methodForm.name.trim(),
    code: methodForm.code.trim() || undefined,
    description: methodForm.description.trim(),
    default_weight: methodForm.default_weight || '0',
  }
  const result = editingMethod.value
    ? await updateWeightBasedMethod(editingMethod.value.id, payload)
    : await createWeightBasedMethod(payload)

  if (result.success && result.data) {
    toast.add({ title: editingMethod.value ? 'Shipping method updated' : 'Shipping method created', color: 'success' })
    methodEditorOpen.value = false
    resetMethodForm()
    await loadMethods()
    await openMethod(result.data)
  }
  else {
    saveError.value = result.error || 'Could not save shipping method.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeleteMethod() {
  if (!pendingDeleteMethod.value)
    return

  isSaving.value = true
  const method = pendingDeleteMethod.value
  const result = await deleteWeightBasedMethod(method.id)

  if (result.success) {
    toast.add({ title: 'Shipping method deleted', description: `${method.name} was removed.`, color: 'success' })
    pendingDeleteMethod.value = null
    if (selectedMethod.value?.id === method.id)
      selectedMethod.value = null
    await loadMethods()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete shipping method.', color: 'error' })
  }

  isSaving.value = false
}

function openCreateBand() {
  if (!selectedMethod.value)
    return
  resetBandForm()
  bandEditorOpen.value = true
}

function openEditBand(band: WeightBandItem) {
  editingBand.value = band
  saveError.value = ''
  bandForm.upper_limit = String(band.upper_limit ?? '')
  bandForm.charge = String(band.charge ?? '')
  bandEditorOpen.value = true
}

async function submitBand() {
  if (!selectedMethod.value)
    return

  saveError.value = ''
  if (!bandForm.upper_limit || Number(bandForm.upper_limit) <= 0) {
    saveError.value = 'Upper limit must be greater than zero.'
    return
  }
  if (bandForm.charge === '' || Number(bandForm.charge) < 0) {
    saveError.value = 'Charge must be zero or greater.'
    return
  }

  isSaving.value = true
  const payload = {
    upper_limit: bandForm.upper_limit,
    charge: bandForm.charge,
  }
  const result = editingBand.value
    ? await updateWeightBand(selectedMethod.value.id, editingBand.value.id, payload)
    : await createWeightBand(selectedMethod.value.id, payload)

  if (result.success) {
    toast.add({ title: editingBand.value ? 'Band updated' : 'Band created', color: 'success' })
    bandEditorOpen.value = false
    resetBandForm()
    await loadMethods()
    if (selectedMethod.value)
      await openMethod(selectedMethod.value)
  }
  else {
    saveError.value = result.error || 'Could not save weight band.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeleteBand() {
  if (!selectedMethod.value || !pendingDeleteBand.value)
    return

  isSaving.value = true
  const band = pendingDeleteBand.value
  const result = await deleteWeightBand(selectedMethod.value.id, band.id)

  if (result.success) {
    toast.add({ title: 'Band deleted', color: 'success' })
    pendingDeleteBand.value = null
    await loadMethods()
    if (selectedMethod.value)
      await openMethod(selectedMethod.value)
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete weight band.', color: 'error' })
  }

  isSaving.value = false
}

onMounted(loadMethods)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Shipping</h1>
        <p class="mt-1 text-sm text-slate-500">Manage Oscar weight-based shipping methods and rate bands.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search methods..."
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadMethods">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateMethod">
          <UIcon name="i-lucide-plus" />
          New Method
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Methods" :value="totalItems" :budget="totalItems" color="#3d7cff" icon="i-lucide-truck" :loading="isLoading" />
      <CardsKpiCard2 name="With bands" :value="methodWithBandsCount" :budget="totalItems" color="#059669" icon="i-lucide-list-checks" :loading="isLoading" />
      <CardsKpiCard2 name="Rate bands" :value="bandCount" :budget="bandCount" color="#f59e0b" icon="i-lucide-route" :loading="isLoading" />
      <CardsKpiCard2 name="Avg default kg" :value="averageDefaultWeight" :budget="averageDefaultWeight" color="#7c3aed" icon="i-lucide-weight" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-5">Method</div>
          <div class="col-span-3">Default weight</div>
          <div class="col-span-2 text-right">Bands</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading shipping methods
        </div>

        <div v-else-if="filteredMethods.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
            <UIcon name="i-lucide-truck" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No shipping methods found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another search or create a weight-based method.</p>
        </div>

        <div
          v-for="method in filteredMethods"
          v-else
          :key="method.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
          :class="{ 'bg-blue-50/60': selectedMethod?.id === method.id }"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-truck" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ method.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ method.code || 'No code' }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-3 text-sm font-semibold text-slate-700">{{ formatWeight(method.default_weight) }}</div>
          <div class="col-span-2 text-right text-sm font-semibold text-slate-700">{{ method.bands?.length || 0 }}</div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="Manage bands">
              <UButton icon="i-lucide-list-plus" color="neutral" variant="ghost" square @click="openMethod(method)" />
            </UTooltip>
            <UTooltip text="Edit method">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditMethod(method)" />
            </UTooltip>
            <UTooltip text="Delete method">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteMethod = method" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Weight Bands</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedMethod ? selectedMethod.name : 'Select a method to manage rate bands.' }}</p>
        </div>

        <div v-if="!selectedMethod" class="p-8 text-center text-sm text-slate-500">
          Choose a shipping method from the table to add, edit, or delete weight bands.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-lg font-black text-slate-950">{{ selectedMethod.name }}</p>
              <p class="truncate text-sm text-slate-500">{{ selectedMethod.description || 'No description' }}</p>
            </div>
            <UButton color="primary" variant="solid" size="sm" @click="openCreateBand">
              <UIcon name="i-lucide-plus" />
              Band
            </UButton>
          </div>

          <div class="overflow-hidden rounded-lg border border-slate-200">
            <div class="grid grid-cols-12 gap-2 border-b border-slate-200 bg-slate-50 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              <div class="col-span-5">Upper Limit</div>
              <div class="col-span-4">Charge</div>
              <div class="col-span-3 text-right">Actions</div>
            </div>
            <div v-if="sortedBands.length === 0" class="p-8 text-center text-sm text-slate-500">No bands configured.</div>
            <div v-for="band in sortedBands" :key="band.id" class="grid grid-cols-12 items-center gap-2 border-b border-slate-100 px-3 py-3 last:border-b-0">
              <div class="col-span-5 text-sm font-semibold text-slate-950">{{ formatWeight(band.upper_limit) }}</div>
              <div class="col-span-4 text-sm font-semibold text-slate-700">{{ formatMoney(band.charge) }}</div>
              <div class="col-span-3 flex justify-end gap-1">
                <UTooltip text="Edit band">
                  <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditBand(band)" />
                </UTooltip>
                <UTooltip text="Delete band">
                  <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteBand = band" />
                </UTooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredMethods.length }} of {{ totalItems }} shipping methods.</p>

    <div v-if="methodEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ editingMethod ? 'Edit shipping method' : 'New shipping method' }}</h3>
              <p class="text-sm text-dimmed">Configure an Oscar weight-based shipping method.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="methodEditorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required><UInput v-model="methodForm.name" autocomplete="off" /></UFormField>
          <UFormField label="Code"><UInput v-model="methodForm.code" autocomplete="off" placeholder="Auto-generated when empty" /></UFormField>
          <UFormField label="Default weight"><UInput v-model="methodForm.default_weight" type="number" min="0" step="0.001" /></UFormField>
          <UFormField label="Description" class="md:col-span-2"><UTextarea v-model="methodForm.description" :rows="4" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="methodEditorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitMethod">Save method</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="bandEditorOpen && selectedMethod" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ editingBand ? 'Edit weight band' : 'New weight band' }}</h3>
              <p class="text-sm text-dimmed">{{ selectedMethod.name }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="bandEditorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4">
          <UFormField label="Upper limit" required><UInput v-model="bandForm.upper_limit" type="number" min="0.001" step="0.001" /></UFormField>
          <UFormField label="Charge" required><UInput v-model="bandForm.charge" type="number" min="0" step="0.01" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="bandEditorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitBand">Save band</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDeleteMethod" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete shipping method</h3></template>
        <p class="text-sm text-default">Delete <span class="font-semibold">{{ pendingDeleteMethod.name }}</span> and its weight bands?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteMethod = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteMethod">Delete method</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDeleteBand" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete weight band</h3></template>
        <p class="text-sm text-default">Delete the band up to <span class="font-semibold">{{ formatWeight(pendingDeleteBand.upper_limit) }}</span>?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteBand = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteBand">Delete band</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
