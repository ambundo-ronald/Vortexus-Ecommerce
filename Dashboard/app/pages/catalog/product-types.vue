<script setup lang="ts">
import type { ProductTypeItem, ProductTypePayload } from '~/composables/useProductTypes'

const CAPABILITY_ALL = '__all_capabilities__'

const toast = useToast()
const { createProductType, deleteProductType, getProductTypes, updateProductType } = useProductTypes()

const productTypes = ref<ProductTypeItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const capabilityFilter = ref(CAPABILITY_ALL)
const editorOpen = ref(false)
const editingProductType = ref<ProductTypeItem | null>(null)
const pendingDeleteProductType = ref<ProductTypeItem | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  slug: '',
  requires_shipping: true,
  track_stock: true,
})

const capabilityOptions = [
  { label: 'All product types', value: CAPABILITY_ALL },
  { label: 'Requires shipping', value: 'requires_shipping' },
  { label: 'Tracks stock', value: 'track_stock' },
  { label: 'Digital/service', value: 'digital' },
]

const filteredProductTypes = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return productTypes.value.filter((productType) => {
    const matchesSearch = !search
      || productType.name.toLowerCase().includes(search)
      || productType.slug.toLowerCase().includes(search)
    const matchesCapability = capabilityFilter.value === CAPABILITY_ALL
      || (capabilityFilter.value === 'requires_shipping' && productType.requires_shipping)
      || (capabilityFilter.value === 'track_stock' && productType.track_stock)
      || (capabilityFilter.value === 'digital' && !productType.requires_shipping && !productType.track_stock)
    return matchesSearch && matchesCapability
  })
})

const shippingCount = computed(() => productTypes.value.filter(item => item.requires_shipping).length)
const stockCount = computed(() => productTypes.value.filter(item => item.track_stock).length)
const digitalCount = computed(() => productTypes.value.filter(item => !item.requires_shipping && !item.track_stock).length)

function resetForm() {
  editingProductType.value = null
  saveError.value = ''
  form.name = ''
  form.slug = ''
  form.requires_shipping = true
  form.track_stock = true
}

function openCreateProductType() {
  resetForm()
  editorOpen.value = true
}

function openEditProductType(productType: ProductTypeItem) {
  editingProductType.value = productType
  saveError.value = ''
  form.name = productType.name
  form.slug = productType.slug
  form.requires_shipping = productType.requires_shipping
  form.track_stock = productType.track_stock
  editorOpen.value = true
}

