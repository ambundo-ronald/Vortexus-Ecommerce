<script setup lang="ts">
import type { RangeItem, RangePayload, RangeProductItem } from '~/composables/useRanges'

const ALL_VISIBILITY = '__all_visibility__'
const ALL_SCOPE = '__all_scope__'

const toast = useToast()
const {
  addRangeProduct,
  createRange,
  deleteRange,
  getRangeProducts,
  getRanges,
  removeRangeProduct,
  updateRange,
} = useRanges()
const { getProducts } = useProduct()

const ranges = ref<RangeItem[]>([])
const rangeProducts = ref<RangeProductItem[]>([])
const productOptions = ref<{ label: string, value: number }[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const isLoadingProducts = ref(false)
const searchQuery = ref('')
const visibilityFilter = ref(ALL_VISIBILITY)
const scopeFilter = ref(ALL_SCOPE)
const editorOpen = ref(false)
const editingRange = ref<RangeItem | null>(null)
const selectedRange = ref<RangeItem | null>(null)
const pendingDeleteRange = ref<RangeItem | null>(null)
const pendingRemoveProduct = ref<RangeProductItem | null>(null)
const productSearch = ref('')
const selectedProductId = ref<number | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  slug: '',
  description: '',
  is_public: true,
  includes_all_products: false,
})

const visibilityOptions = [
  { label: 'All visibility', value: ALL_VISIBILITY },
  { label: 'Public', value: 'public' },
  { label: 'Private', value: 'private' },
]

const scopeOptions = [
  { label: 'All scopes', value: ALL_SCOPE },
  { label: 'All products', value: 'all' },
  { label: 'Selected products', value: 'selected' },
]

const filteredRanges = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return ranges.value.filter((range) => {
    const matchesSearch = !search
      || range.name.toLowerCase().includes(search)
      || range.slug.toLowerCase().includes(search)
      || String(range.id).includes(search)
      || String(range.description || '').toLowerCase().includes(search)
    const matchesVisibility = visibilityFilter.value === ALL_VISIBILITY
      || (visibilityFilter.value === 'public' && range.is_public)
      || (visibilityFilter.value === 'private' && !range.is_public)
    const matchesScope = scopeFilter.value === ALL_SCOPE
      || (scopeFilter.value === 'all' && range.includes_all_products)
      || (scopeFilter.value === 'selected' && !range.includes_all_products)
    return matchesSearch && matchesVisibility && matchesScope
  })
})

const publicCount = computed(() => ranges.value.filter(range => range.is_public).length)
const allProductCount = computed(() => ranges.value.filter(range => range.includes_all_products).length)
const assignedProductCount = computed(() => ranges.value.reduce((total, range) => total + Number(range.num_products || 0), 0))

function resetForm() {
  editingRange.value = null
  saveError.value = ''
  form.name = ''
  form.slug = ''
  form.description = ''
  form.is_public = true
  form.includes_all_products = false
}

function openCreateRange() {
  resetForm()
  editorOpen.value = true
}

function openEditRange(range: RangeItem) {
  editingRange.value = range
  saveError.value = ''
  form.name = range.name
  form.slug = range.slug
  form.description = range.description || ''
  form.is_public = range.is_public
  form.includes_all_products = range.includes_all_products
  editorOpen.value = true
}

