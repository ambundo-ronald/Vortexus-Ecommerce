<script setup lang="ts">
import type { AdminEmailTemplateItem } from '~/composables/useEmailConfig'

const toast = useToast()
const { getEmailTemplates, updateEmailTemplate } = useEmailConfig()

const templates = ref<AdminEmailTemplateItem[]>([])
const selected = ref<AdminEmailTemplateItem | null>(null)
const isLoading = ref(false)
const saving = ref(false)
const search = ref('')

const form = reactive({
  name: '',
  category: '',
  email_subject_template: '',
  email_body_template: '',
  email_body_html_template: '',
})

const commonVariables = '{{ shop_name }}, {{ display_name }}, {{ verification_url }}, {{ reset_url }}, {{ code }}'

function selectTemplate(template: AdminEmailTemplateItem) {
  selected.value = template
  form.name = template.name
  form.category = template.category
  form.email_subject_template = template.email_subject_template
  form.email_body_template = template.email_body_template
  form.email_body_html_template = template.email_body_html_template
}

async function loadTemplates() {
  isLoading.value = true
  const result = await getEmailTemplates(search.value.trim())
  if (result.success) {
    templates.value = result.data ?? []
    if (!selected.value && templates.value.length)
      selectTemplate(templates.value[0])
    else if (selected.value) {
      const current = templates.value.find(template => template.code === selected.value?.code)
      if (current)
        selectTemplate(current)
    }
  }
  else {
    toast.add({ title: 'Could not load templates', description: result.error || 'Please try again.', color: 'error' })
  }
  isLoading.value = false
}

async function saveTemplate() {
  if (!selected.value)
    return
  saving.value = true
  const result = await updateEmailTemplate(selected.value.code, { ...form })
  if (result.success && result.data) {
    toast.add({ title: 'Template saved', description: `${result.data.name} was updated.`, color: 'success' })
    await loadTemplates()
  }
  else {
    toast.add({ title: 'Could not save template', description: result.error || 'Please check the template fields.', color: 'error' })
  }
  saving.value = false
}

function formatCode(code: string) {
  return code.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase())
}

onMounted(loadTemplates)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Email Templates</h1>
        <p class="mt-1 text-sm text-slate-500">Edit the subject, plain text, and optional HTML used by account and security emails.</p>
      </div>
      <div class="flex w-full gap-2 lg:w-auto">
        <UInput v-model="search" class="flex-1 lg:w-72" icon="i-lucide-search" placeholder="Search templates..." @keyup.enter="loadTemplates" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadTemplates"><UIcon name="i-lucide-refresh-cw" />Refresh</UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-12">
      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-4">
        <div class="border-b border-slate-200 px-4 py-3 text-xs font-bold uppercase text-slate-500">Templates</div>
        <div v-if="isLoading" class="p-8 text-center text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading templates
        </div>
        <div v-else-if="templates.length === 0" class="p-8 text-center text-sm text-slate-500">No email templates found.</div>
        <button
          v-for="template in templates"
          v-else
          :key="template.code"
          type="button"
          class="block w-full border-b border-slate-100 px-4 py-3 text-left last:border-b-0 hover:bg-slate-50"
          :class="selected?.code === template.code ? 'bg-blue-50' : 'bg-white'"
          @click="selectTemplate(template)"
        >
          <div class="flex items-center justify-between gap-3">
            <p class="truncate text-sm font-bold text-slate-950">{{ template.name || formatCode(template.code) }}</p>
            <UBadge color="neutral" variant="soft">{{ template.category || 'Email' }}</UBadge>
          </div>
          <p class="mt-1 truncate text-xs text-slate-500">{{ template.code }}</p>
        </button>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-4 xl:col-span-8">
        <div v-if="!selected" class="p-12 text-center text-sm text-slate-500">Select a template to edit.</div>
        <div v-else class="space-y-4">
          <div class="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 class="text-lg font-black text-slate-950">{{ form.name || formatCode(selected.code) }}</h2>
              <p class="text-sm text-slate-500">{{ selected.code }}</p>
            </div>
            <UButton color="primary" :loading="saving" @click="saveTemplate"><UIcon name="i-lucide-save" />Save Template</UButton>
          </div>

          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <UFormField label="Name"><UInput v-model="form.name" /></UFormField>
            <UFormField label="Category"><UInput v-model="form.category" /></UFormField>
          </div>
          <UFormField label="Subject"><UInput v-model="form.email_subject_template" /></UFormField>
          <UFormField label="Plain text body">
            <UTextarea v-model="form.email_body_template" :rows="14" class="font-mono text-sm" />
          </UFormField>
          <UFormField label="HTML body">
            <UTextarea v-model="form.email_body_html_template" :rows="10" class="font-mono text-sm" placeholder="<p>Hello {{ display_name }}</p>" />
          </UFormField>

          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 class="mb-2 text-sm font-black text-slate-950">Common Variables</h3>
            <p class="text-sm text-slate-600">{{ commonVariables }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
