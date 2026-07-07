<script setup lang="ts">
import type { SupplierItem, SupplierPayload } from '~/composables/useSuppliers'

const toast = useToast()
const { getSupplier, getSuppliers, updateSupplier } = useSuppliers()

const suppliers = ref<SupplierItem[]>([])
const selectedSupplier = ref<SupplierItem | null>(null)
const searchQuery = ref('')
const ALL_STATUSES = '__all_statuses__'
const statusFilter = ref(ALL_STATUSES)
const isLoading = ref(false)
const isSaving = ref(false)
const editorOpen = ref(false)
const saveError = ref('')

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Suspended', value: 'suspended' },
]

const form = reactive({
  company_name: '',
  contact_name: '',
  phone: '',
  country_code: '',
  website: '',
  notes: '',
  status_note: '',
  account_manager_id: '',
  status: 'pending',
})

const filteredSuppliers = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return suppliers.value.filter((supplier) => {
    return !search
      || supplier.company_name.toLowerCase().includes(search)
      || supplier.contact_name.toLowerCase().includes(search)
      || supplier.partner?.name?.toLowerCase().includes(search)
      || supplier.partner?.code?.toLowerCase().includes(search)
      || supplier.user?.email?.toLowerCase().includes(search)
      || String(supplier.id).includes(search)
  })
})

const pendingCount = computed(() => suppliers.value.filter(supplier => supplier.status === 'pending').length)
const approvedCount = computed(() => suppliers.value.filter(supplier => supplier.status === 'approved').length)
const suspendedCount = computed(() => suppliers.value.filter(supplier => supplier.status === 'suspended').length)

function statusColor(status: string) {
  if (status === 'approved')
    return 'success'
  if (status === 'suspended')
    return 'error'
  return 'warning'
}

