<script setup lang="ts">
import type { CategoryItem, CategoryPayload } from '~/composables/useCategories'

const ALL_VISIBILITY = '__all_visibility__'
const ROOT_PARENT = '__root__'

const toast = useToast()
const { createCategory, deleteCategory, getCategories, updateCategory } = useCategories()
const { firstRequiredError } = useAdminForm()

const categories = ref<CategoryItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const visibilityFilter = ref(ALL_VISIBILITY)
const editorOpen = ref(false)
const editingCategory = ref<CategoryItem | null>(null)
const pendingDeleteCategory = ref<CategoryItem | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  slug: '',
  description: '',
  is_public: true,
  parent_id: ROOT_PARENT as string,
})

const visibilityOptions = [
  { label: 'All categories', value: ALL_VISIBILITY },
  { label: 'Public', value: 'public' },
  { label: 'Hidden', value: 'hidden' },
]

const parentOptions = computed(() => [
  { label: 'Root category', value: ROOT_PARENT },
  ...categories.value
    .filter(category => category.id !== editingCategory.value?.id)
    .map(category => ({
      label: `${'--'.repeat(Math.max(category.depth - 1, 0))} ${category.name}`.trim(),
      value: String(category.id),
    })),
])

const filteredCategories = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return categories.value.filter((category) => {
    const matchesSearch = !search
      || category.name.toLowerCase().includes(search)
      || category.slug.toLowerCase().includes(search)
      || category.description.toLowerCase().includes(search)
    const matchesVisibility = visibilityFilter.value === ALL_VISIBILITY
      || (visibilityFilter.value === 'public' && category.is_public)
      || (visibilityFilter.value === 'hidden' && !category.is_public)
    return matchesSearch && matchesVisibility
  })
})

const rootCount = computed(() => categories.value.filter(category => !category.parent_id).length)
const publicCount = computed(() => categories.value.filter(category => category.is_public).length)
const hiddenCount = computed(() => categories.value.filter(category => !category.is_public).length)
const childCount = computed(() => categories.value.filter(category => category.parent_id).length)

function resetForm() {
  editingCategory.value = null
  saveError.value = ''
  form.name = ''
  form.slug = ''
  form.description = ''
  form.is_public = true
  form.parent_id = ROOT_PARENT
}

function openCreateCategory(parent?: CategoryItem) {
  resetForm()
  if (parent)
    form.parent_id = String(parent.id)
  editorOpen.value = true
}

function openEditCategory(category: CategoryItem) {
  editingCategory.value = category
  saveError.value = ''
  form.name = category.name
  form.slug = category.slug
  form.description = category.description
  form.is_public = category.is_public
  form.parent_id = category.parent_id ? String(category.parent_id) : ROOT_PARENT
  editorOpen.value = true
}

function categoryIndent(category: CategoryItem) {
  return `${Math.max(category.depth - 1, 0) * 1.5}rem`
}

function formatParent(category: CategoryItem) {
  if (!category.parent_id)
    return 'Root'
  return categories.value.find(item => item.id === category.parent_id)?.name || 'Parent'
}

