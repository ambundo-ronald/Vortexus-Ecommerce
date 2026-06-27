<script setup lang="ts">
import type { AttributeItem, AttributePayload } from '~/composables/useAttributes'
import type { ProductTypeItem } from '~/composables/useProductTypes'

const ALL_TYPES = '__all_types__'
const ALL_PRODUCT_TYPES = '__all_product_types__'

const toast = useToast()
const { createAttribute, deleteAttribute, getAttributes, updateAttribute } = useAttributes()
const { getProductTypes } = useProductTypes()

const attributes = ref<AttributeItem[]>([])
const productTypes = ref<ProductTypeItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const typeFilter = ref(ALL_TYPES)
const productTypeFilter = ref(ALL_PRODUCT_TYPES)
const editorOpen = ref(false)
const editingAttribute = ref<AttributeItem | null>(null)
const pendingDeleteAttribute = ref<AttributeItem | null>(null)
const saveError = ref('')

const form = reactive({
  product_class_id: '',
  parent_attribute_id: '',
  name: '',
  code: '',
  type: 'text',
  uom: '',
  required: false,
})

const attributeTypeOptions = [
  { label: 'Text', value: 'text' },
  { label: 'Integer', value: 'integer' },
  { label: 'Boolean', value: 'boolean' },
  { label: 'Float', value: 'float' },
  { label: 'UOM', value: 'uom' },
  { label: 'Rich text', value: 'richtext' },
  { label: 'Date', value: 'date' },
  { label: 'Datetime', value: 'datetime' },
  { label: 'Option', value: 'option' },
  { label: 'Multi option', value: 'multi_option' },
  { label: 'File', value: 'file' },
  { label: 'Image', value: 'image' },
]

const typeFilterOptions = computed(() => [
  { label: 'All types', value: ALL_TYPES },
  ...attributeTypeOptions,
])

const productTypeOptions = computed(() => [
  { label: 'Select product type', value: '__select_product_type__', disabled: true },
  ...productTypes.value.map(productType => ({
    label: productType.name,
    value: String(productType.id),
  })),
])

const productTypeFilterOptions = computed(() => [
  { label: 'All product types', value: ALL_PRODUCT_TYPES },
  ...productTypes.value.map(productType => ({
    label: productType.name,
    value: String(productType.id),
  })),
])

const parentAttributeOptions = computed(() => [
  { label: 'No parent attribute', value: '__no_parent__' },
  ...attributes.value
    .filter(attribute =>
      String(attribute.product_class_id) === String(form.product_class_id)
      && (!editingAttribute.value || attribute.id !== editingAttribute.value.id),
    )
    .map(attribute => ({
      label: `${attribute.name} (${attribute.code})`,
      value: String(attribute.id),
    })),
])

const filteredAttributes = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return attributes.value.filter((attribute) => {
    const productTypeName = getProductTypeName(attribute.product_class_id).toLowerCase()
    const matchesSearch = !search
      || attribute.name.toLowerCase().includes(search)
      || attribute.code.toLowerCase().includes(search)
      || (attribute.parent_attribute_name || '').toLowerCase().includes(search)
      || (attribute.uom || '').toLowerCase().includes(search)
      || productTypeName.includes(search)
    const matchesType = typeFilter.value === ALL_TYPES || attribute.type === typeFilter.value
    const matchesProductType = productTypeFilter.value === ALL_PRODUCT_TYPES || String(attribute.product_class_id) === productTypeFilter.value
    return matchesSearch && matchesType && matchesProductType
  })
})

const requiredCount = computed(() => attributes.value.filter(item => item.required).length)
const optionalCount = computed(() => attributes.value.filter(item => !item.required).length)
const assignedProductTypeCount = computed(() => new Set(attributes.value.map(item => item.product_class_id)).size)

function getProductTypeName(id: number) {
  return productTypes.value.find(productType => productType.id === id)?.name || `Type ${id}`
}

function getTypeLabel(value: string) {
  return attributeTypeOptions.find(option => option.value === value)?.label || value
}

