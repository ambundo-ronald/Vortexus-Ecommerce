<script setup lang="ts">
const toast = useToast()
const { request } = useBackendApi()

const ALL_STATUSES = '__all_statuses__'
const activeTab = ref<'offers' | 'requests'>('offers')
const statusFilter = ref('pending_review')
const searchQuery = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const decisionOpen = ref(false)
const selectedItem = ref<any | null>(null)
const decisionStatus = ref('')
const reviewNote = ref('')
const linkedProductSearch = ref('')
const linkedProductResults = ref<any[]>([])
const linkedProduct = ref<any | null>(null)
const saveError = ref('')
const offers = ref<any[]>([])
const productRequests = ref<any[]>([])
const pagination = ref({ page: 1, page_size: 24, total: 0, num_pages: 1, has_next: false })

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Pending review', value: 'pending_review' },
  { label: 'Changes requested', value: 'changes_requested' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Suspended', value: 'suspended' },
]

const requestStatusOptions = statusOptions.filter(option => option.value !== 'suspended')

const moderationActions = computed(() => {
  const actions = [
    { label: 'Approve', value: 'approved', color: 'success', icon: 'i-lucide-circle-check' },
    { label: 'Request changes', value: 'changes_requested', color: 'warning', icon: 'i-lucide-message-square-warning' },
    { label: 'Reject', value: 'rejected', color: 'error', icon: 'i-lucide-circle-x' },
  ]
  if (activeTab.value === 'offers')
    actions.push({ label: 'Suspend', value: 'suspended', color: 'error', icon: 'i-lucide-ban' })
  return actions
})

const currentRows = computed(() => activeTab.value === 'offers' ? offers.value : productRequests.value)

const filteredRows = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  if (!search)
    return currentRows.value

  return currentRows.value.filter((item) => {
    const product = item.product || item.linked_product || {}
    return String(item.id).includes(search)
      || item.requested_title?.toLowerCase?.().includes(search)
      || item.brand?.toLowerCase?.().includes(search)
      || item.category_hint?.toLowerCase?.().includes(search)
      || product.title?.toLowerCase?.().includes(search)
      || product.upc?.toLowerCase?.().includes(search)
      || product.sku?.toLowerCase?.().includes(search)
      || item.supplier?.company_name?.toLowerCase?.().includes(search)
      || item.supplier?.partner?.code?.toLowerCase?.().includes(search)
  })
})

const pendingCount = computed(() => currentRows.value.filter(row => row.status === 'pending_review').length)
const approvedCount = computed(() => currentRows.value.filter(row => row.status === 'approved').length)
const blockedCount = computed(() => currentRows.value.filter(row => ['rejected', 'suspended', 'changes_requested'].includes(row.status)).length)

function readApiError(err: any) {
  const detail = err?.data?.error?.detail || err?.data?.detail || err?.message
  const errors = err?.data?.error?.errors || err?.data
  if (errors && typeof errors === 'object') {
    return Object.entries(errors).map(([field, messages]) => {
      const text = Array.isArray(messages) ? messages.join(' ') : String(messages)
      return `${field}: ${text}`
    }).join(' ')
  }
  return typeof detail === 'string' ? detail : 'Unknown error'
}

function formatStatus(status: string) {
  return status ? status.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()) : 'Unknown'
}

