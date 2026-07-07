<script setup lang="ts">
import type { CommunicationTemplate, CommunicationTemplatePayload } from '~/composables/useCommunications'

const toast = useToast()
const { getCommunication, getCommunications, updateCommunication } = useCommunications()

const templates = ref<CommunicationTemplate[]>([])
const selectedTemplate = ref<CommunicationTemplate | null>(null)
const editingTemplate = ref<CommunicationTemplate | null>(null)
const searchQuery = ref('')
const categoryFilter = ref('all')
const activeEditorTab = ref<'text' | 'html' | 'sms'>('text')
const isLoading = ref(false)
const isSaving = ref(false)
const editorOpen = ref(false)
const saveError = ref('')

const form = reactive({
  name: '',
  category: '',
  email_subject_template: '',
  email_body_template: '',
  email_body_html_template: '',
  sms_template: '',
})

const categoryOptions = computed(() => [
  { label: 'All categories', value: 'all' },
  ...Array.from(new Set(templates.value.map(template => template.category || 'Uncategorized')))
    .sort((a, b) => a.localeCompare(b))
    .map(category => ({ label: category, value: category })),
])

const filteredTemplates = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return templates.value.filter((template) => {
    const matchesCategory = categoryFilter.value === 'all' || (template.category || 'Uncategorized') === categoryFilter.value
    const matchesSearch = !search
      || template.name.toLowerCase().includes(search)
      || template.code.toLowerCase().includes(search)
      || (template.category || '').toLowerCase().includes(search)
      || (template.email_subject_template || '').toLowerCase().includes(search)
    return matchesCategory && matchesSearch
  })
})

const emailTemplateCount = computed(() => templates.value.filter(template =>
  template.email_subject_template || template.email_body_template || template.email_body_html_template,
).length)
const smsTemplateCount = computed(() => templates.value.filter(template => template.sms_template).length)
const htmlTemplateCount = computed(() => templates.value.filter(template => template.email_body_html_template).length)

const selectedPreview = computed(() => {
  if (!selectedTemplate.value)
    return ''

  return selectedTemplate.value.email_body_template
    || stripHtml(selectedTemplate.value.email_body_html_template)
    || selectedTemplate.value.sms_template
    || 'No message body configured.'
})

const editorTabs = [
  { key: 'text', label: 'Text Email', icon: 'i-lucide-mail' },
  { key: 'html', label: 'HTML Email', icon: 'i-lucide-code-2' },
  { key: 'sms', label: 'SMS', icon: 'i-lucide-message-square' },
] as const

