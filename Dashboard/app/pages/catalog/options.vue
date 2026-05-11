<script setup lang="ts">
import type { OptionItem, OptionPayload } from '~/composables/useOptions'

const ALL_TYPES = '__all_types__'
const ALL_REQUIRED = '__all_required__'

const toast = useToast()
const { createOption, deleteOption, getOptions, updateOption } = useOptions()

const options = ref<OptionItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const typeFilter = ref(ALL_TYPES)
const requiredFilter = ref(ALL_REQUIRED)
const editorOpen = ref(false)
const editingOption = ref<OptionItem | null>(null)
const pendingDeleteOption = ref<OptionItem | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  code: '',
  type: 'text',
  required: false,
  help_text: '',
  order: 0,
})

const optionTypeOptions = [
  { label: 'Text', value: 'text' },
  { label: 'Integer', value: 'integer' },
  { label: 'Boolean', value: 'boolean' },
  { label: 'Float', value: 'float' },
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
  ...optionTypeOptions,
])

const requiredOptions = [
  { label: 'All options', value: ALL_REQUIRED },
  { label: 'Required', value: 'required' },
  { label: 'Optional', value: 'optional' },
]

const filteredOptions = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return options.value.filter((option) => {
    const matchesSearch = !search
      || option.name.toLowerCase().includes(search)
      || option.code.toLowerCase().includes(search)
      || option.help_text.toLowerCase().includes(search)
    const matchesType = typeFilter.value === ALL_TYPES || option.type === typeFilter.value
    const matchesRequired = requiredFilter.value === ALL_REQUIRED
      || (requiredFilter.value === 'required' && option.required)
      || (requiredFilter.value === 'optional' && !option.required)
    return matchesSearch && matchesType && matchesRequired
  })
})

const requiredCount = computed(() => options.value.filter(item => item.required).length)
const optionalCount = computed(() => options.value.filter(item => !item.required).length)
const configuredHelpCount = computed(() => options.value.filter(item => Boolean(item.help_text?.trim())).length)

function getTypeLabel(value: string) {
  return optionTypeOptions.find(option => option.value === value)?.label || value
}

function resetForm() {
  editingOption.value = null
  saveError.value = ''
  form.name = ''
  form.code = ''
  form.type = 'text'
  form.required = false
  form.help_text = ''
  form.order = 0
}

function openCreateOption() {
  resetForm()
  editorOpen.value = true
}

function openEditOption(option: OptionItem) {
  editingOption.value = option
  saveError.value = ''
  form.name = option.name
  form.code = option.code
  form.type = option.type
  form.required = option.required
  form.help_text = option.help_text
  form.order = Number(option.order || 0)
  editorOpen.value = true
}