function statusColor(status: string) {
  if (status === 'approved')
    return 'success'
  if (status === 'rejected' || status === 'suspended')
    return 'error'
  if (status === 'changes_requested')
    return 'warning'
  return 'info'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function money(value: any, currency = 'KES') {
  if (value === null || value === undefined || value === '')
    return 'Not set'
  return `${currency || 'KES'} ${Number(value).toLocaleString()}`
}

function productTitle(item: any) {
  return item.product?.title || item.linked_product?.title || item.requested_title || 'Untitled product'
}

function productImage(item: any) {
  const product = item.product || item.linked_product || {}
  return product.image || product.thumbnail || ''
}

function getStatusOptions() {
  return activeTab.value === 'offers' ? statusOptions : requestStatusOptions
}

async function loadRows(page = 1) {
  isLoading.value = true
  const endpoint = activeTab.value === 'offers' ? '/admin/supplier-offers/' : '/admin/supplier-product-requests/'

  try {
    const result = await request<{ results: any[], pagination: any }>(endpoint, {
      method: 'GET',
      query: {
        status: statusFilter.value === ALL_STATUSES ? '' : statusFilter.value,
        page,
        page_size: pagination.value.page_size,
      },
    })
    if (activeTab.value === 'offers')
      offers.value = result.results || []
    else
      productRequests.value = result.results || []
    pagination.value = result.pagination || pagination.value
    selectedItem.value = currentRows.value.find(row => row.id === selectedItem.value?.id) || null
  }
  catch (err: any) {
    if (activeTab.value === 'offers')
      offers.value = []
    else
      productRequests.value = []
    toast.add({ title: 'Could not load supplier queue', description: readApiError(err), color: 'error' })
  }
  finally {
    isLoading.value = false
  }
}

function switchTab(tab: 'offers' | 'requests') {
  activeTab.value = tab
  statusFilter.value = 'pending_review'
  searchQuery.value = ''
  selectedItem.value = null
  loadRows(1)
}

function openDecision(item: any, status: string) {
  selectedItem.value = item
  decisionStatus.value = status
  reviewNote.value = ''
  saveError.value = ''
  linkedProduct.value = item.linked_product || null
  linkedProductSearch.value = item.linked_product?.title || ''
  linkedProductResults.value = []
  decisionOpen.value = true
}

async function searchLinkedProducts() {
  const query = linkedProductSearch.value.trim()
  if (query.length < 2) {
    linkedProductResults.value = []
    return
  }
  try {
    const result = await request<{ results: any[] }>('/catalog/products/', {
      method: 'GET',
      query: { q: query, page_size: 8 },
      redirectOnAuthError: false,
    })
    linkedProductResults.value = result.results || []
  }
  catch {
    linkedProductResults.value = []
  }
}

function selectLinkedProduct(product: any) {
  linkedProduct.value = product
  linkedProductSearch.value = product.title || ''
  linkedProductResults.value = []
}

async function submitDecision() {
  if (!selectedItem.value || !decisionStatus.value)
    return

  saveError.value = ''
  const needsNote = ['rejected', 'changes_requested', 'suspended'].includes(decisionStatus.value)
  if (needsNote && !reviewNote.value.trim()) {
    saveError.value = 'A review note is required for this decision.'
    return
  }

  const payload: Record<string, any> = {
    status: decisionStatus.value,
    review_note: reviewNote.value.trim(),
  }
  if (activeTab.value === 'requests') {
    if (decisionStatus.value === 'approved' && !linkedProduct.value?.id) {
      saveError.value = 'Link this request to an official catalogue product before approving.'
      return
    }
    payload.linked_product_id = linkedProduct.value?.id || null
  }

  isSaving.value = true
  const endpoint = activeTab.value === 'offers'
    ? `/admin/supplier-offers/${selectedItem.value.id}/`
    : `/admin/supplier-product-requests/${selectedItem.value.id}/`

  try {
    const result = await request<any>(endpoint, {
      method: 'PATCH',
      body: payload,
    })
    const updated = result.offer || result.request
    toast.add({
      title: 'Supplier queue updated',
      description: `${productTitle(updated)} is now ${formatStatus(updated.status)}.`,
      color: 'success',
    })
    decisionOpen.value = false
    selectedItem.value = updated
    await loadRows(pagination.value.page)
  }
  catch (err: any) {
    saveError.value = readApiError(err)
    toast.add({ title: 'Decision failed', description: saveError.value, color: 'error' })
  }
  finally {
    isSaving.value = false
  }
}

watch(statusFilter, () => loadRows(1))

onMounted(() => loadRows())
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Supplier Offers</h1>
        <p class="mt-1 text-sm text-slate-500">Approve supplier stock and cost offers against the official product catalogue.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UButtonGroup>
          <UButton :variant="activeTab === 'offers' ? 'solid' : 'outline'" color="primary" @click="switchTab('offers')">
            Stock offers
          </UButton>
          <UButton :variant="activeTab === 'requests' ? 'solid' : 'outline'" color="primary" @click="switchTab('requests')">
            Product requests
          </UButton>
        </UButtonGroup>
        <UInput v-model="searchQuery" class="min-w-56 flex-1 lg:max-w-sm" color="neutral" variant="outline" size="lg" icon="i-lucide-search" placeholder="Search product, supplier, SKU..." />
        <USelect v-model="statusFilter" :items="getStatusOptions()" class="w-52" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadRows(pagination.page)">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <CardsKpiCard2 :name="activeTab === 'offers' ? 'Loaded offers' : 'Loaded requests'" :value="currentRows.length" :budget="pagination.total || currentRows.length" color="#30328f" icon="i-lucide-list-checks" :loading="isLoading" />
      <CardsKpiCard2 name="Pending" :value="pendingCount" :budget="currentRows.length" color="#f59e0b" icon="i-lucide-clock" :loading="isLoading" />
      <CardsKpiCard2 name="Blocked" :value="blockedCount" :budget="currentRows.length" color="#dc2626" icon="i-lucide-ban" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-5">Product</div>
          <div class="col-span-3">Supplier</div>
          <div class="col-span-2">Commercials</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading supplier queue
        </div>

        <div v-else-if="filteredRows.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
            <UIcon name="i-lucide-package-search" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No supplier items found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another status filter or search term.</p>
        </div>

        <button
          v-for="item in filteredRows"
          v-else
          :key="item.id"
          type="button"
          class="grid w-full grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 text-left last:border-b-0 hover:bg-slate-50"
          :class="{ 'bg-blue-50/60': selectedItem?.id === item.id }"
          @click="selectedItem = item"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100 text-slate-500">
                <img v-if="productImage(item)" :src="productImage(item)" alt="" class="h-full w-full object-cover">
                <UIcon v-else name="i-lucide-box" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ productTitle(item) }}</p>
                <p class="truncate text-xs text-slate-500">
                  {{ item.product?.upc || item.product?.sku || item.supplier_sku || 'No SKU' }}
                </p>
              </div>
            </div>
          </div>
          <div class="col-span-3 min-w-0">
            <p class="truncate text-sm font-semibold text-slate-700">{{ item.supplier?.company_name || 'Unknown supplier' }}</p>
            <p class="truncate text-xs text-slate-500">{{ item.supplier?.account_manager?.name || item.supplier?.account_manager?.email || 'No account manager' }}</p>
          </div>
          <div class="col-span-2">
            <p class="text-sm font-bold text-slate-950">{{ money(item.supplier_unit_cost, item.currency) }}</p>
            <p class="text-xs text-slate-500">Qty {{ item.available_quantity || 0 }}</p>
            <UBadge :color="statusColor(item.status)" variant="soft" class="mt-1">{{ formatStatus(item.status) }}</UBadge>
          </div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip v-for="action in moderationActions.slice(0, 2)" :key="action.value" :text="action.label">
              <UButton :icon="action.icon" :color="action.color as any" variant="ghost" square :loading="isSaving" @click.stop="openDecision(item, action.value)" />
            </UTooltip>
          </div>
        </button>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Queue Detail</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedItem ? productTitle(selectedItem) : 'Select an item to inspect supplier details.' }}</p>
        </div>

        <div v-if="!selectedItem" class="p-8 text-center text-sm text-slate-500">
          Choose a supplier item from the queue.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-lg font-black text-slate-950">{{ productTitle(selectedItem) }}</p>
              <p class="truncate text-sm text-slate-500">Queue #{{ selectedItem.id }}</p>
            </div>
            <UBadge :color="statusColor(selectedItem.status)" variant="soft">{{ formatStatus(selectedItem.status) }}</UBadge>
          </div>

          <dl class="space-y-3 text-sm">
            <div>
              <dt class="font-semibold text-slate-500">Supplier</dt>
              <dd class="mt-1 text-slate-950">{{ selectedItem.supplier?.company_name }}</dd>
              <dd class="text-xs text-slate-500">{{ selectedItem.supplier?.user?.email }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Supplier cost</dt>
              <dd class="mt-1 text-slate-950">{{ money(selectedItem.supplier_unit_cost, selectedItem.currency) }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Available quantity</dt>
              <dd class="mt-1 text-slate-950">{{ selectedItem.available_quantity || 0 }}</dd>
            </div>
            <div v-if="activeTab === 'offers'">
              <dt class="font-semibold text-slate-500">Public selling price</dt>
              <dd class="mt-1 text-slate-950">{{ money(selectedItem.product?.price, selectedItem.product?.currency) }}</dd>
              <dd class="text-xs text-slate-500">Controlled by admin catalogue pricing, not supplier cost.</dd>
            </div>
            <div v-if="activeTab === 'requests'">
              <dt class="font-semibold text-slate-500">Requested catalogue details</dt>
              <dd class="mt-1 whitespace-pre-wrap text-slate-950">{{ selectedItem.description || 'No description supplied.' }}</dd>
              <dd class="mt-1 text-xs text-slate-500">{{ selectedItem.brand || 'No brand' }} - {{ selectedItem.category_hint || 'No category hint' }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Submitted</dt>
              <dd class="mt-1 text-slate-950">{{ formatDate(selectedItem.submitted_at) }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Review note</dt>
              <dd class="mt-1 whitespace-pre-wrap text-slate-950">{{ selectedItem.review_note || 'No review note recorded.' }}</dd>
            </div>
          </dl>

          <div class="mt-5 flex flex-wrap gap-2">
            <UButton v-for="action in moderationActions" :key="action.value" :color="action.color as any" variant="outline" :loading="isSaving" @click="openDecision(selectedItem, action.value)">
              <UIcon :name="action.icon" />
              {{ action.label }}
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4 flex flex-col gap-3 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
      <p>Showing {{ filteredRows.length }} of {{ pagination.total || currentRows.length }} items.</p>
      <div class="flex gap-2">
        <UButton color="neutral" variant="outline" :disabled="pagination.page <= 1 || isLoading" @click="loadRows(pagination.page - 1)">Previous</UButton>
        <UButton color="neutral" variant="outline" :disabled="!pagination.has_next || isLoading" @click="loadRows(pagination.page + 1)">Next</UButton>
      </div>
    </div>

    <div v-if="decisionOpen && selectedItem" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ formatStatus(decisionStatus) }}</h3>
              <p class="text-sm text-dimmed">{{ productTitle(selectedItem) }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="decisionOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div v-if="activeTab === 'requests' && decisionStatus === 'approved'" class="mb-4">
          <UFormField label="Link official catalogue product">
            <UInput v-model="linkedProductSearch" icon="i-lucide-search" placeholder="Search product to link..." @input="searchLinkedProducts" />
          </UFormField>
          <div v-if="linkedProductResults.length" class="mt-2 overflow-hidden rounded-lg border border-slate-200">
            <button
              v-for="product in linkedProductResults"
              :key="product.id"
              type="button"
              class="flex w-full items-center justify-between gap-3 border-b border-slate-100 px-3 py-2 text-left text-sm last:border-b-0 hover:bg-slate-50"
              @click="selectLinkedProduct(product)"
            >
              <span class="min-w-0 truncate font-semibold text-slate-800">{{ product.title }}</span>
              <span class="shrink-0 text-xs text-slate-500">{{ product.upc || product.sku || product.id }}</span>
            </button>
          </div>
          <p v-if="linkedProduct" class="mt-2 text-sm font-semibold text-emerald-700">
            Linked to {{ linkedProduct.title }}
          </p>
        </div>

        <UFormField label="Review note">
          <UTextarea v-model="reviewNote" :rows="5" placeholder="Add feedback for supplier or internal moderation context." />
        </UFormField>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="decisionOpen = false">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitDecision">Save decision</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