async function loadProductTypes() {
  isLoading.value = true
  const result = await getProductTypes({ pageSize: 100 })

  if (result.success) {
    productTypes.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? productTypes.value.length
  }
  else {
    productTypes.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load product types',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function submitProductType() {
  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Product type name is required.'
    return
  }

  isSaving.value = true
  const payload: ProductTypePayload = {
    name: form.name.trim(),
    slug: form.slug.trim() || undefined,
    requires_shipping: form.requires_shipping,
    track_stock: form.track_stock,
  }

  const result = editingProductType.value
    ? await updateProductType(editingProductType.value.id, payload)
    : await createProductType(payload)

  if (result.success) {
    toast.add({
      title: editingProductType.value ? 'Product type updated' : 'Product type created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadProductTypes()
  }
  else {
    saveError.value = result.error || 'Could not save product type.'
    toast.add({
      title: 'Save failed',
      description: saveError.value,
      color: 'error',
    })
  }

  isSaving.value = false
}

async function confirmDeleteProductType() {
  if (!pendingDeleteProductType.value)
    return

  const productType = pendingDeleteProductType.value
  isSaving.value = true
  const result = await deleteProductType(productType.id)

  if (result.success) {
    toast.add({
      title: 'Product type deleted',
      description: `${productType.name} was removed.`,
      color: 'success',
    })
    pendingDeleteProductType.value = null
    await loadProductTypes()
  }
  else {
    toast.add({
      title: 'Delete failed',
      description: result.error || 'Could not delete product type.',
      color: 'error',
    })
  }

  isSaving.value = false
}

onMounted(loadProductTypes)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Product Types</h1>
        <p class="mt-1 text-sm text-slate-500">Define the catalog classes that control shipping and stock behavior.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search product types..."
        />
        <USelect
          v-model="capabilityFilter"
          :items="capabilityOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-48"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadProductTypes">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateProductType">
          <UIcon name="i-lucide-plus" />
          New Type
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total types" :value="totalItems" :budget="totalItems" color="#3d7cff" icon="i-lucide-boxes" :loading="isLoading" />
      <CardsKpiCard2 name="Shipping" :value="shippingCount" :budget="totalItems" color="#059669" icon="i-lucide-truck" :loading="isLoading" />
      <CardsKpiCard2 name="Stock tracked" :value="stockCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-warehouse" :loading="isLoading" />
      <CardsKpiCard2 name="Digital/service" :value="digitalCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-cloud" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-5">Product type</div>
        <div class="col-span-3">Slug</div>
        <div class="col-span-2">Capabilities</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading product types
      </div>

      <div v-else-if="filteredProductTypes.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-package-search" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No product types found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear the filter, or create a new product type.</p>
      </div>

      <div
        v-for="productType in filteredProductTypes"
        v-else
        :key="productType.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-5 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              <UIcon name="i-lucide-boxes" />
            </div>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ productType.name }}</p>
              <p class="truncate text-xs text-slate-500">ID {{ productType.id }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-3 truncate text-sm text-slate-600">{{ productType.slug || 'No slug' }}</div>
        <div class="col-span-2 flex flex-wrap gap-1">
          <UBadge v-if="productType.requires_shipping" color="success" variant="soft">Shipping</UBadge>
          <UBadge v-if="productType.track_stock" color="info" variant="soft">Stock</UBadge>
          <UBadge v-if="!productType.requires_shipping && !productType.track_stock" color="warning" variant="soft">Digital</UBadge>
        </div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="Edit product type">
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditProductType(productType)" />
          </UTooltip>
          <UTooltip text="Delete product type">
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteProductType = productType" />
          </UTooltip>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">
      Showing {{ filteredProductTypes.length }} of {{ totalItems }} product types.
    </p>

    <div
      v-if="editorOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="max-h-[92vh] w-full max-w-2xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">
                {{ editingProductType ? 'Edit product type' : 'New product type' }}
              </h3>
              <p class="text-sm text-dimmed">Control how products in this class are fulfilled and stocked.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
          {{ saveError }}
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required>
            <UInput v-model="form.name" autocomplete="off" />
          </UFormField>
          <UFormField label="Slug">
            <UInput v-model="form.slug" autocomplete="off" placeholder="Auto-generated when empty" />
          </UFormField>
          <div class="md:col-span-2 grid grid-cols-1 gap-3 md:grid-cols-2">
            <label class="rounded-lg border border-slate-200 bg-white p-4">
              <UCheckbox v-model="form.requires_shipping" label="Requires shipping" />
              <p class="mt-2 text-sm text-slate-500">Products in this type need delivery or pickup fulfillment.</p>
            </label>
            <label class="rounded-lg border border-slate-200 bg-white p-4">
              <UCheckbox v-model="form.track_stock" label="Track stock" />
              <p class="mt-2 text-sm text-slate-500">Inventory records should be tracked for products in this type.</p>
            </label>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">
              Cancel
            </UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitProductType">
              Save product type
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div
      v-if="pendingDeleteProductType"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-error/10 p-2 text-error">
              <UIcon name="i-lucide-trash-2" />
            </div>
            <div>
              <h3 class="font-semibold text-default">Delete product type</h3>
              <p class="text-sm text-dimmed">Products using this type may block deletion.</p>
            </div>
          </div>
        </template>

        <p class="text-sm text-default">
          Delete <span class="font-semibold">{{ pendingDeleteProductType.name }}</span> from the catalogue?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteProductType = null">
              Cancel
            </UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteProductType">
              Delete product type
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