async function loadOptions() {
  isLoading.value = true
  const result = await getOptions({ pageSize: 200 })

  if (result.success) {
    options.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? options.value.length
  }
  else {
    options.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load options',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function submitOption() {
  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Option name is required.'
    return
  }

  isSaving.value = true
  const payload: OptionPayload = {
    name: form.name.trim(),
    code: form.code.trim() || undefined,
    type: form.type,
    required: form.required,
    help_text: form.help_text.trim(),
    order: Number(form.order || 0),
  }

  const result = editingOption.value
    ? await updateOption(editingOption.value.id, payload)
    : await createOption(payload)

  if (result.success) {
    toast.add({
      title: editingOption.value ? 'Option updated' : 'Option created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadOptions()
  }
  else {
    saveError.value = result.error || 'Could not save option.'
    toast.add({
      title: 'Save failed',
      description: saveError.value,
      color: 'error',
    })
  }

  isSaving.value = false
}

async function confirmDeleteOption() {
  if (!pendingDeleteOption.value)
    return

  const option = pendingDeleteOption.value
  isSaving.value = true
  const result = await deleteOption(option.id)

  if (result.success) {
    toast.add({
      title: 'Option deleted',
      description: `${option.name} was removed.`,
      color: 'success',
    })
    pendingDeleteOption.value = null
    await loadOptions()
  }
  else {
    toast.add({
      title: 'Delete failed',
      description: result.error || 'Could not delete option.',
      color: 'error',
    })
  }

  isSaving.value = false
}

onMounted(loadOptions)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Product Options</h1>
        <p class="mt-1 text-sm text-slate-500">Manage order-time product options such as custom text, files, and selectable values.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search options..."
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
        <USelect
          v-model="requiredFilter"
          :items="requiredOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          color="neutral"
          variant="outline"
          size="lg"
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadOptions">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateOption">
          <UIcon name="i-lucide-plus" />
          New Option
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total options" :value="totalItems" :budget="totalItems" color="#3d7cff" icon="i-lucide-settings-2" :loading="isLoading" />
      <CardsKpiCard2 name="Required" :value="requiredCount" :budget="totalItems" color="#dc2626" icon="i-lucide-circle-alert" :loading="isLoading" />
      <CardsKpiCard2 name="Optional" :value="optionalCount" :budget="totalItems" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Help configured" :value="configuredHelpCount" :budget="totalItems" color="#7c3aed" icon="i-lucide-message-square-text" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-4">Option</div>
        <div class="col-span-2">Data type</div>
        <div class="col-span-1">Required</div>
        <div class="col-span-1 text-right">Order</div>
        <div class="col-span-2">Help text</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading options
      </div>

      <div v-else-if="filteredOptions.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-settings-2" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No options found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear the filters, or create a new product option.</p>
      </div>

      <div
        v-for="option in filteredOptions"
        v-else
        :key="option.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-4 min-w-0">
          <div class="flex min-w-0 items-center gap-3">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              <UIcon name="i-lucide-settings-2" />
            </div>
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ option.name }}</p>
              <p class="truncate text-xs text-slate-500">{{ option.code || 'No code' }}</p>
            </div>
          </div>
        </div>
        <div class="col-span-2">
          <UBadge color="info" variant="soft">{{ getTypeLabel(option.type) }}</UBadge>
        </div>
        <div class="col-span-1">
          <UBadge :color="option.required ? 'error' : 'neutral'" variant="soft">
            {{ option.required ? 'Yes' : 'No' }}
          </UBadge>
        </div>
        <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ option.order }}</div>
        <div class="col-span-2 truncate text-sm text-slate-600">{{ option.help_text || 'No help text' }}</div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="Edit option">
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditOption(option)" />
          </UTooltip>
          <UTooltip text="Delete option">
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteOption = option" />
          </UTooltip>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">
      Showing {{ filteredOptions.length }} of {{ totalItems }} options.
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
                {{ editingOption ? 'Edit option' : 'New option' }}
              </h3>
              <p class="text-sm text-dimmed">Configure an option customers can provide during product purchase.</p>
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
          <UFormField label="Code">
            <UInput v-model="form.code" autocomplete="off" placeholder="Auto-generated when empty" />
          </UFormField>
          <UFormField label="Data type" required>
            <USelect
              v-model="form.type"
              :items="optionTypeOptions"
              value-attribute="value"
              option-attribute="label"
            />
          </UFormField>
          <UFormField label="Display order">
            <UInput v-model.number="form.order" type="number" min="0" />
          </UFormField>
          <label class="rounded-lg border border-slate-200 bg-white p-4 md:col-span-2">
            <UCheckbox v-model="form.required" label="Required during purchase" />
            <p class="mt-2 text-sm text-slate-500">Required options should be completed before the basket line can be submitted.</p>
          </label>
          <UFormField label="Help text" class="md:col-span-2">
            <UTextarea v-model="form.help_text" :rows="4" />
          </UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">
              Cancel
            </UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitOption">
              Save option
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div
      v-if="pendingDeleteOption"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-error/10 p-2 text-error">
              <UIcon name="i-lucide-trash-2" />
            </div>
            <div>
              <h3 class="font-semibold text-default">Delete option</h3>
              <p class="text-sm text-dimmed">Products using this option may block deletion.</p>
            </div>
          </div>
        </template>

        <p class="text-sm text-default">
          Delete <span class="font-semibold">{{ pendingDeleteOption.name }}</span> from the catalogue?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteOption = null">
              Cancel
            </UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteOption">
              Delete option
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
