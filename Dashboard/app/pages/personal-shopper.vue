<script setup lang="ts">
import QRCode from 'qrcode'
import type { ShopperListRecord } from '~/composables/usePersonalShopper'

interface SelectOption { label: string, value: string | number }
interface CustomerOption { id: string, name: string, email: string }

const toast = useToast()
const config = useRuntimeConfig()
const { getLists, createList, archiveList } = usePersonalShopper()
const { getUsers } = useUser()
const { getProductOptions } = useProduct()

const lists = ref<ShopperListRecord[]>([])
const customers = ref<CustomerOption[]>([])
const products = ref<SelectOption[]>([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const search = ref('')
const qrDataUrl = ref('')
const sharedList = ref<ShopperListRecord | null>(null)
const form = reactive({
  customer_id: undefined as number | undefined,
  title: '',
  note: '',
  expires_at: '',
  publish: true,
  items: [] as Array<{ product_id?: number, quantity: number, note: string }>,
})

const customerOptions = computed(() => customers.value.map(user => ({
  label: `${user.name || user.email} · ${user.email}`,
  value: Number(user.id),
})))
const productOptions = computed(() => products.value.map(product => ({
  label: product.label,
  value: Number(product.value),
})))

function hubUrl(item: ShopperListRecord) {
  const base = String(config.public.storefrontBase).replace(/\/$/, '')
  return `${base}/hub/${item.share_token}`
}

async function load() {
  loading.value = true
  const [listResult, userResult, productResult] = await Promise.all([
    getLists(search.value ? { q: search.value } : {}),
    getUsers({ pageSize: 100, role: 'customer', status: 'active' }),
    getProductOptions({ pageSize: 100, maxPages: 5 }),
  ])
  lists.value = listResult.data || []
  customers.value = userResult.success ? (userResult.data?.results || []) : []
  products.value = productResult.success ? (productResult.data || []) : []
  if (!listResult.success)
    toast.add({ title: 'Could not load shopper lists', description: listResult.error, color: 'error' })
  loading.value = false
}

function openForm() {
  Object.assign(form, { customer_id: undefined, title: '', note: '', expires_at: '', publish: true, items: [{ product_id: undefined, quantity: 1, note: '' }] })
  showForm.value = true
}

function addItem() {
  form.items.push({ product_id: undefined, quantity: 1, note: '' })
}

async function save() {
  if (!form.customer_id || !form.title.trim() || !form.items.length || form.items.some(item => !item.product_id)) {
    toast.add({ title: 'Complete the list', description: 'Choose a customer, title, and at least one product.', color: 'warning' })
    return
  }
  saving.value = true
  const result = await createList({
    customer_id: form.customer_id,
    title: form.title.trim(),
    note: form.note.trim(),
    status: form.publish ? 'shared' : 'draft',
    expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
    items: form.items.map(item => ({ product_id: Number(item.product_id), quantity: Number(item.quantity), note: item.note.trim() })),
  })
  saving.value = false
  if (!result.success) {
    toast.add({ title: 'Could not create list', description: result.error, color: 'error' })
    return
  }
  showForm.value = false
  await load()
  toast.add({ title: form.publish ? 'List published' : 'Draft saved', description: 'The personal shopper list is ready.', color: 'success' })
  if (form.publish)
    await showShare(result.data)
}

async function showShare(item: ShopperListRecord) {
  sharedList.value = item
  qrDataUrl.value = await QRCode.toDataURL(hubUrl(item), { width: 320, margin: 2, errorCorrectionLevel: 'M' })
}

async function copyLink(item: ShopperListRecord | null) {
  if (!item) return
  await navigator.clipboard.writeText(hubUrl(item))
  toast.add({ title: 'Hub link copied', color: 'success' })
}

async function archive(item: ShopperListRecord) {
  const result = await archiveList(item.id)
  if (result.success) await load()
  else toast.add({ title: 'Could not archive list', description: result.error, color: 'error' })
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 300)
})
onMounted(load)
</script>