async function loadCategories() {
  isLoading.value = true
  const result = await getCategories({ pageSize: 200 })

  if (result.success) {
    categories.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? categories.value.length
  }
  else {
    categories.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load categories',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function submitCategory() {
  saveError.value = ''
  const validationError = firstRequiredError([
    { label: 'Category name', value: form.name },
  ])
  if (validationError) {
    saveError.value = validationError
    return
  }

  isSaving.value = true
  const payload: CategoryPayload = {
    name: form.name.trim(),
    slug: form.slug.trim() || undefined,
    description: form.description.trim(),
    is_public: form.is_public,
    parent_id: form.parent_id === ROOT_PARENT ? null : Number(form.parent_id),
  }

  const result = editingCategory.value
    ? await updateCategory(editingCategory.value.id, {
        name: payload.name,
        slug: payload.slug,
        description: payload.description,
        is_public: payload.is_public,
      })
    : await createCategory(payload)

  if (result.success) {
    toast.add({
      title: editingCategory.value ? 'Category updated' : 'Category created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadCategories()
  }
  else {
    saveError.value = result.error || 'Could not save category.'
    toast.add({
      title: 'Save failed',
      description: saveError.value,
      color: 'error',
    })
  }

  isSaving.value = false
}

async function confirmDeleteCategory() {
  if (!pendingDeleteCategory.value)
    return

  const category = pendingDeleteCategory.value
  isSaving.value = true
  const result = await deleteCategory(category.id)

  if (result.success) {
    toast.add({
      title: 'Category deleted',
      description: `${category.name} was removed.`,
      color: 'success',
    })
    pendingDeleteCategory.value = null
    await loadCategories()
  }
  else {
    toast.add({
      title: 'Delete failed',
      description: result.error || 'Could not delete category.',
      color: 'error',
    })
  }

  isSaving.value = false
}

onMounted(loadCategories)
</script>

<template>
  <div>
    <AdminTableToolbar
      v-model:search="searchQuery"
      title="Catalog Categories"
      description="Manage the storefront category tree used for product browsing."
      search-placeholder="Search categories..."
      create-label="New Category"
      :loading="isLoading"
      @refresh="loadCategories"
      @create="openCreateCategory()"
    >
      <template #filters>
        <USelect
          v-model="visibilityFilter"
          :items="visibilityOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />
      </template>
    </AdminTableToolbar>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total categories" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-folder-tree" :loading="isLoading" />
      <CardsKpiCard2 name="Root categories" :value="rootCount" :budget="totalItems" color="#059669" icon="i-lucide-folder" :loading="isLoading" />
      <CardsKpiCard2 name="Child categories" :value="childCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-network" :loading="isLoading" />
      <CardsKpiCard2 name="Hidden" :value="hiddenCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-eye-off" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-5">Category</div>
        <div class="col-span-2">Parent</div>
        <div class="col-span-2">Visibility</div>
        <div class="col-span-1 text-right">Children</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <AdminTableState
        :loading="isLoading"
        :empty="filteredCategories.length === 0"
        loading-label="Loading categories"
        empty-icon="i-lucide-folder-search"
        empty-title="No categories found"
        empty-description="Try another search, clear the filter, or create a root category."
      >
        <div
          v-for="category in filteredCategories"
          :key="category.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3" :style="{ paddingLeft: categoryIndent(category) }">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon :name="category.numchild ? 'i-lucide-folder-tree' : 'i-lucide-folder'" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ category.name }}</p>
                <p class="truncate text-xs text-slate-500">{{ category.slug || 'No slug' }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-2 truncate text-sm text-slate-600">{{ formatParent(category) }}</div>
          <div class="col-span-2">
            <UBadge :color="category.is_public ? 'success' : 'warning'" variant="soft">
              {{ category.is_public ? 'Public' : 'Hidden' }}
            </UBadge>
          </div>
          <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ category.numchild }}</div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="Add child category">
              <UButton icon="i-lucide-plus" color="neutral" variant="ghost" square @click="openCreateCategory(category)" />
            </UTooltip>
            <UTooltip text="Edit category">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditCategory(category)" />
            </UTooltip>
            <UTooltip text="Delete category">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteCategory = category" />
            </UTooltip>
          </div>
        </div>
      </AdminTableState>
    </div>

    <AdminTableFooter
      :shown="filteredCategories.length"
      :total="totalItems"
      label="categories"
      note="Editing a category keeps its current parent."
    />

    <AdminFormModal
      v-if="editorOpen"
      :title="editingCategory ? 'Edit category' : 'New category'"
      description="Create and maintain storefront category structure."
      :error="saveError"
      :saving="isSaving"
      save-label="Save category"
      @close="editorOpen = false"
      @submit="submitCategory"
    >
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <UFormField label="Name" required>
          <UInput v-model="form.name" autocomplete="off" />
        </UFormField>
        <UFormField label="Slug">
          <UInput v-model="form.slug" autocomplete="off" placeholder="Auto-generated when empty" />
        </UFormField>
        <UFormField label="Parent">
          <USelect
            v-model="form.parent_id"
            :items="parentOptions"
            value-attribute="value"
            option-attribute="label"
            :disabled="Boolean(editingCategory)"
          />
          <p v-if="editingCategory" class="mt-1 text-xs text-dimmed">
            Parent changes are not supported by the current backend endpoint.
          </p>
        </UFormField>
        <UFormField label="Visibility">
          <UCheckbox v-model="form.is_public" label="Visible in storefront navigation" />
        </UFormField>
        <UFormField label="Description" class="md:col-span-2">
          <UTextarea v-model="form.description" :rows="4" />
        </UFormField>
      </div>
    </AdminFormModal>

    <AdminConfirmDialog
      v-if="pendingDeleteCategory"
      title="Delete category"
      description="Child categories may also be affected."
      confirm-label="Delete category"
      icon="i-lucide-trash-2"
      :loading="isSaving"
      @cancel="pendingDeleteCategory = null"
      @confirm="confirmDeleteCategory"
    >
      <p class="text-sm text-default">
        Delete <span class="font-semibold">{{ pendingDeleteCategory.name }}</span> from the catalogue?
      </p>
    </AdminConfirmDialog>
  </div>
</template>
