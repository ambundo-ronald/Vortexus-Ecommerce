<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const auth = useAuth()
const toast = useToast()
const { request } = useBackendApi()
const { createOffer, createProductRequest, getDashboard, getOffers, getProductRequests, getProducts, getOrders } = useSupplierWorkspace()

const isLoading = ref(false)
const isSaving = ref(false)
const dashboard = ref<any | null>(null)
const products = ref<any[]>([])
const offers = ref<any[]>([])
const productRequests = ref<any[]>([])
const orders = ref<any[]>([])
const offerModalOpen = ref(false)
const productRequestModalOpen = ref(false)
const productSearch = ref('')
const productSearchResults = ref<any[]>([])
const selectedCatalogueProduct = ref<any | null>(null)
const offerForm = reactive({
  supplier_unit_cost: '',
  available_quantity: 0,
  supplier_sku: '',
  lead_time_days: 0,
  notes: '',
})
const productRequestForm = reactive({
  requested_title: '',
  brand: '',
  category_hint: '',
  description: '',
  supplier_sku: '',
  supplier_unit_cost: '',
  available_quantity: 0,
  notes: '',
})
let productSearchTimer: ReturnType<typeof setTimeout> | null = null

const currency = computed(() => {
  const firstOrderCurrency = orders.value.find(order => order.currency)?.currency
  const firstOfferCurrency = offers.value.find(offer => offer.currency)?.currency
  const firstProductCurrency = products.value.find(product => product.offer?.currency)?.offer?.currency
  return firstOrderCurrency || firstOfferCurrency || firstProductCurrency || 'KES'
})

const moneyFormatter = computed(() =>
  new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: currency.value,
    maximumFractionDigits: 0,
  }),
)

const statusColor = computed(() => {
  const status = dashboard.value?.supplier?.status || auth.user.value?.supplier?.status || ''
  if (status === 'approved')
    return 'success'
  if (status === 'suspended')
    return 'error'
  return 'warning'
})

const statusCopy = computed(() => {
  const status = dashboard.value?.supplier?.status || auth.user.value?.supplier?.status || 'pending'
  if (status === 'approved')
    return 'Your supplier account is approved. You can manage products and fulfill assigned orders.'
  if (status === 'suspended')
    return 'Your supplier account is suspended. Product and order updates are restricted until support reviews it.'
  return 'Your supplier application is pending review. You can view status here; selling tools unlock after approval.'
})

const metrics = computed(() => dashboard.value?.metrics || {})
const payments = computed(() => dashboard.value?.payments || {})

const productColumns: TableColumn<any>[] = [
  {
    accessorKey: 'title',
    header: 'Product',
    cell: ({ row }) => h('div', { class: 'min-w-0' }, [
      h('p', { class: 'truncate font-semibold text-slate-950 dark:text-white' }, row.original.title || 'Untitled product'),
      h('p', { class: 'truncate text-xs text-slate-500' }, row.original.sku || row.original.upc || 'No SKU'),
    ]),
  },
  {
    accessorKey: 'moderation.status',
    header: 'Review',
    cell: ({ row }) => h(resolveComponent('UBadge'), {
      label: formatStatus(row.original.moderation?.status || 'pending_review'),
      color: moderationColor(row.original.moderation?.status),
      variant: 'soft',
    }),
  },
  {
    accessorKey: 'offer.num_in_stock',
    header: 'Stock',
    cell: ({ row }) => `${Number(row.original.offer?.num_in_stock || row.original.stock_count || 0).toLocaleString()} units`,
  },
  {
    accessorKey: 'offer.price',
    header: 'Price',
    cell: ({ row }) => moneyFormatter.value.format(Number(row.original.offer?.price || row.original.price || 0)),
  },
]

