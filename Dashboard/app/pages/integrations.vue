<script setup lang="ts">
import type { ERPNextPreviewResource, ERPNextPreviewResult, IntegrationConnection, IntegrationConnectionPayload, IntegrationLog } from '~/composables/useIntegrations'

const toast = useToast()
const { getConnections, createConnection, updateConnection, getLogs, testConnection, syncStock, previewERPNext, importERPNextCatalog } = useIntegrations()

const connections = ref<IntegrationConnection[]>([])
const selectedConnection = ref<IntegrationConnection | null>(null)
const logs = ref<IntegrationLog[]>([])
const isLoading = ref(false)
const actionId = ref<number | null>(null)
const previewActionId = ref<number | null>(null)
const importActionId = ref<number | null>(null)
const previewResource = ref<ERPNextPreviewResource>('items')
const previewLimit = ref(20)
const previewResult = ref<ERPNextPreviewResult | null>(null)
const previewConnection = ref<IntegrationConnection | null>(null)
const importIncludeStock = ref(true)
const importSummary = ref<Record<string, any> | null>(null)
const isEditorOpen = ref(false)
const isSavingConnection = ref(false)
const editingConnectionId = ref<number | null>(null)
const connectionForm = ref({
  name: '',
  base_url: '',
  credential_source: 'db',
  secret_env_prefix: '',
  api_key: '',
  api_secret: '',
  default_company: '',
  default_warehouse: '',
  poll_interval_minutes: 20,
  is_active: true,
  price_list: 'Standard Selling',
  item_groups_text: '',
  default_currency: '',
  partner_name: '',
  product_class: 'Industrial Product',
  use_vortexus_bridge_app: false,
  sync_customers: true,
  export_orders: true,
  export_order_accounting: true,
  sync_cancellations: true,
  sync_refunds: true,
  customer_group: 'Ecommerce',
  territory: 'Kenya',
  pesapal_bank_account: '',
  delivery_days: 7,
})

const previewResourceOptions = [
  { label: 'Items', value: 'items' },
  { label: 'Stock', value: 'stock' },
  { label: 'Prices', value: 'prices' },
]

const previewLimitOptions = [
  { label: '10 records', value: 10 },
  { label: '20 records', value: 20 },
  { label: '50 records', value: 50 },
  { label: '100 records', value: 100 },
]

const credentialSourceOptions = [
  { label: 'Saved in dashboard', value: 'db' },
  { label: 'Environment variables', value: 'env' },
]

const activeConnections = computed(() => connections.value.filter(connection => connection.is_active).length)
const healthyConnections = computed(() => connections.value.filter(connection => connection.status === 'active').length)
const errorConnections = computed(() => connections.value.filter(connection => connection.status === 'error').length)
const previewColumns = computed(() => {
  const firstRecord = previewResult.value?.records?.[0]
  if (!firstRecord)
    return []

  return Object.keys(firstRecord).slice(0, 7)
})

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '')
    return '-'

  if (typeof value === 'object')
    return JSON.stringify(value)

  return String(value)
}

