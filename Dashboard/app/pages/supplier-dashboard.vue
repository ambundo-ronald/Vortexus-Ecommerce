<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const auth = useAuth()
const toast = useToast()
const { getDashboard, getProducts, getOrders } = useSupplierWorkspace()

const isLoading = ref(false)
const dashboard = ref<any | null>(null)
const products = ref<any[]>([])
const orders = ref<any[]>([])

const currency = computed(() => {
  const firstOrderCurrency = orders.value.find(order => order.currency)?.currency
  const firstProductCurrency = products.value.find(product => product.offer?.currency)?.offer?.currency
  return firstOrderCurrency || firstProductCurrency || 'KES'
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

  if (dashboardResult.success)
    dashboard.value = dashboardResult.data
  else
    toast.add({ title: 'Could not load supplier dashboard', description: dashboardResult.error || 'Please try again.', color: 'error' })

  products.value = productsResult.success ? productsResult.data?.results || [] : []
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
      <UButton variant="outline" icon="i-lucide-refresh-cw" :loading="isLoading" @click="loadWorkspace">
        Refresh
      </UButton>
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
        :value="metrics.product_count || 0"
        :budget="metrics.product_count || 0"
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
        name="Confirmed payments"
        :value="Number(metrics.confirmed_payment_total || 0)"
        :budget="Number(metrics.confirmed_payment_total || 0)"
        format="currency"
        :currency="currency"
        color="var(--color-info)"
        icon="i-lucide-banknote"
        :loading="isLoading"
      />
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
  </div>
</template>