async function loadRanges() {
  isLoading.value = true
  const result = await getRanges({ pageSize: 200 })

  if (result.success) {
    ranges.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? ranges.value.length
  }
  else {
    ranges.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load ranges',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function loadProducts() {
  isLoadingProducts.value = true
  const result = await getProducts({ pageSize: 50, search: productSearch.value.trim() })

  if (result.success) {
    productOptions.value = (result.data?.results ?? []).map((product: any) => ({
      label: `#${product.id} ${product.name || product.title || 'Untitled'}${product.sku ? ` / ${product.sku}` : ''}`,
      value: Number(product.id),
    }))
  }
  else {
    productOptions.value = []
    toast.add({
      title: 'Could not search products',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoadingProducts.value = false
}

async function loadRangeProducts(range: RangeItem) {
  selectedRange.value = range
  selectedProductId.value = null
  rangeProducts.value = []
  const result = await getRangeProducts(range.id)

  if (result.success)
    rangeProducts.value = result.data ?? []
  else
    toast.add({ title: 'Could not load range products', description: result.error || 'Please try again.', color: 'error' })

  await loadProducts()
}

async function submitRange() {
  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Range name is required.'
    return
  }

  isSaving.value = true
  const payload: RangePayload = {
    name: form.name.trim(),
    slug: form.slug.trim() || undefined,
    description: form.description.trim(),
    is_public: form.is_public,
    includes_all_products: form.includes_all_products,
  }
  const result = editingRange.value
    ? await updateRange(editingRange.value.id, payload)
    : await createRange(payload)

  if (result.success) {
    toast.add({
      title: editingRange.value ? 'Range updated' : 'Range created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadRanges()
  }
  else {
    saveError.value = result.error || 'Could not save range.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeleteRange() {
  if (!pendingDeleteRange.value)
    return

  isSaving.value = true
  const range = pendingDeleteRange.value
  const result = await deleteRange(range.id)

  if (result.success) {
    toast.add({ title: 'Range deleted', description: `${range.name} was removed.`, color: 'success' })
    pendingDeleteRange.value = null
    if (selectedRange.value?.id === range.id)
      selectedRange.value = null
    await loadRanges()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete range.', color: 'error' })
  }

  isSaving.value = false
}

async function addProductToRange() {
  if (!selectedRange.value || !selectedProductId.value)
    return

  isSaving.value = true
  const result = await addRangeProduct(selectedRange.value.id, selectedProductId.value)

  if (result.success) {
    toast.add({ title: 'Product added', color: 'success' })
    selectedProductId.value = null
    await loadRanges()
    await loadRangeProducts(result.data || selectedRange.value)
  }
  else {
    toast.add({ title: 'Add failed', description: result.error || 'Could not add product.', color: 'error' })
  }

  isSaving.value = false
}

async function confirmRemoveProduct() {
  if (!selectedRange.value || !pendingRemoveProduct.value)
    return

  isSaving.value = true
  const product = pendingRemoveProduct.value
  const result = await removeRangeProduct(selectedRange.value.id, product.id)

  if (result.success) {
    toast.add({ title: 'Product removed', color: 'success' })
    pendingRemoveProduct.value = null
    await loadRanges()
    await loadRangeProducts(result.data || selectedRange.value)
  }
  else {
    toast.add({ title: 'Remove failed', description: result.error || 'Could not remove product.', color: 'error' })
  }

  isSaving.value = false
}

watch(productSearch, async () => {
  if (selectedRange.value)
    await loadProducts()
})

onMounted(loadRanges)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Ranges</h1>
        <p class="mt-1 text-sm text-slate-500">Manage curated product collections used by offers and storefront merchandising.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search ranges..."
        />
        <USelect v-model="visibilityFilter" :items="visibilityOptions" value-attribute="value" option-attribute="label" class="min-w-40" color="neutral" variant="outline" size="lg" />
        <USelect v-model="scopeFilter" :items="scopeOptions" value-attribute="value" option-attribute="label" class="min-w-44" color="neutral" variant="outline" size="lg" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadRanges">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateRange">
          <UIcon name="i-lucide-plus" />
          New Range
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total ranges" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-layers-3" :loading="isLoading" />
      <CardsKpiCard2 name="Public" :value="publicCount" :budget="totalItems" color="#059669" icon="i-lucide-eye" :loading="isLoading" />
      <CardsKpiCard2 name="All products" :value="allProductCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-infinity" :loading="isLoading" />
      <CardsKpiCard2 name="Assigned products" :value="assignedProductCount" :budget="assignedProductCount" color="#f59e0b" icon="i-lucide-package-plus" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-4">Range</div>
          <div class="col-span-2">Visibility</div>
          <div class="col-span-2">Scope</div>
          <div class="col-span-2 text-right">Products</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading ranges
        </div>

        <div v-else-if="filteredRanges.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
            <UIcon name="i-lucide-layers-3" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No ranges found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another search, clear the filters, or create a new range.</p>
        </div>

        <div
          v-for="range in filteredRanges"
          v-else
          :key="range.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
        >
          <div class="col-span-4 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-layers-3" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ range.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ range.slug || 'No slug' }} / #{{ range.id }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-2">
            <UBadge :color="range.is_public ? 'success' : 'neutral'" variant="soft">{{ range.is_public ? 'Public' : 'Private' }}</UBadge>
          </div>
          <div class="col-span-2">
            <UBadge :color="range.includes_all_products ? 'info' : 'warning'" variant="soft">
              {{ range.includes_all_products ? 'All products' : 'Selected' }}
            </UBadge>
          </div>
          <div class="col-span-2 text-right text-sm font-semibold text-slate-700">{{ range.num_products }}</div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="Manage products">
              <UButton icon="i-lucide-package-plus" color="neutral" variant="ghost" square @click="loadRangeProducts(range)" />
            </UTooltip>
            <UTooltip text="Edit range">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditRange(range)" />
            </UTooltip>
            <UTooltip text="Delete range">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteRange = range" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Product Assignment</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedRange ? selectedRange.name : 'Select a range to manage products.' }}</p>
        </div>

        <div v-if="!selectedRange" class="p-8 text-center text-sm text-slate-500">
          Choose a range from the table to review assigned products.
        </div>

        <div v-else class="p-4">
          <div v-if="selectedRange.includes_all_products" class="mb-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-semibold text-blue-900">
            This range includes every product. Manual product assignment is optional and may not change storefront matching.
          </div>

          <div class="mb-4 grid grid-cols-1 gap-2">
            <UInput v-model="productSearch" color="neutral" variant="outline" icon="i-lucide-search" placeholder="Search products to add..." />
            <div class="flex gap-2">
              <USelect v-model="selectedProductId" :items="productOptions" value-attribute="value" option-attribute="label" class="min-w-0 flex-1" :loading="isLoadingProducts" placeholder="Select product" />
              <UButton color="primary" variant="solid" :loading="isSaving" :disabled="!selectedProductId" @click="addProductToRange">
                <UIcon name="i-lucide-plus" />
                Add
              </UButton>
            </div>
          </div>

          <div class="max-h-[420px] overflow-y-auto rounded-lg border border-slate-200">
            <div v-if="rangeProducts.length === 0" class="p-8 text-center text-sm text-slate-500">No products assigned.</div>
            <div v-for="product in rangeProducts" :key="product.id" class="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0">
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ product.title }}</p>
                <p class="truncate text-xs text-slate-500">#{{ product.id }} / {{ product.upc || 'No UPC' }}</p>
              </div>
              <UTooltip text="Remove product">
                <UButton icon="i-lucide-x" color="error" variant="ghost" square @click="pendingRemoveProduct = product" />
              </UTooltip>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredRanges.length }} of {{ totalItems }} ranges.</p>

    <div v-if="editorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[92vh] w-full max-w-2xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ editingRange ? 'Edit range' : 'New range' }}</h3>
              <p class="text-sm text-dimmed">Configure collection visibility and matching scope.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required><UInput v-model="form.name" autocomplete="off" /></UFormField>
          <UFormField label="Slug"><UInput v-model="form.slug" autocomplete="off" placeholder="Auto-generated when empty" /></UFormField>
          <label class="rounded-lg border border-slate-200 bg-white p-4">
            <UCheckbox v-model="form.is_public" label="Public range" />
          </label>
          <label class="rounded-lg border border-slate-200 bg-white p-4">
            <UCheckbox v-model="form.includes_all_products" label="Includes all products" />
          </label>
          <UFormField label="Description" class="md:col-span-2"><UTextarea v-model="form.description" :rows="4" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitRange">Save range</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDeleteRange" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete range</h3></template>
        <p class="text-sm text-default">Delete <span class="font-semibold">{{ pendingDeleteRange.name }}</span>? Offers using this range may block deletion.</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteRange = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteRange">Delete range</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingRemoveProduct" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Remove product</h3></template>
        <p class="text-sm text-default">Remove <span class="font-semibold">{{ pendingRemoveProduct.title }}</span> from this range?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingRemoveProduct = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmRemoveProduct">Remove product</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