function stripHtml(value: string) {
  return (value || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

function fillForm(template: CommunicationTemplate) {
  form.name = template.name || ''
  form.category = template.category || ''
  form.email_subject_template = template.email_subject_template || ''
  form.email_body_template = template.email_body_template || ''
  form.email_body_html_template = template.email_body_html_template || ''
  form.sms_template = template.sms_template || ''
}

function subjectPreview(template: CommunicationTemplate) {
  return template.email_subject_template || 'No email subject'
}

function bodyLength(template: CommunicationTemplate) {
  return Number(template.email_body_template?.length || 0)
    + Number(template.email_body_html_template?.length || 0)
    + Number(template.sms_template?.length || 0)
}

async function loadTemplates() {
  isLoading.value = true
  const result = await getCommunications()

  if (result.success) {
    templates.value = result.data ?? []
    if (selectedTemplate.value)
      selectedTemplate.value = templates.value.find(template => template.code === selectedTemplate.value?.code) || null
  }
  else {
    templates.value = []
    toast.add({ title: 'Could not load communications', description: result.error || 'Please try again.', color: 'error' })
  }

  isLoading.value = false
}

async function openDetail(template: CommunicationTemplate) {
  selectedTemplate.value = template
  const result = await getCommunication(template.code)
  if (result.success && result.data)
    selectedTemplate.value = result.data
  else if (!result.success)
    toast.add({ title: 'Could not load template detail', description: result.error || 'Please try again.', color: 'error' })
}

function openEditor(template: CommunicationTemplate) {
  editingTemplate.value = template
  fillForm(template)
  activeEditorTab.value = 'text'
  saveError.value = ''
  editorOpen.value = true
}

async function submitTemplate() {
  if (!editingTemplate.value)
    return

  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Name is required.'
    return
  }
  if (!form.category.trim()) {
    saveError.value = 'Category is required.'
    return
  }

  isSaving.value = true
  const payload: CommunicationTemplatePayload = {
    name: form.name.trim(),
    category: form.category.trim(),
    email_subject_template: form.email_subject_template,
    email_body_template: form.email_body_template,
    email_body_html_template: form.email_body_html_template,
    sms_template: form.sms_template,
  }
  const result = await updateCommunication(editingTemplate.value.code, payload)

  if (result.success && result.data) {
    toast.add({ title: 'Template updated', description: `${result.data.name} was saved.`, color: 'success' })
    editorOpen.value = false
    selectedTemplate.value = result.data
    await loadTemplates()
  }
  else {
    saveError.value = result.error || 'Could not save template.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

onMounted(loadTemplates)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Communications</h1>
        <p class="mt-1 text-sm text-slate-500">Review and update Oscar customer communication templates.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search templates..."
        />
        <USelect v-model="categoryFilter" :items="categoryOptions" class="w-48" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadTemplates">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Templates" :value="templates.length" :budget="templates.length || 1" color="#2563eb" icon="i-lucide-send" :loading="isLoading" />
      <CardsKpiCard2 name="Email ready" :value="emailTemplateCount" :budget="templates.length || 1" color="#059669" icon="i-lucide-mail-check" :loading="isLoading" />
      <CardsKpiCard2 name="HTML bodies" :value="htmlTemplateCount" :budget="templates.length || 1" color="#7c3aed" icon="i-lucide-code-2" :loading="isLoading" />
      <CardsKpiCard2 name="SMS ready" :value="smsTemplateCount" :budget="templates.length || 1" color="#f59e0b" icon="i-lucide-message-square" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-3">Template</div>
          <div class="col-span-2">Category</div>
          <div class="col-span-4">Subject</div>
          <div class="col-span-1 text-right">Body</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading templates
        </div>

        <div v-else-if="filteredTemplates.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
            <UIcon name="i-lucide-send" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No templates found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another search or category.</p>
        </div>

        <div
          v-for="template in filteredTemplates"
          v-else
          :key="template.code"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
          :class="{ 'bg-blue-50/60': selectedTemplate?.code === template.code }"
        >
          <div class="col-span-3 min-w-0">
            <p class="truncate font-semibold text-slate-950">{{ template.name || template.code }}</p>
            <p class="truncate text-xs text-slate-500">{{ template.code }}</p>
          </div>
          <div class="col-span-2">
            <UBadge color="neutral" variant="soft" class="max-w-full truncate">{{ template.category || 'Uncategorized' }}</UBadge>
          </div>
          <div class="col-span-4 min-w-0">
            <p class="truncate text-sm font-semibold text-slate-700">{{ subjectPreview(template) }}</p>
          </div>
          <div class="col-span-1 text-right text-sm font-semibold text-slate-700">{{ bodyLength(template) }}</div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="View detail">
              <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openDetail(template)" />
            </UTooltip>
            <UTooltip text="Edit template">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditor(template)" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Template Detail</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedTemplate ? selectedTemplate.code : 'Select a template to preview content.' }}</p>
        </div>

        <div v-if="!selectedTemplate" class="p-8 text-center text-sm text-slate-500">
          Choose a template from the table to inspect subject, body, HTML, and SMS content.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-lg font-black text-slate-950">{{ selectedTemplate.name }}</p>
              <p class="truncate text-sm text-slate-500">{{ selectedTemplate.category || 'Uncategorized' }}</p>
            </div>
            <UBadge color="neutral" variant="soft">{{ selectedTemplate.id }}</UBadge>
          </div>

          <dl class="space-y-3 text-sm">
            <div>
              <dt class="font-semibold text-slate-500">Subject</dt>
              <dd class="mt-1 break-words text-slate-950">{{ subjectPreview(selectedTemplate) }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Preview</dt>
              <dd class="mt-1 rounded-lg border border-slate-200 bg-slate-50 p-3 leading-6 text-slate-700">
                <p class="line-clamp-6 whitespace-pre-wrap">{{ selectedPreview }}</p>
              </dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">SMS length</dt>
              <dd class="mt-1 text-slate-950">{{ selectedTemplate.sms_template?.length || 0 }} characters</dd>
            </div>
          </dl>

          <div class="mt-5">
            <UButton color="primary" variant="solid" @click="openEditor(selectedTemplate)">
              <UIcon name="i-lucide-pencil" />
              Edit Template
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredTemplates.length }} of {{ templates.length }} templates.</p>

    <div v-if="editorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[90vh] w-full max-w-5xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-default">Edit communication template</h3>
              <p class="truncate text-sm text-dimmed">{{ editingTemplate?.code }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required><UInput v-model="form.name" autocomplete="off" /></UFormField>
          <UFormField label="Category" required><UInput v-model="form.category" autocomplete="off" /></UFormField>
          <UFormField label="Email subject" class="md:col-span-2"><UInput v-model="form.email_subject_template" autocomplete="off" /></UFormField>
        </div>

        <div class="mt-5 flex flex-wrap gap-2 border-b border-slate-200 pb-3">
          <UButton
            v-for="tab in editorTabs"
            :key="tab.key"
            :color="activeEditorTab === tab.key ? 'primary' : 'neutral'"
            :variant="activeEditorTab === tab.key ? 'solid' : 'outline'"
            @click="activeEditorTab = tab.key"
          >
            <UIcon :name="tab.icon" />
            {{ tab.label }}
          </UButton>
        </div>

        <div class="mt-4">
          <UFormField v-if="activeEditorTab === 'text'" label="Text email body">
            <UTextarea v-model="form.email_body_template" :rows="14" class="font-mono text-sm" />
          </UFormField>
          <UFormField v-else-if="activeEditorTab === 'html'" label="HTML email body">
            <UTextarea v-model="form.email_body_html_template" :rows="14" class="font-mono text-sm" />
          </UFormField>
          <UFormField v-else label="SMS template">
            <UTextarea v-model="form.sms_template" :rows="10" class="font-mono text-sm" />
          </UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitTemplate">Save template</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