const offerColumns: TableColumn<any>[] = [
  {
    accessorKey: 'product.title',
    header: 'Catalogue product',
    cell: ({ row }) => h('div', { class: 'min-w-0' }, [
      h('p', { class: 'truncate font-semibold text-slate-950 dark:text-white' }, row.original.product?.title || 'Untitled product'),
      h('p', { class: 'truncate text-xs text-slate-500' }, row.original.product?.sku || row.original.product?.upc || 'No SKU'),
    ]),
  },
  {
    accessorKey: 'status',
    header: 'Review',
    cell: ({ row }) => h(resolveComponent('UBadge'), {
      label: formatStatus(row.original.status || 'pending_review'),
      color: moderationColor(row.original.status),
      variant: 'soft',
    }),
  },
  {
    accessorKey: 'available_quantity',
    header: 'Qty',
    cell: ({ row }) => `${Number(row.original.available_quantity || 0).toLocaleString()} units`,
  },
  {
    accessorKey: 'supplier_unit_cost',
    header: 'Your cost',
    cell: ({ row }) => moneyFormatter.value.format(Number(row.original.supplier_unit_cost || 0)),
  },
]

const productRequestColumns: TableColumn<any>[] = [
  {
    accessorKey: 'requested_title',
    header: 'Requested product',
    cell: ({ row }) => h('div', { class: 'min-w-0' }, [
      h('p', { class: 'truncate font-semibold text-slate-950 dark:text-white' }, row.original.requested_title || 'Untitled request'),
      h('p', { class: 'truncate text-xs text-slate-500' }, row.original.brand || row.original.category_hint || 'No brand/category'),
    ]),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => h(resolveComponent('UBadge'), {
      label: formatStatus(row.original.status || 'pending_review'),
      color: moderationColor(row.original.status),
      variant: 'soft',
    }),
  },
  {
    accessorKey: 'linked_product',
    header: 'Linked product',
    cell: ({ row }) => row.original.linked_product?.title || 'Not linked yet',
  },
]

const orderColumns: TableColumn<any>[] = [
  {
    accessorKey: 'number',
    header: 'Order',
    cell: ({ row }) => `#${row.original.number}`,
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => h(resolveComponent('UBadge'), {
      label: formatStatus(row.original.status || 'pending'),
      color: orderStatusColor(row.original.status),
      variant: 'soft',
    }),
  },
  {
    accessorKey: 'supplier_item_count',
    header: 'Items',
    cell: ({ row }) => Number(row.original.supplier_item_count || 0).toLocaleString(),
  },
  {
    accessorKey: 'supplier_total_incl_tax',
    header: 'Sales',
    cell: ({ row }) => moneyFormatter.value.format(Number(row.original.supplier_total_incl_tax || 0)),
  },
]

async function loadWorkspace() {
  isLoading.value = true
  const [dashboardResult, productsResult, ordersResult] = await Promise.all([
    getDashboard(),
    getProducts({ pageSize: 8 }),
    getOrders({ pageSize: 8 }),
  ])
  const [offersResult, requestsResult] = await Promise.all([
    getOffers({ pageSize: 8 }),
    getProductRequests({ pageSize: 8 }),
  ])

  if (dashboardResult.success)
    dashboard.value = dashboardResult.data
  else
    toast.add({ title: 'Could not load supplier dashboard', description: dashboardResult.error || 'Please try again.', color: 'error' })

  products.value = productsResult.success ? productsResult.data?.results || [] : []
  offers.value = offersResult.success ? offersResult.data?.results || [] : []
  productRequests.value = requestsResult.success ? requestsResult.data?.results || [] : []
  orders.value = ordersResult.success ? ordersResult.data?.results || [] : []
  isLoading.value = false
}

function formatMoney(value: number | string | undefined) {
  return moneyFormatter.value.format(Number(value || 0))
}

function formatStatus(value: string = '') {
  return value.replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase()) || 'Pending'
}

function moderationColor(value: string = '') {
  if (value === 'approved')
    return 'success'
  if (['rejected', 'suspended'].includes(value))
    return 'error'
  if (value === 'changes_requested')
    return 'warning'
  return 'neutral'
}

function orderStatusColor(value: string = '') {
  if (['delivered', 'shipped'].includes(value))
    return 'success'
  if (value === 'cancelled')
    return 'error'
  if (['packed', 'processing', 'partially_shipped'].includes(value))
    return 'warning'
  return 'neutral'
}