function statusColor(status: string) {
  if (status === 'active')
    return 'success'
  if (status === 'error')
    return 'error'
  if (status === 'disabled')
    return 'neutral'
  return 'warning'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Never'

  return new Date(value).toLocaleString('en-KE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

async function loadLogs(connection: IntegrationConnection) {
  selectedConnection.value = connection
  const result = await getLogs(connection.id)
  logs.value = result.data || []

  if (!result.success) {
    toast.add({
      title: 'Could not load logs',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }
}

async function loadConnections() {
  isLoading.value = true
  const result = await getConnections()

  if (result.success) {
    connections.value = result.data || []
    if (!selectedConnection.value && connections.value.length)
      await loadLogs(connections.value[0])
  }
  else {
    connections.value = []
    toast.add({
      title: 'Could not load integrations',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function runTest(connection: IntegrationConnection) {
  actionId.value = connection.id
  const result = await testConnection(connection.id)

  toast.add({
    title: result.success ? 'Connection is reachable' : 'Connection test failed',
    description: result.success ? 'The backend confirmed this connection.' : result.error || 'Please check the connection.',
    color: result.success ? 'success' : 'error',
  })

  await loadConnections()
  actionId.value = null
}

function resetConnectionForm() {
  editingConnectionId.value = null
  connectionForm.value = {
    name: '',
    base_url: '',
    credential_source: 'db',
    secret_env_prefix: '',
    api_key: '',
    api_secret: '',
    default_company: '',
    default_warehouse: '',
    poll_interval_minutes: 20,
    is_active: true,
    price_list: 'Standard Selling',
    item_groups_text: '',
    default_currency: '',
    partner_name: '',
    product_class: 'Industrial Product',
    use_vortexus_bridge_app: false,
    sync_customers: true,
    export_orders: true,
    export_order_accounting: true,
    sync_cancellations: true,
    sync_refunds: true,
    customer_group: 'Ecommerce',
    territory: 'Kenya',
    pesapal_bank_account: '',
    delivery_days: 7,
  }
}

function openNewConnection() {
  resetConnectionForm()
  isEditorOpen.value = true
}

function openEditConnection(connection: IntegrationConnection) {
  editingConnectionId.value = connection.id
  const metadata = connection.metadata || {}
  connectionForm.value = {
    name: connection.name || '',
    base_url: connection.base_url || '',
    credential_source: connection.credential_source || 'db',
    secret_env_prefix: connection.secret_env_prefix || '',
    api_key: '',
    api_secret: '',
    default_company: connection.default_company || '',
    default_warehouse: connection.default_warehouse || '',
    poll_interval_minutes: Number(connection.poll_interval_minutes || 20),
    is_active: Boolean(connection.is_active),
    price_list: metadata.price_list || 'Standard Selling',
    item_groups_text: Array.isArray(metadata.item_groups) ? metadata.item_groups.join(', ') : '',
    default_currency: metadata.default_currency || '',
    partner_name: metadata.partner_name || '',
    product_class: metadata.product_class || 'Industrial Product',
    use_vortexus_bridge_app: Boolean(metadata.use_vortexus_bridge_app),
    sync_customers: metadata.sync_customers !== false,
    export_orders: metadata.export_orders !== false,
    export_order_accounting: metadata.export_order_accounting !== false,
    sync_cancellations: metadata.sync_cancellations !== false,
    sync_refunds: metadata.sync_refunds !== false,
    customer_group: metadata.customer_group || 'Ecommerce',
    territory: metadata.territory || 'Kenya',
    pesapal_bank_account: metadata.pesapal_bank_account || '',
    delivery_days: Number(metadata.delivery_days || 7),
  }
  isEditorOpen.value = true
}

function buildConnectionPayload(): IntegrationConnectionPayload {
  const metadata: Record<string, any> = {
    price_list: connectionForm.value.price_list.trim(),
    item_groups: connectionForm.value.item_groups_text
      .split(',')
      .map(item => item.trim())
      .filter(Boolean),
    default_currency: connectionForm.value.default_currency.trim(),
    partner_name: connectionForm.value.partner_name.trim(),
    product_class: connectionForm.value.product_class.trim(),
    use_vortexus_bridge_app: connectionForm.value.use_vortexus_bridge_app,
    sync_customers: connectionForm.value.sync_customers,
    export_orders: connectionForm.value.export_orders,
    export_order_accounting: connectionForm.value.export_order_accounting,
    sync_cancellations: connectionForm.value.sync_cancellations,
    sync_refunds: connectionForm.value.sync_refunds,
    customer_group: connectionForm.value.customer_group.trim(),
    territory: connectionForm.value.territory.trim(),
    pesapal_bank_account: connectionForm.value.pesapal_bank_account.trim(),
    delivery_days: Number(connectionForm.value.delivery_days || 7),
  }

  Object.keys(metadata).forEach((key) => {
    if (typeof metadata[key] === 'boolean' || typeof metadata[key] === 'number')
      return
    if (Array.isArray(metadata[key]) ? metadata[key].length === 0 : !metadata[key])
      delete metadata[key]
  })

  const payload: IntegrationConnectionPayload = {
    name: connectionForm.value.name.trim(),
    connection_type: 'erpnext',
    base_url: connectionForm.value.base_url.trim(),
    auth_type: 'token',
    credential_source: connectionForm.value.credential_source,
    secret_env_prefix: connectionForm.value.secret_env_prefix.trim(),
    default_company: connectionForm.value.default_company.trim(),
    default_warehouse: connectionForm.value.default_warehouse.trim(),
    poll_interval_minutes: Number(connectionForm.value.poll_interval_minutes || 20),
    is_active: connectionForm.value.is_active,
    metadata,
  }

  if (connectionForm.value.credential_source === 'db') {
    if (connectionForm.value.api_key)
      payload.api_key = connectionForm.value.api_key
    if (connectionForm.value.api_secret)
      payload.api_secret = connectionForm.value.api_secret
  }

  return payload
}

async function saveConnection() {
  isSavingConnection.value = true
  const payload = buildConnectionPayload()
  const result = editingConnectionId.value
    ? await updateConnection(editingConnectionId.value, payload)
    : await createConnection(payload)

  if (result.success && result.data) {
    toast.add({
      title: editingConnectionId.value ? 'ERPNext integration updated' : 'ERPNext integration created',
      description: 'The dashboard can now test, preview, import, and sync with this ERPNext connection.',
      color: 'success',
    })
    isEditorOpen.value = false
    resetConnectionForm()
    await loadConnections()
    await loadLogs(result.data)
  }
  else {
    toast.add({
      title: 'Could not save ERPNext integration',
      description: result.error || 'Please check the form and try again.',
      color: 'error',
    })
  }

  isSavingConnection.value = false
}

async function runPreview(connection: IntegrationConnection) {
  previewActionId.value = connection.id
  previewConnection.value = connection
  selectedConnection.value = connection

  const result = await previewERPNext(connection.id, {
    resource: previewResource.value,
    limit: previewLimit.value,
  })

  if (result.success && result.data) {
    previewResult.value = result.data
    toast.add({
      title: 'Preview loaded',
      description: `${result.data.count} ${result.data.resource} records returned from ERPNext.`,
      color: 'success',
    })
  }
  else {
    previewResult.value = null
    toast.add({
      title: 'Preview failed',
      description: result.error || 'Please check the ERPNext connection.',
      color: 'error',
    })
  }

  previewActionId.value = null
}

async function runCatalogImport(connection: IntegrationConnection) {
  importActionId.value = connection.id
  selectedConnection.value = connection
  importSummary.value = null

  const result = await importERPNextCatalog(connection.id, {
    include_stock: importIncludeStock.value,
  })

  if (result.success) {
    importSummary.value = result.data || {}
    toast.add({
      title: 'Catalog import finished',
      description: importIncludeStock.value ? 'Catalog and stock data were imported from ERPNext.' : 'Catalog data was imported from ERPNext.',
      color: 'success',
    })
    await loadConnections()
    await loadLogs(connection)
  }
  else {
    toast.add({
      title: 'Catalog import failed',
      description: result.error || 'Please check the ERPNext connection.',
      color: 'error',
    })
  }

  importActionId.value = null
}

async function runStockSync(connection: IntegrationConnection) {
  actionId.value = connection.id
  const result = await syncStock(connection.id)

  toast.add({
    title: result.success ? 'Stock sync finished' : 'Stock sync failed',
    description: result.success ? 'Inventory values were refreshed from the connection.' : result.error || 'Please try again.',
    color: result.success ? 'success' : 'error',
  })

  await loadConnections()
  actionId.value = null
}

onMounted(loadConnections)
</script>

<template>
  <div class="px-4 py-8 sm:px-6 lg:px-10">
    <div class="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <h1 class="text-3xl font-black tracking-tight text-slate-950">
          Integrations
        </h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-600">
          Monitor connected business systems, test connectivity, and sync stock where supported by the backend.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <UButton color="primary" size="lg" icon="i-lucide-plus" @click="openNewConnection">
          New ERPNext Integration
        </UButton>
        <UButton variant="outline" size="lg" :loading="isLoading" @click="loadConnections">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <CardsKpiCard2 name="Connections" :value="connections.length" :budget="connections.length" color="#3d7cff" />
      <CardsKpiCard2 name="Active" :value="activeConnections" :budget="connections.length" color="#16a34a" />
      <CardsKpiCard2 name="Needs attention" :value="errorConnections" :budget="connections.length" color="#ef4444" />
    </div>

    <div v-if="isEditorOpen" class="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-200 px-5 py-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 class="text-lg font-black text-slate-950">
              {{ editingConnectionId ? 'Edit ERPNext integration' : 'New ERPNext integration' }}
            </h2>
            <p class="mt-1 text-sm text-slate-500">
              Configure catalog, price list, warehouse, and credentials used by backend sync jobs.
            </p>
          </div>
          <UButton color="neutral" variant="ghost" icon="i-lucide-x" @click="isEditorOpen = false">
            Close
          </UButton>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 p-5 md:grid-cols-2 xl:grid-cols-3">
        <UFormField label="Connection name" required>
          <UInput v-model="connectionForm.name" placeholder="ERPNext Main" />
        </UFormField>
        <UFormField label="ERPNext URL" required>
          <UInput v-model="connectionForm.base_url" placeholder="https://erp.example.com" />
        </UFormField>
        <UFormField label="Credential source">
          <USelect v-model="connectionForm.credential_source" :items="credentialSourceOptions" class="w-full" />
        </UFormField>

        <UFormField v-if="connectionForm.credential_source === 'env'" label="Secret env prefix" required>
          <UInput v-model="connectionForm.secret_env_prefix" placeholder="ERPNEXT_MAIN" />
        </UFormField>
        <UFormField v-if="connectionForm.credential_source === 'db'" label="API key">
          <PasswordInput v-model="connectionForm.api_key" :placeholder="editingConnectionId ? 'Saved if already configured' : 'ERPNext API key'" autocomplete="new-password" />
        </UFormField>
        <UFormField v-if="connectionForm.credential_source === 'db'" label="API secret">
          <PasswordInput v-model="connectionForm.api_secret" :placeholder="editingConnectionId ? 'Saved if already configured' : 'ERPNext API secret'" autocomplete="new-password" />
        </UFormField>

        <UFormField label="Company">
          <UInput v-model="connectionForm.default_company" placeholder="Company name in ERPNext" />
        </UFormField>
        <UFormField label="Warehouse">
          <UInput v-model="connectionForm.default_warehouse" placeholder="Stores - Company" />
        </UFormField>
        <UFormField label="Selling price list">
          <UInput v-model="connectionForm.price_list" placeholder="Standard Selling" />
        </UFormField>
        <UFormField label="Item groups">
          <UInput v-model="connectionForm.item_groups_text" placeholder="Machines, Spares, Tools" />
        </UFormField>
        <UFormField label="Default currency">
          <UInput v-model="connectionForm.default_currency" maxlength="3" placeholder="KES" />
        </UFormField>
        <UFormField label="Poll interval minutes">
          <UInput v-model.number="connectionForm.poll_interval_minutes" type="number" min="1" />
        </UFormField>
        <UFormField label="Partner name">
          <UInput v-model="connectionForm.partner_name" placeholder="Default Partner" />
        </UFormField>
        <UFormField label="Product class">
          <UInput v-model="connectionForm.product_class" placeholder="Industrial Product" />
        </UFormField>
        <UFormField label="Customer group">
          <UInput v-model="connectionForm.customer_group" placeholder="Ecommerce" />
        </UFormField>
        <UFormField label="Territory">
          <UInput v-model="connectionForm.territory" placeholder="Kenya" />
        </UFormField>
        <UFormField label="Pesapal clearing account">
          <UInput v-model="connectionForm.pesapal_bank_account" placeholder="Pesapal Clearing - VI" />
        </UFormField>
        <UFormField label="Delivery days">
          <UInput v-model.number="connectionForm.delivery_days" type="number" min="1" />
        </UFormField>
        <div class="flex items-end">
          <UCheckbox v-model="connectionForm.is_active" label="Enable scheduled sync" />
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 border-t border-slate-200 px-5 py-4 sm:grid-cols-2 xl:grid-cols-3">
        <UCheckbox v-model="connectionForm.use_vortexus_bridge_app" label="Use Reesolmart ERPNext app" />
        <UCheckbox v-model="connectionForm.sync_customers" label="Sync customers" />
        <UCheckbox v-model="connectionForm.export_orders" label="Export sales orders" />
        <UCheckbox v-model="connectionForm.export_order_accounting" label="Export invoices and payments" />
        <UCheckbox v-model="connectionForm.sync_cancellations" label="Sync cancellations" />
        <UCheckbox v-model="connectionForm.sync_refunds" label="Sync refund credit notes" />
      </div>

      <div class="flex flex-wrap justify-end gap-2 border-t border-slate-200 px-5 py-4">
        <UButton color="neutral" variant="ghost" @click="isEditorOpen = false">
          Cancel
        </UButton>
        <UButton color="primary" icon="i-lucide-save" :loading="isSavingConnection" @click="saveConnection">
          Save Integration
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_420px]">
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-200 px-5 py-4">
          <h2 class="text-lg font-black text-slate-950">
            Connections
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            {{ healthyConnections }} healthy connections
          </p>
        </div>

        <div v-if="isLoading" class="space-y-3 p-5">
          <USkeleton v-for="item in 4" :key="item" class="h-24 rounded-xl" />
        </div>

        <div v-else-if="!connections.length" class="px-6 py-16 text-center">
          <div class="mx-auto flex size-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <UIcon name="i-lucide-unplug" class="size-7" />
          </div>
          <h2 class="mt-5 text-xl font-black text-slate-950">
            No integrations configured
          </h2>
          <p class="mx-auto mt-2 max-w-md text-sm text-slate-600">
            The backend supports integration connections, but none are currently configured.
          </p>
        </div>

        <div v-else class="divide-y divide-slate-200">
          <div
            v-for="connection in connections"
            :key="connection.id"
            class="flex flex-col gap-4 px-5 py-5 lg:flex-row lg:items-center lg:justify-between"
          >
            <button class="min-w-0 text-left" @click="loadLogs(connection)">
              <div class="flex items-center gap-3">
                <div class="flex size-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                  <UIcon name="i-lucide-plug" class="size-5" />
                </div>
                <div class="min-w-0">
                  <p class="truncate text-base font-black text-slate-950">
                    {{ connection.name }}
                  </p>
                  <p class="truncate text-sm text-slate-500">
                    {{ connection.base_url }}
                  </p>
                </div>
              </div>
            </button>

            <div class="flex flex-wrap items-center gap-2">
              <UBadge :color="statusColor(connection.status)" variant="soft" class="capitalize">
                {{ connection.status }}
              </UBadge>
              <UBadge color="neutral" variant="soft" class="uppercase">
                {{ connection.connection_type }}
              </UBadge>
              <UButton
                size="sm"
                variant="ghost"
                icon="i-lucide-pencil"
                @click="openEditConnection(connection)"
              />
              <UButton
                size="sm"
                variant="outline"
                :loading="actionId === connection.id"
                @click="runTest(connection)"
              >
                Test
              </UButton>
              <UButton
                v-if="connection.connection_type === 'erpnext'"
                size="sm"
                variant="outline"
                :loading="previewActionId === connection.id"
                @click="runPreview(connection)"
              >
                Preview
              </UButton>
              <UButton
                v-if="connection.connection_type === 'erpnext'"
                size="sm"
                color="primary"
                variant="outline"
                :loading="importActionId === connection.id"
                @click="runCatalogImport(connection)"
              >
                Import
              </UButton>
              <UButton
                v-if="connection.connection_type === 'erpnext'"
                size="sm"
                color="primary"
                variant="soft"
                :loading="actionId === connection.id"
                @click="runStockSync(connection)"
              >
                Sync stock
              </UButton>
            </div>
          </div>
        </div>
      </div>

      <aside class="space-y-6">
        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-200 px-5 py-4">
            <h2 class="text-lg font-black text-slate-950">
              ERPNext tools
            </h2>
            <p class="mt-1 text-sm text-slate-500">
              Preview remote data and choose whether imports also refresh stock.
            </p>
          </div>

          <div class="space-y-4 p-5">
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <UFormField label="Preview resource">
                <USelect v-model="previewResource" :items="previewResourceOptions" class="w-full" />
              </UFormField>
              <UFormField label="Preview limit">
                <USelect v-model="previewLimit" :items="previewLimitOptions" class="w-full" />
              </UFormField>
            </div>

            <UCheckbox v-model="importIncludeStock" label="Include stock during catalog import" />

            <div v-if="previewResult" class="rounded-xl border border-slate-200">
              <div class="border-b border-slate-200 px-4 py-3">
                <p class="font-black text-slate-950">
                  {{ previewConnection?.name || 'ERPNext' }} preview
                </p>
                <p class="mt-1 text-xs uppercase tracking-wide text-slate-500">
                  {{ previewResult.count }} {{ previewResult.resource }} records
                </p>
              </div>

              <div v-if="previewColumns.length" class="max-h-80 overflow-auto">
                <table class="min-w-full divide-y divide-slate-200 text-sm">
                  <thead class="bg-slate-50">
                    <tr>
                      <th v-for="column in previewColumns" :key="column" class="px-3 py-2 text-left text-xs font-black uppercase text-slate-500">
                        {{ column }}
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    <tr v-for="(record, index) in previewResult.records" :key="index">
                      <td v-for="column in previewColumns" :key="column" class="max-w-44 truncate px-3 py-2 text-slate-700">
                        {{ formatValue(record[column]) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-else class="px-4 py-6 text-center text-sm text-slate-500">
                ERPNext returned no records for this preview.
              </div>
            </div>

            <div v-if="importSummary" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
              <p class="font-black text-emerald-950">
                Latest import summary
              </p>
              <dl class="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div v-for="(value, key) in importSummary" :key="key">
                  <dt class="text-xs uppercase tracking-wide text-emerald-700">
                    {{ key }}
                  </dt>
                  <dd class="mt-1 font-semibold text-emerald-950">
                    {{ formatValue(value) }}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-200 px-5 py-4">
            <h2 class="text-lg font-black text-slate-950">
              Recent logs
            </h2>
            <p class="mt-1 truncate text-sm text-slate-500">
              {{ selectedConnection?.name || 'Select a connection' }}
            </p>
          </div>

          <div v-if="!selectedConnection" class="px-5 py-12 text-center text-sm text-slate-500">
            Select a connection to view recent logs.
          </div>

          <div v-else-if="!logs.length" class="px-5 py-12 text-center text-sm text-slate-500">
            No logs recorded for this connection yet.
          </div>

          <div v-else class="max-h-[520px] divide-y divide-slate-200 overflow-y-auto">
            <div v-for="log in logs" :key="log.id" class="px-5 py-4">
              <div class="flex items-center justify-between gap-3">
                <p class="font-semibold text-slate-950">
                  {{ log.entity_type }}
                </p>
                <UBadge :color="statusColor(log.status)" variant="soft" class="capitalize">
                  {{ log.status }}
                </UBadge>
              </div>
              <p class="mt-1 text-xs text-slate-500">
                {{ formatDate(log.created_at) }}
              </p>
              <p v-if="log.error_message" class="mt-2 text-sm text-red-600">
                {{ log.error_message }}
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