function formatStatus(status: string) {
  return status ? status.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function formatDate(value: string) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function fillForm(supplier: SupplierItem) {
  form.company_name = supplier.company_name || ''
  form.contact_name = supplier.contact_name || ''
  form.phone = supplier.phone || ''
  form.country_code = supplier.country_code || ''
  form.website = supplier.website || ''
  form.notes = supplier.notes || ''
  form.status_note = supplier.status_note || ''
  form.account_manager_id = supplier.account_manager?.id ? String(supplier.account_manager.id) : ''
  form.status = supplier.status || 'pending'
}

async function loadSuppliers() {
  isLoading.value = true
  const result = await getSuppliers({ status: statusFilter.value === ALL_STATUSES ? '' : statusFilter.value })

  if (result.success) {
    suppliers.value = result.data?.results ?? []
    if (selectedSupplier.value) {
      selectedSupplier.value = suppliers.value.find(supplier => supplier.id === selectedSupplier.value?.id) || null
      if (selectedSupplier.value)
        fillForm(selectedSupplier.value)
    }
  }
  else {
    suppliers.value = []
    toast.add({
      title: 'Could not load suppliers',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function openSupplier(supplier: SupplierItem) {
  selectedSupplier.value = supplier
  fillForm(supplier)

  const result = await getSupplier(supplier.id)
  if (result.success && result.data) {
    selectedSupplier.value = result.data
    fillForm(result.data)
  }
  else if (!result.success) {
    toast.add({ title: 'Could not load supplier detail', description: result.error || 'Please try again.', color: 'error' })
  }
}

async function quickStatus(supplier: SupplierItem, status: string) {
  isSaving.value = true
  const result = await updateSupplier(supplier.id, { status })

  if (result.success) {
    toast.add({ title: 'Supplier status updated', description: `${supplier.company_name} is now ${formatStatus(status)}.`, color: 'success' })
    await loadSuppliers()
    if (selectedSupplier.value?.id === supplier.id)
      await openSupplier(result.data || supplier)
  }
  else {
    toast.add({ title: 'Status update failed', description: result.error || 'Could not update supplier.', color: 'error' })
  }

  isSaving.value = false
}

function openEditor() {
  if (!selectedSupplier.value)
    return
  fillForm(selectedSupplier.value)
  saveError.value = ''
  editorOpen.value = true
}

async function submitSupplier() {
  if (!selectedSupplier.value)
    return

  saveError.value = ''
  if (!form.company_name.trim()) {
    saveError.value = 'Company name is required.'
    return
  }

  isSaving.value = true
  const payload: SupplierPayload = {
    company_name: form.company_name.trim(),
    contact_name: form.contact_name.trim(),
    phone: form.phone.trim(),
    country_code: form.country_code.trim().toUpperCase(),
    website: form.website.trim(),
    notes: form.notes.trim(),
    status_note: form.status_note.trim(),
    account_manager_id: form.account_manager_id ? Number(form.account_manager_id) : null,
    status: form.status,
  }
  const result = await updateSupplier(selectedSupplier.value.id, payload)

  if (result.success && result.data) {
    selectedSupplier.value = result.data
    fillForm(result.data)
    toast.add({ title: 'Supplier updated', description: `${result.data.company_name} was saved.`, color: 'success' })
    editorOpen.value = false
    await loadSuppliers()
  }
  else {
    saveError.value = result.error || 'Could not update supplier.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

watch(statusFilter, loadSuppliers)

onMounted(loadSuppliers)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Suppliers</h1>
        <p class="mt-1 text-sm text-slate-500">Review supplier profiles, update contact details, and manage approval status.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search suppliers..."
        />
        <USelect v-model="statusFilter" :items="statusOptions" class="w-44" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadSuppliers">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total suppliers" :value="suppliers.length" :budget="suppliers.length" color="#30328f" icon="i-lucide-store" :loading="isLoading" />
      <CardsKpiCard2 name="Pending" :value="pendingCount" :budget="suppliers.length" color="#f59e0b" icon="i-lucide-clock" :loading="isLoading" />
      <CardsKpiCard2 name="Approved" :value="approvedCount" :budget="suppliers.length" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Suspended" :value="suspendedCount" :budget="suppliers.length" color="#dc2626" icon="i-lucide-ban" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-5">Supplier</div>
          <div class="col-span-3">Partner</div>
          <div class="col-span-2">Status</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading suppliers
        </div>

        <div v-else-if="filteredSuppliers.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
            <UIcon name="i-lucide-store" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No suppliers found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another search or status filter.</p>
        </div>

        <div
          v-for="supplier in filteredSuppliers"
          v-else
          :key="supplier.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
          :class="{ 'bg-blue-50/60': selectedSupplier?.id === supplier.id }"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-store" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ supplier.company_name }}</p>
                <p class="truncate text-xs text-slate-500">{{ supplier.user?.email || 'No user email' }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-3 min-w-0">
            <p class="truncate text-sm font-semibold text-slate-700">{{ supplier.partner?.name || 'No partner' }}</p>
            <p class="truncate text-xs text-slate-500">{{ supplier.partner?.code || 'No code' }}</p>
          </div>
          <div class="col-span-2">
            <UBadge :color="statusColor(supplier.status)" variant="soft">{{ formatStatus(supplier.status) }}</UBadge>
          </div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="View details">
              <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openSupplier(supplier)" />
            </UTooltip>
            <UTooltip v-if="supplier.status !== 'approved'" text="Approve supplier">
              <UButton icon="i-lucide-circle-check" color="success" variant="ghost" square :loading="isSaving" @click="quickStatus(supplier, 'approved')" />
            </UTooltip>
            <UTooltip v-if="supplier.status !== 'suspended'" text="Suspend supplier">
              <UButton icon="i-lucide-ban" color="error" variant="ghost" square :loading="isSaving" @click="quickStatus(supplier, 'suspended')" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Supplier Detail</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedSupplier ? selectedSupplier.company_name : 'Select a supplier to inspect profile details.' }}</p>
        </div>

        <div v-if="!selectedSupplier" class="p-8 text-center text-sm text-slate-500">
          Choose a supplier from the table to review application, partner, and account details.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-lg font-black text-slate-950">{{ selectedSupplier.company_name }}</p>
              <p class="truncate text-sm text-slate-500">Supplier #{{ selectedSupplier.id }}</p>
            </div>
            <UBadge :color="statusColor(selectedSupplier.status)" variant="soft">{{ formatStatus(selectedSupplier.status) }}</UBadge>
          </div>

          <dl class="space-y-3 text-sm">
            <div>
              <dt class="font-semibold text-slate-500">Contact</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.contact_name || 'Not provided' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Phone</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.phone || 'Not provided' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Country</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.country_code || 'Not provided' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Website</dt>
              <dd class="mt-1 break-all text-slate-950">{{ selectedSupplier.website || 'Not provided' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">User account</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.user?.email || selectedSupplier.user?.username || 'Not provided' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Partner</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.partner?.name || 'Not linked' }}</dd>
              <dd class="text-xs text-slate-500">{{ selectedSupplier.partner?.code || 'No code' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Notes</dt>
              <dd class="mt-1 whitespace-pre-wrap text-slate-950">{{ selectedSupplier.notes || 'No notes recorded.' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Status note</dt>
              <dd class="mt-1 whitespace-pre-wrap text-slate-950">{{ selectedSupplier.status_note || 'No supplier-facing note.' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Account manager</dt>
              <dd class="mt-1 text-slate-950">{{ selectedSupplier.account_manager?.name || selectedSupplier.account_manager?.email || 'Not assigned' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Updated</dt>
              <dd class="mt-1 text-slate-950">{{ formatDate(selectedSupplier.updated_at) }}</dd>
            </div>
          </dl>

          <div class="mt-5 flex flex-wrap gap-2">
            <UButton color="primary" variant="solid" @click="openEditor">
              <UIcon name="i-lucide-pencil" />
              Edit Profile
            </UButton>
            <UButton v-if="selectedSupplier.status !== 'approved'" color="success" variant="outline" :loading="isSaving" @click="quickStatus(selectedSupplier, 'approved')">
              <UIcon name="i-lucide-circle-check" />
              Approve
            </UButton>
            <UButton v-if="selectedSupplier.status !== 'suspended'" color="error" variant="outline" :loading="isSaving" @click="quickStatus(selectedSupplier, 'suspended')">
              <UIcon name="i-lucide-ban" />
              Suspend
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredSuppliers.length }} of {{ suppliers.length }} suppliers.</p>

    <div v-if="editorOpen && selectedSupplier" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-3xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">Edit supplier profile</h3>
              <p class="text-sm text-dimmed">{{ selectedSupplier.company_name }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Company name" required><UInput v-model="form.company_name" autocomplete="off" /></UFormField>
          <UFormField label="Status"><USelect v-model="form.status" :items="statusOptions.slice(1)" /></UFormField>
          <UFormField label="Contact name"><UInput v-model="form.contact_name" autocomplete="off" /></UFormField>
          <UFormField label="Phone"><UInput v-model="form.phone" autocomplete="off" /></UFormField>
          <UFormField label="Country code"><UInput v-model="form.country_code" maxlength="2" autocomplete="off" /></UFormField>
          <UFormField label="Website"><UInput v-model="form.website" type="url" autocomplete="off" /></UFormField>
          <UFormField label="Account manager ID"><UInput v-model="form.account_manager_id" type="number" min="1" autocomplete="off" /></UFormField>
          <UFormField label="Notes" class="md:col-span-2"><UTextarea v-model="form.notes" :rows="5" /></UFormField>
          <UFormField label="Supplier-facing status note" class="md:col-span-2"><UTextarea v-model="form.status_note" :rows="4" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitSupplier">Save supplier</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