function resetOfferForm() {
  selectedCatalogueProduct.value = null
  productSearch.value = ''
  productSearchResults.value = []
  offerForm.supplier_unit_cost = ''
  offerForm.available_quantity = 0
  offerForm.supplier_sku = ''
  offerForm.lead_time_days = 0
  offerForm.notes = ''
}

function resetProductRequestForm() {
  productRequestForm.requested_title = ''
  productRequestForm.brand = ''
  productRequestForm.category_hint = ''
  productRequestForm.description = ''
  productRequestForm.supplier_sku = ''
  productRequestForm.supplier_unit_cost = ''
  productRequestForm.available_quantity = 0
  productRequestForm.notes = ''
}

function openOfferModal() {
  resetOfferForm()
  offerModalOpen.value = true
}

function openProductRequestModal() {
  resetProductRequestForm()
  productRequestModalOpen.value = true
}

function queueProductSearch() {
  if (productSearchTimer)
    clearTimeout(productSearchTimer)
  productSearchTimer = setTimeout(searchCatalogueProducts, 300)
}

async function searchCatalogueProducts() {
  const query = productSearch.value.trim()
  selectedCatalogueProduct.value = null
  if (query.length < 2) {
    productSearchResults.value = []
    return
  }
  try {
    const result = await request<{ results: any[] }>('/catalog/products/', {
      method: 'GET',
      query: { q: query, page_size: 8 },
    })
    productSearchResults.value = result.results || []
  }
  catch {
    productSearchResults.value = []
  }
}

function selectCatalogueProduct(product: any) {
  selectedCatalogueProduct.value = product
  productSearch.value = product.title || product.sku || ''
  productSearchResults.value = []
  if (!offerForm.supplier_sku)
    offerForm.supplier_sku = product.sku || product.upc || ''
}

async function submitOffer() {
  if (!selectedCatalogueProduct.value) {
    toast.add({ title: 'Select a catalogue product first', color: 'warning' })
    return
  }
  if (!offerForm.supplier_unit_cost || Number(offerForm.supplier_unit_cost) <= 0) {
    toast.add({ title: 'Enter your supplier cost', color: 'warning' })
    return
  }
  isSaving.value = true
  const result = await createOffer({
    product_id: selectedCatalogueProduct.value.id,
    supplier_unit_cost: offerForm.supplier_unit_cost,
    currency: currency.value,
    available_quantity: Number(offerForm.available_quantity || 0),
    lead_time_days: Number(offerForm.lead_time_days || 0),
    supplier_sku: offerForm.supplier_sku,
    notes: offerForm.notes,
  })
  if (result.success) {
    toast.add({ title: 'Offer submitted for review', color: 'success' })
    offerModalOpen.value = false
    await loadWorkspace()
  }
  else {
    toast.add({ title: 'Offer failed', description: result.error || 'Could not submit offer.', color: 'error' })
  }
  isSaving.value = false
}

async function submitProductRequest() {
  if (!productRequestForm.requested_title.trim()) {
    toast.add({ title: 'Product name is required', color: 'warning' })
    return
  }
  isSaving.value = true
  const result = await createProductRequest({
    requested_title: productRequestForm.requested_title,
    brand: productRequestForm.brand,
    category_hint: productRequestForm.category_hint,
    description: productRequestForm.description,
    supplier_sku: productRequestForm.supplier_sku,
    supplier_unit_cost: productRequestForm.supplier_unit_cost || undefined,
    currency: currency.value,
    available_quantity: Number(productRequestForm.available_quantity || 0),
    notes: productRequestForm.notes,
  })
  if (result.success) {
    toast.add({ title: 'Product request submitted', color: 'success' })
    productRequestModalOpen.value = false
    await loadWorkspace()
  }
  else {
    toast.add({ title: 'Request failed', description: result.error || 'Could not submit request.', color: 'error' })
  }
  isSaving.value = false
}

