<script setup lang="ts">
import type { PartnerItem, PartnerPayload, PartnerUserItem } from '~/composables/usePartners'

const toast = useToast()
const {
  createPartner,
  deletePartner,
  getPartners,
  getPartnerUsers,
  linkPartnerUser,
  unlinkPartnerUser,
  updatePartner,
} = usePartners()
const { getUsers } = useUser()

const partners = ref<PartnerItem[]>([])
const partnerUsers = ref<PartnerUserItem[]>([])
const userOptions = ref<{ label: string, value: number }[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const isLoadingUsers = ref(false)
const searchQuery = ref('')
const userSearch = ref('')
const selectedUserId = ref<number | null>(null)
const editorOpen = ref(false)
const editingPartner = ref<PartnerItem | null>(null)
const selectedPartner = ref<PartnerItem | null>(null)
const pendingDeletePartner = ref<PartnerItem | null>(null)
const pendingUnlinkUser = ref<PartnerUserItem | null>(null)
const saveError = ref('')

const form = reactive({
  name: '',
  code: '',
})

const filteredPartners = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return partners.value.filter((partner) => {
    return !search
      || partner.name.toLowerCase().includes(search)
      || partner.code.toLowerCase().includes(search)
      || String(partner.id).includes(search)
  })
})

const linkedPartnerCount = computed(() => partners.value.filter(partner => Number(partner.user_count || 0) > 0).length)
const unlinkedPartnerCount = computed(() => partners.value.filter(partner => Number(partner.user_count || 0) === 0).length)
const linkedUserCount = computed(() => partners.value.reduce((total, partner) => total + Number(partner.user_count || 0), 0))

function resetForm() {
  editingPartner.value = null
  saveError.value = ''
  form.name = ''
  form.code = ''
}

function openCreatePartner() {
  resetForm()
  editorOpen.value = true
}

function openEditPartner(partner: PartnerItem) {
  editingPartner.value = partner
  saveError.value = ''
  form.name = partner.name
  form.code = partner.code
  editorOpen.value = true
}