<template>
  <div class="p-4 sm:p-8">
    <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Personal Shopper</h1>
        <p class="mt-1 text-sm text-slate-500">Curate and securely share product lists with registered customers.</p>
      </div>
      <div class="flex gap-2">
        <UInput v-model="search" icon="i-lucide-search" placeholder="Search customer or list" />
        <UButton color="primary" @click="openForm"><UIcon name="i-lucide-plus" /> New list</UButton>
      </div>
    </div>

    <div v-if="loading" class="py-16 text-center text-slate-500">Loading personal shopper lists…</div>
    <div v-else-if="!lists.length" class="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
      <UIcon name="i-lucide-shopping-basket" class="size-10 text-blue-600" />
      <h2 class="mt-3 text-lg font-bold">No shopper lists yet</h2>
      <p class="mt-1 text-sm text-slate-500">Create the first curated list for a customer.</p>
    </div>
    <div v-else class="grid gap-4 xl:grid-cols-2">
      <UCard v-for="item in lists" :key="item.id">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="flex items-center gap-2"><h2 class="font-bold text-slate-950">{{ item.title }}</h2><UBadge>{{ item.status.replaceAll('_', ' ') }}</UBadge></div>
            <p class="mt-1 text-sm text-slate-600">{{ item.customer.name }} · {{ item.customer.email }}</p>
            <p class="mt-2 text-sm text-slate-500">{{ item.items.length }} products · Updated {{ new Date(item.date_updated).toLocaleDateString() }}</p>
          </div>
          <div class="flex gap-1">
            <UButton v-if="item.status !== 'draft' && item.status !== 'archived'" icon="i-lucide-qr-code" variant="outline" @click="showShare(item)" />
            <UButton v-if="item.status !== 'archived'" icon="i-lucide-archive" variant="ghost" color="error" @click="archive(item)" />
          </div>
        </div>
      </UCard>
    </div>

    <UModal v-model:open="showForm" title="Create personal shopper list" description="Choose a customer and the products you recommend.">
      <template #body>
        <div class="space-y-4">
          <UFormField label="Customer" required><USelectMenu v-model="form.customer_id" :items="customerOptions" value-key="value" searchable class="w-full" /></UFormField>
          <UFormField label="List title" required><UInput v-model="form.title" placeholder="Recommended borehole system" class="w-full" /></UFormField>
          <UFormField label="Message to customer"><UTextarea v-model="form.note" :rows="3" class="w-full" /></UFormField>
          <UFormField label="Expires (optional)"><UInput v-model="form.expires_at" type="datetime-local" class="w-full" /></UFormField>
          <div class="flex items-center justify-between"><h3 class="font-bold">Products</h3><UButton size="sm" variant="outline" @click="addItem"><UIcon name="i-lucide-plus" /> Add product</UButton></div>
          <div v-for="(item, index) in form.items" :key="index" class="grid gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-[1fr_90px_auto]">
            <USelectMenu v-model="item.product_id" :items="productOptions" value-key="value" searchable placeholder="Choose product" />
            <UInput v-model.number="item.quantity" type="number" min="1" aria-label="Quantity" />
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" :disabled="form.items.length === 1" @click="form.items.splice(index, 1)" />
            <UInput v-model="item.note" class="sm:col-span-3" placeholder="Why this item? (optional)" />
          </div>
          <UCheckbox v-model="form.publish" label="Publish and generate Hub link now" />
        </div>
      </template>
      <template #footer><div class="flex w-full justify-end gap-2"><UButton variant="outline" @click="showForm = false">Cancel</UButton><UButton color="primary" :loading="saving" @click="save">{{ form.publish ? 'Publish list' : 'Save draft' }}</UButton></div></template>
    </UModal>

    <UModal :open="!!sharedList" title="Share Personal Shopper Hub" @update:open="value => { if (!value) sharedList = null }">
      <template #body>
        <div v-if="sharedList" class="text-center">
          <img :src="qrDataUrl" alt="QR code for the customer's secure Hub page" class="mx-auto w-64 rounded-lg border">
          <p class="mt-3 text-sm text-slate-500">The customer must sign in to the account assigned to this list.</p>
          <UInput :model-value="hubUrl(sharedList)" readonly class="mt-3 w-full" />
        </div>
      </template>
      <template #footer><div class="flex w-full justify-end"><UButton icon="i-lucide-copy" color="primary" @click="copyLink(sharedList)">Copy link</UButton></div></template>
    </UModal>
  </div>
</template>