onMounted(loadWorkspace)
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-8">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wide text-primary">
          Supplier workspace
        </p>
        <h1 class="text-xl font-semibold">
          {{ dashboard?.supplier?.company_name || auth.user.value?.supplier?.company_name || 'Supplier dashboard' }}
        </h1>
        <p class="text-sm text-toned">
          Products, sales, and payment visibility for your supplier account.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <UButton color="primary" icon="i-lucide-plus" :disabled="dashboard?.supplier?.status !== 'approved'" @click="openOfferModal">
          Add stock offer
        </UButton>
        <UButton variant="outline" icon="i-lucide-file-plus-2" :disabled="dashboard?.supplier?.status !== 'approved'" @click="openProductRequestModal">
          Request product
        </UButton>
        <UButton variant="outline" icon="i-lucide-refresh-cw" :loading="isLoading" @click="loadWorkspace">
          Refresh
        </UButton>
      </div>
    </div>

    <div class="px-4 md:px-8">
      <UAlert
        :color="statusColor"
        variant="soft"
        icon="i-lucide-store"
        :title="formatStatus(dashboard?.supplier?.status || auth.user.value?.supplier?.status || 'pending')"
        :description="statusCopy"
      />
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-4">
      <CardsKpiCard2
        name="Products"
        :value="metrics.approved_offer_count || metrics.product_count || 0"
        :budget="metrics.offer_count || metrics.product_count || 0"
        color="var(--color-primary)"
        icon="i-lucide-box"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Open orders"
        :value="metrics.open_order_count || 0"
        :budget="metrics.order_count || 0"
        color="var(--color-warning)"
        icon="i-lucide-receipt"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Gross sales"
        :value="Number(metrics.gross_sales_total || 0)"
        :budget="Number(metrics.gross_sales_total || 0)"
        format="currency"
        :currency="currency"
        color="var(--color-success)"
        icon="i-lucide-chart-no-axes-combined"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Confirmed payable"
        :value="Number(metrics.confirmed_payable_total || metrics.confirmed_payment_total || 0)"
        :budget="Number(metrics.confirmed_payable_total || metrics.confirmed_payment_total || 0)"
        format="currency"
        :currency="currency"
        color="var(--color-info)"
        icon="i-lucide-banknote"
        :loading="isLoading"
      />
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 md:px-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">
                Stock offers
              </h3>
              <p class="text-sm text-toned">
                Pick existing catalogue products, then submit your cost and stock for approval.
              </p>
            </div>
            <UBadge color="warning" variant="soft">{{ metrics.pending_offer_count || 0 }} pending</UBadge>
          </div>
        </template>
        <UTable :columns="offerColumns" :data="offers" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">
                Product requests
              </h3>
              <p class="text-sm text-toned">
                Request a catalogue product when you cannot find it in search.
              </p>
            </div>
            <UBadge color="neutral" variant="soft">{{ productRequests.length }} loaded</UBadge>
          </div>
        </template>
        <UTable :columns="productRequestColumns" :data="productRequests" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 md:px-8 xl:grid-cols-3">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">
              Payment summary
            </h3>
            <p class="text-sm text-toned">
              Settlement ledger will be added in the next phase.
            </p>
          </div>
        </template>
        <div class="space-y-4 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-toned">Confirmed customer payments</span>
            <span class="font-semibold">{{ formatMoney(payments.confirmed_total) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-toned">Awaiting payment confirmation</span>
            <span class="font-semibold">{{ formatMoney(payments.pending_total) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-toned">Paid out to supplier</span>
            <span class="font-semibold">{{ formatMoney(payments.paid_out_total) }}</span>
          </div>
          <USeparator />
          <div class="flex items-center justify-between">
            <span class="text-toned">Basis</span>
            <UBadge color="neutral" variant="soft">{{ formatStatus(payments.basis || 'confirmed_customer_payment') }}</UBadge>
          </div>
        </div>
      </UCard>

      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">
                Recent supplier orders
              </h3>
              <p class="text-sm text-toned">
                Only orders assigned to your supplier partner appear here.
              </p>
            </div>
            <UBadge color="neutral" variant="soft">{{ metrics.order_count || 0 }} total</UBadge>
          </div>
        </template>
        <UTable :columns="orderColumns" :data="orders" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-6 px-4 pb-8 md:px-8">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">
                Supplier products
              </h3>
              <p class="text-sm text-toned">
                Product visibility depends on admin review status.
              </p>
            </div>
            <div class="flex items-center gap-2">
              <UBadge color="success" variant="soft">{{ metrics.public_product_count || 0 }} public</UBadge>
              <UBadge color="warning" variant="soft">{{ metrics.pending_product_count || 0 }} pending</UBadge>
            </div>
          </div>
        </template>
        <UTable :columns="productColumns" :data="products" :loading="isLoading" />
      </UCard>
    </div>

    <div v-if="offerModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">Add stock offer</h3>
              <p class="text-sm text-dimmed">Search the official catalogue, then submit your cost and available quantity.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="offerModalOpen = false" />
          </div>
        </template>

        <div class="space-y-4">
          <UFormField label="Catalogue product" required>
            <div class="relative">
              <UInput v-model="productSearch" icon="i-lucide-search" autocomplete="off" placeholder="Search product name, SKU, brand..." @input="queueProductSearch" />
              <div v-if="productSearchResults.length" class="absolute z-50 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white p-1 shadow-xl">
                <button
                  v-for="product in productSearchResults"
                  :key="product.id"
                  type="button"
                  class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left hover:bg-blue-50"
                  @mousedown.prevent="selectCatalogueProduct(product)"
                >
                  <img v-if="product.thumbnail" :src="product.thumbnail" alt="" class="h-10 w-10 rounded-md object-cover">
                  <span v-else class="flex h-10 w-10 items-center justify-center rounded-md bg-slate-100"><UIcon name="i-lucide-box" /></span>
                  <span class="min-w-0">
                    <span class="block truncate text-sm font-semibold text-slate-950">{{ product.title }}</span>
                    <span class="block truncate text-xs text-slate-500">{{ product.sku || product.upc || 'No SKU' }} · {{ product.currency || currency }} {{ Number(product.price || 0).toLocaleString() }}</span>
                  </span>
                </button>
              </div>
            </div>
          </UFormField>

          <div v-if="selectedCatalogueProduct" class="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm">
            Selected: <span class="font-semibold">{{ selectedCatalogueProduct.title }}</span>
          </div>

          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <UFormField label="Your supplier cost" required><UInput v-model="offerForm.supplier_unit_cost" type="number" min="0" step="0.01" /></UFormField>
            <UFormField label="Available quantity" required><UInput v-model.number="offerForm.available_quantity" type="number" min="0" /></UFormField>
            <UFormField label="Supplier SKU"><UInput v-model="offerForm.supplier_sku" autocomplete="off" /></UFormField>
            <UFormField label="Lead time days"><UInput v-model.number="offerForm.lead_time_days" type="number" min="0" /></UFormField>
            <UFormField label="Notes" class="md:col-span-2"><UTextarea v-model="offerForm.notes" :rows="4" /></UFormField>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="offerModalOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="isSaving" @click="submitOffer">Submit for approval</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="productRequestModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">Request new product</h3>
              <p class="text-sm text-dimmed">Use this when the official catalogue does not have the product yet.</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="productRequestModalOpen = false" />
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Product name" required class="md:col-span-2"><UInput v-model="productRequestForm.requested_title" autocomplete="off" /></UFormField>
          <UFormField label="Brand"><UInput v-model="productRequestForm.brand" autocomplete="off" /></UFormField>
          <UFormField label="Category suggestion"><UInput v-model="productRequestForm.category_hint" autocomplete="off" /></UFormField>
          <UFormField label="Supplier SKU"><UInput v-model="productRequestForm.supplier_sku" autocomplete="off" /></UFormField>
          <UFormField label="Available quantity"><UInput v-model.number="productRequestForm.available_quantity" type="number" min="0" /></UFormField>
          <UFormField label="Your supplier cost"><UInput v-model="productRequestForm.supplier_unit_cost" type="number" min="0" step="0.01" /></UFormField>
          <UFormField label="Description" class="md:col-span-2"><UTextarea v-model="productRequestForm.description" :rows="4" /></UFormField>
          <UFormField label="Notes" class="md:col-span-2"><UTextarea v-model="productRequestForm.notes" :rows="3" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="productRequestModalOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="isSaving" @click="submitProductRequest">Submit request</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