async function loadPartners() {
  isLoading.value = true
  const result = await getPartners({ pageSize: 200 })

  if (result.success) {
    partners.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? partners.value.length
  }
  else {
    partners.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load partners',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function loadUsers() {
  isLoadingUsers.value = true
  const result = await getUsers({ pageSize: 50, search: userSearch.value.trim() })

  if (result.success) {
    const linkedIds = new Set(partnerUsers.value.map(user => Number(user.id)))
    userOptions.value = (result.data?.results ?? [])
      .filter((user: any) => !linkedIds.has(Number(user.id)))
      .map((user: any) => ({
        label: `#${user.id} ${user.email || user.name || user.username || 'Unnamed user'}`,
        value: Number(user.id),
      }))
  }
  else {
    userOptions.value = []
    toast.add({
      title: 'Could not search users',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoadingUsers.value = false
}

async function loadPartnerUsers(partner: PartnerItem) {
  selectedPartner.value = partner
  selectedUserId.value = null
  partnerUsers.value = []
  const result = await getPartnerUsers(partner.id)

  if (result.success)
    partnerUsers.value = result.data ?? []
  else
    toast.add({ title: 'Could not load partner users', description: result.error || 'Please try again.', color: 'error' })

  await loadUsers()
}

async function submitPartner() {
  saveError.value = ''
  if (!form.name.trim()) {
    saveError.value = 'Partner name is required.'
    return
  }

  isSaving.value = true
  const payload: PartnerPayload = {
    name: form.name.trim(),
    code: form.code.trim() || undefined,
  }
  const result = editingPartner.value
    ? await updatePartner(editingPartner.value.id, payload)
    : await createPartner(payload)

  if (result.success) {
    toast.add({
      title: editingPartner.value ? 'Partner updated' : 'Partner created',
      description: `${payload.name} was saved successfully.`,
      color: 'success',
    })
    editorOpen.value = false
    resetForm()
    await loadPartners()
  }
  else {
    saveError.value = result.error || 'Could not save partner.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeletePartner() {
  if (!pendingDeletePartner.value)
    return

  isSaving.value = true
  const partner = pendingDeletePartner.value
  const result = await deletePartner(partner.id)

  if (result.success) {
    toast.add({ title: 'Partner deleted', description: `${partner.name} was removed.`, color: 'success' })
    pendingDeletePartner.value = null
    if (selectedPartner.value?.id === partner.id)
      selectedPartner.value = null
    await loadPartners()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete partner.', color: 'error' })
  }

  isSaving.value = false
}

async function linkUser() {
  if (!selectedPartner.value || !selectedUserId.value)
    return

  isSaving.value = true
  const result = await linkPartnerUser(selectedPartner.value.id, selectedUserId.value)

  if (result.success) {
    toast.add({ title: 'User linked', color: 'success' })
    selectedUserId.value = null
    await loadPartners()
    await loadPartnerUsers(result.data || selectedPartner.value)
  }
  else {
    toast.add({ title: 'Link failed', description: result.error || 'Could not link user.', color: 'error' })
  }

  isSaving.value = false
}

async function confirmUnlinkUser() {
  if (!selectedPartner.value || !pendingUnlinkUser.value)
    return

  isSaving.value = true
  const user = pendingUnlinkUser.value
  const result = await unlinkPartnerUser(selectedPartner.value.id, user.id)

  if (result.success) {
    toast.add({ title: 'User unlinked', color: 'success' })
    pendingUnlinkUser.value = null
    await loadPartners()
    await loadPartnerUsers(result.data || selectedPartner.value)
  }
  else {
    toast.add({ title: 'Unlink failed', description: result.error || 'Could not unlink user.', color: 'error' })
  }

  isSaving.value = false
}

watch(userSearch, async () => {
  if (selectedPartner.value)
    await loadUsers()
})

onMounted(loadPartners)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Partners</h1>
        <p class="mt-1 text-sm text-slate-500">Manage Oscar partners and link dashboard users to supplier accounts.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search partners..."
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadPartners">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreatePartner">
          <UIcon name="i-lucide-plus" />
          New Partner
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total partners" :value="totalItems" :budget="totalItems" color="#30328f" icon="i-lucide-handshake" :loading="isLoading" />
      <CardsKpiCard2 name="With users" :value="linkedPartnerCount" :budget="totalItems" color="#059669" icon="i-lucide-user-check" :loading="isLoading" />
      <CardsKpiCard2 name="No users" :value="unlinkedPartnerCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-user-x" :loading="isLoading" />
      <CardsKpiCard2 name="Linked users" :value="linkedUserCount" :budget="linkedUserCount" color="#7c3aed" icon="i-lucide-users" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-5">Partner</div>
          <div class="col-span-3">Code</div>
          <div class="col-span-2 text-right">Users</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading partners
        </div>

        <div v-else-if="filteredPartners.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
            <UIcon name="i-lucide-handshake" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No partners found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another search or create a new partner.</p>
        </div>

        <div
          v-for="partner in filteredPartners"
          v-else
          :key="partner.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                <UIcon name="i-lucide-handshake" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ partner.name }}</p>
                <p class="truncate text-xs text-slate-500">Partner #{{ partner.id }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-3 truncate text-sm font-semibold text-slate-700">{{ partner.code || 'No code' }}</div>
          <div class="col-span-2 text-right text-sm font-semibold text-slate-700">{{ partner.user_count }}</div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="Manage users">
              <UButton icon="i-lucide-users" color="neutral" variant="ghost" square @click="loadPartnerUsers(partner)" />
            </UTooltip>
            <UTooltip text="Edit partner">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditPartner(partner)" />
            </UTooltip>
            <UTooltip text="Delete partner">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeletePartner = partner" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Partner Users</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedPartner ? selectedPartner.name : 'Select a partner to manage linked users.' }}</p>
        </div>

        <div v-if="!selectedPartner" class="p-8 text-center text-sm text-slate-500">
          Choose a partner from the table to link or unlink users.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 grid grid-cols-1 gap-2">
            <UInput v-model="userSearch" color="neutral" variant="outline" icon="i-lucide-search" placeholder="Search users to link..." />
            <div class="flex gap-2">
              <USelect v-model="selectedUserId" :items="userOptions" value-attribute="value" option-attribute="label" class="min-w-0 flex-1" :loading="isLoadingUsers" placeholder="Select user" />
              <UButton color="primary" variant="solid" :loading="isSaving" :disabled="!selectedUserId" @click="linkUser">
                <UIcon name="i-lucide-link" />
                Link
              </UButton>
            </div>
          </div>

          <div class="max-h-[420px] overflow-y-auto rounded-lg border border-slate-200">
            <div v-if="partnerUsers.length === 0" class="p-8 text-center text-sm text-slate-500">No users linked.</div>
            <div v-for="user in partnerUsers" :key="user.id" class="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0">
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ user.email || user.username || 'Unnamed user' }}</p>
                <p class="truncate text-xs text-slate-500">User #{{ user.id }}</p>
              </div>
              <UTooltip text="Unlink user">
                <UButton icon="i-lucide-unlink" color="error" variant="ghost" square @click="pendingUnlinkUser = user" />
              </UTooltip>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredPartners.length }} of {{ totalItems }} partners.</p>

    <div v-if="editorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ editingPartner ? 'Edit partner' : 'New partner' }}</h3>
              <p class="text-sm text-dimmed">Configure the Oscar partner record.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editorOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Name" required><UInput v-model="form.name" autocomplete="off" /></UFormField>
          <UFormField label="Code"><UInput v-model="form.code" autocomplete="off" placeholder="Auto-generated when empty" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editorOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitPartner">Save partner</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDeletePartner" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete partner</h3></template>
        <p class="text-sm text-default">Delete <span class="font-semibold">{{ pendingDeletePartner.name }}</span>? Stock records or supplier links may block deletion.</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeletePartner = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeletePartner">Delete partner</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingUnlinkUser" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Unlink user</h3></template>
        <p class="text-sm text-default">Unlink <span class="font-semibold">{{ pendingUnlinkUser.email || pendingUnlinkUser.username }}</span> from this partner?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingUnlinkUser = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmUnlinkUser">Unlink user</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
