<script setup lang="ts">
import type { IntegrationConnection, IntegrationLog } from '~/composables/useIntegrations'

const toast = useToast()
const { getConnections, getLogs, testConnection, syncStock } = useIntegrations()

const connections = ref<IntegrationConnection[]>([])
const selectedConnection = ref<IntegrationConnection | null>(null)
const logs = ref<IntegrationLog[]>([])
const isLoading = ref(false)
const actionId = ref<number | null>(null)

const activeConnections = computed(() => connections.value.filter(connection => connection.is_active).length)
const healthyConnections = computed(() => connections.value.filter(connection => connection.status === 'active').length)
const errorConnections = computed(() => connections.value.filter(connection => connection.status === 'error').length)

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

      <UButton variant="outline" size="lg" :loading="isLoading" @click="loadConnections">
        <UIcon name="i-lucide-refresh-cw" />
        Refresh
      </UButton>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <CardsKpiCard2 name="Connections" :value="connections.length" :budget="connections.length" color="#3d7cff" />
      <CardsKpiCard2 name="Active" :value="activeConnections" :budget="connections.length" color="#16a34a" />
      <CardsKpiCard2 name="Needs attention" :value="errorConnections" :budget="connections.length" color="#ef4444" />
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
                variant="outline"
                :loading="actionId === connection.id"
                @click="runTest(connection)"
              >
                Test
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

      <aside class="rounded-2xl border border-slate-200 bg-white shadow-sm">
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
      </aside>
    </div>
  </div>
</template>