function resetForm() {
  editingAttribute.value = null
  saveError.value = ''
  form.product_class_id = productTypes.value[0]?.id ? String(productTypes.value[0].id) : ''
  form.parent_attribute_id = '__no_parent__'
  form.name = ''
  form.code = ''
  form.type = 'text'
  form.uom = ''
  form.required = false
}

function openCreateAttribute() {
  resetForm()
  editorOpen.value = true
}

function openEditAttribute(attribute: AttributeItem) {
  editingAttribute.value = attribute
  saveError.value = ''
  form.product_class_id = String(attribute.product_class_id)
  form.parent_attribute_id = attribute.parent_attribute_id ? String(attribute.parent_attribute_id) : '__no_parent__'
  form.name = attribute.name
  form.code = attribute.code
  form.type = attribute.type
  form.uom = attribute.uom || ''
  form.required = attribute.required
  editorOpen.value = true
}

async function loadProductTypes() {
  const result = await getProductTypes({ pageSize: 200 })
  if (result.success)
    productTypes.value = result.data?.results ?? []
  else
    productTypes.value = []
}

async function loadAttributes() {
  isLoading.value = true
  await loadProductTypes()
  const result = await getAttributes({ pageSize: 200 })

  if (result.success) {
    attributes.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? attributes.value.length
  }
  else {
    attributes.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load attributes',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function submitAttribute() {
  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Attribute name is required.'
    return
  }
  if (!form.product_class_id) {
    saveError.value = 'Select a product type before saving.'
    return
  }

  isSaving.value = true
  const payload: AttributePayload = {
    product_class_id: Number(form.product_class_id),
    name: form.name.trim(),
    code: form.code.trim() || undefined,
    type: form.type,
    parent_attribute_id: form.parent_attribute_id && form.parent_attribute_id !== '__no_parent__'
      ? Number(form.parent_attribute_id)
      : null,
    uom: form.type === 'uom' ? form.uom.trim() : '',
    required: form.required,
  }

  const result = editingAttribute.value
    ? await updateAttribute(editingAttribute.value.id, {
        name: payload.name,
        code: payload.code,
        type: payload.type,
        parent_attribute_id: payload.parent_attribute_id,
        uom: payload.uom,
        required: payload.required,
      })
    : await createAttribute(payload)

  if (result.success) {
    toast.add({
      title: editingAttribute.value ? 'Attribute updated' : 'Attribute created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadAttributes()
  }
  else {
    saveError.value = result.error || 'Could not save attribute.'
    toast.add({
      title: 'Save failed',
      description: saveError.value,
      color: 'error',
    })
  }

  isSaving.value = false
}

async function confirmDeleteAttribute() {
  if (!pendingDeleteAttribute.value)
    return

  const attribute = pendingDeleteAttribute.value
  isSaving.value = true
  const result = await deleteAttribute(attribute.id)

  if (result.success) {
    toast.add({
      title: 'Attribute deleted',
      description: `${attribute.name} was removed.`,
      color: 'success',
    })
    pendingDeleteAttribute.value = null
    await loadAttributes()
  }
  else {
    toast.add({
      title: 'Delete failed',
      description: result.error || 'Could not delete attribute.',
      color: 'error',
    })
  }

  isSaving.value = false
}

onMounted(loadAttributes)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Product Attributes</h1>
        <p class="mt-1 text-sm text-slate-500">Manage reusable product fields attached to catalog product types.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search attributes..."
        />
        <USelect
          v-model="productTypeFilter"
          :items="productTypeFilterOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-48"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <USelect
          v-model="typeFilter"
          :items="typeFilterOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadAttributes">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateAttribute">
          <UIcon name="i-lucide-plus" />
          New Attribute
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total attributes" :value="totalItems" :budget="totalItems" color="#3d7cff" icon="i-lucide-list-plus" :loading="isLoading" />
      <CardsKpiCard2 name="Required" :value="requiredCount" :budget="totalItems" color="#dc2626" icon="i-lucide-circle-alert" :loading="isLoading" />
      <CardsKpiCard2 name="Optional" :value="optionalCount" :budget="totalItems" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Product types used" :value="assignedProductTypeCount" :budget="productTypes.length" color="#7c3aed" icon="i-lucide-boxes" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Attribute</div>
        <div class="col-span-2">Parent</div>
        <div class="col-span-2">Product type</div>
        <div class="col-span-2">Data type</div>
        <div class="col-span-1">Required</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading attributes
      </div>

      <div v-else-if="filteredAttributes.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-list-plus" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No attributes found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear the filters, or create a new attribute.</p>
      </div>

      <div
        v-for="attribute in filteredAttributes"
        v-else
        :key="attribute.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-3 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              <UIcon name="i-lucide-list-plus" />
            </div>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ attribute.name }}</p>
              <p class="truncate text-xs text-slate-500">{{ attribute.code || 'No code' }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2 truncate text-sm text-slate-600">
          {{ attribute.parent_attribute_name || 'None' }}
        </div>
        <div class="col-span-2 truncate text-sm text-slate-600">{{ getProductTypeName(attribute.product_class_id) }}</div>
        <div class="col-span-2">
          <UBadge color="info" variant="soft">{{ getTypeLabel(attribute.type) }}{{ attribute.uom ? ` · ${attribute.uom}` : '' }}</UBadge>
        </div>
        <div class="col-span-1">
          <UBadge :color="attribute.required ? 'error' : 'neutral'" variant="soft">
            {{ attribute.required ? 'Yes' : 'No' }}
          </UBadge>
        </div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="Edit attribute">
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditAttribute(attribute)" />
          </UTooltip>
          <UTooltip text="Delete attribute">
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteAttribute = attribute" />
          </UTooltip>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">
      Showing {{ filteredAttributes.length }} of {{ totalItems }} attributes.
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
                {{ editingAttribute ? 'Edit attribute' : 'New attribute' }}
              </h3>
              <p class="text-sm text-dimmed">Attach structured fields to a product type.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
          {{ saveError }}
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Product type" required>
            <USelect
              v-model="form.product_class_id"
              :items="productTypeOptions"
              value-attribute="value"
              option-attribute="label"
              :disabled="Boolean(editingAttribute)"
            />
            <p v-if="editingAttribute" class="mt-1 text-xs text-dimmed">
              Product type changes are not supported by the current backend endpoint.
            </p>
          </UFormField>
          <UFormField label="Data type" required>
            <USelect
              v-model="form.type"
              :items="attributeTypeOptions"
              value-attribute="value"
              option-attribute="label"
            />
          </UFormField>
          <UFormField label="Parent attribute">
            <USelect
              v-model="form.parent_attribute_id"
              :items="parentAttributeOptions"
              value-attribute="value"
              option-attribute="label"
            />
          </UFormField>
          <UFormField v-if="form.type === 'uom'" label="UOM" required>
            <UInput v-model="form.uom" autocomplete="off" placeholder="e.g. LPM, bar, mm, kg" />
          </UFormField>
          <UFormField label="Name" required>
            <UInput v-model="form.name" autocomplete="off" />
          </UFormField>
          <UFormField label="Code">
            <UInput v-model="form.code" autocomplete="off" placeholder="Auto-generated when empty" />
          </UFormField>
          <label class="rounded-lg border border-slate-200 bg-white p-4 md:col-span-2">
            <UCheckbox v-model="form.required" label="Required for products in this type" />
            <p class="mt-2 text-sm text-slate-500">Required attributes should be filled before products are published.</p>
          </label>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">
              Cancel
            </UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitAttribute">
              Save attribute
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div
      v-if="pendingDeleteAttribute"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-error/10 p-2 text-error">
              <UIcon name="i-lucide-trash-2" />
            </div>
            <div>
              <h3 class="font-semibold text-default">Delete attribute</h3>
              <p class="text-sm text-dimmed">Products using this attribute may block deletion.</p>
            </div>
          </div>
        </template>

        <p class="text-sm text-default">
          Delete <span class="font-semibold">{{ pendingDeleteAttribute.name }}</span> from the catalogue?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteAttribute = null">
              Cancel
            </UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteAttribute">
              Delete attribute
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
