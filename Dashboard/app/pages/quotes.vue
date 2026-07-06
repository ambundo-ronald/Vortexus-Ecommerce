<script setup lang="ts">
import type { QuoteRequestItem } from '~/composables/useQuoteRequests'

const toast = useToast()
const { getQuoteRequest, getQuoteRequests } = useQuoteRequests()

const quoteRequests = ref<QuoteRequestItem[]>([])
const selectedQuote = ref<QuoteRequestItem | null>(null)
const totalItems = ref(0)
const isLoading = ref(false)
const detailOpen = ref(false)
const searchQuery = ref('')

const filteredQuotes = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  if (!search)
    return quoteRequests.value

  return quoteRequests.value.filter((quote) => {
    return String(quote.id).includes(search)
      || quote.customer_name.toLowerCase().includes(search)
      || quote.customer_email.toLowerCase().includes(search)
      || quote.customer_phone.toLowerCase().includes(search)
      || quote.company.toLowerCase().includes(search)
      || quote.product_title.toLowerCase().includes(search)
      || quote.message_text.toLowerCase().includes(search)
  })
})

const customerCount = computed(() => new Set(quoteRequests.value.map(quote => quote.customer_email || quote.actor_email).filter(Boolean)).size)
const productCount = computed(() => new Set(quoteRequests.value.map(quote => quote.product_id).filter(Boolean)).size)
const phoneCount = computed(() => quoteRequests.value.filter(quote => quote.customer_phone).length)

function formatDate(value?: string | null) {
  if (!value)
    return 'Not recorded'
  return new Intl.DateTimeFormat('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadQuoteRequests() {
  isLoading.value = true
  const result = await getQuoteRequests({ pageSize: 200 })

  if (result.success) {
    quoteRequests.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? quoteRequests.value.length
  }
  else {
    quoteRequests.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load quotations',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function openDetail(quote: QuoteRequestItem) {
  selectedQuote.value = quote
  detailOpen.value = true
  const result = await getQuoteRequest(quote.id)
  if (result.success && result.data)
    selectedQuote.value = result.data
  else if (!result.success)
    toast.add({ title: 'Could not load quotation detail', description: result.error || 'Please try again.', color: 'error' })
}

onMounted(loadQuoteRequests)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Quotations</h1>
        <p class="mt-1 text-sm text-slate-500">Review logged-in customer quotation requests and contact details.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search quotations..."
        />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadQuoteRequests">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Quote requests" :value="totalItems" :budget="totalItems || 1" color="#3d7cff" icon="i-lucide-file-question" :loading="isLoading" />
      <CardsKpiCard2 name="Customers" :value="customerCount" :budget="quoteRequests.length || 1" color="#059669" icon="i-lucide-users" :loading="isLoading" />
      <CardsKpiCard2 name="Products" :value="productCount" :budget="quoteRequests.length || 1" color="#7c3aed" icon="i-lucide-package" :loading="isLoading" />
      <CardsKpiCard2 name="With phone" :value="phoneCount" :budget="quoteRequests.length || 1" color="#f59e0b" icon="i-lucide-phone" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Customer</div>
        <div class="col-span-3">Product</div>
        <div class="col-span-3">Message</div>
        <div class="col-span-2">Created</div>
        <div class="col-span-1 text-right">Action</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading quotations
      </div>

      <div v-else-if="filteredQuotes.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-file-question" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No quotation requests found</h2>
        <p class="mt-1 text-sm text-slate-500">New logged-in quote requests will appear here.</p>
      </div>

      <div
        v-for="quote in filteredQuotes"
        v-else
        :key="quote.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-3 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-950">{{ quote.customer_name }}</p>
          <p class="truncate text-xs text-slate-500">{{ quote.customer_email || quote.customer_phone || 'No contact recorded' }}</p>
        </div>
        <div class="col-span-3 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ quote.product_title }}</p>
          <p class="truncate text-xs text-slate-500">Product #{{ quote.product_id || 'general' }}</p>
        </div>
        <div class="col-span-3 min-w-0">
          <p class="truncate text-sm text-slate-700">{{ quote.message_text || 'No message' }}</p>
          <p class="truncate text-xs text-slate-500">{{ quote.company || 'No company/site' }}</p>
        </div>
        <div class="col-span-2 text-sm text-slate-700">{{ formatDate(quote.created_at) }}</div>
        <div class="col-span-1 text-right">
          <UTooltip text="Open quotation">
            <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="openDetail(quote)" />
          </UTooltip>
        </div>
      </div>
    </div>

    <div v-if="detailOpen && selectedQuote" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[90vh] w-full max-w-3xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-default">Quotation #{{ selectedQuote.id }}</h3>
              <p class="text-sm text-dimmed">{{ formatDate(selectedQuote.created_at) }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="detailOpen = false" />
          </div>
        </template>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Customer contact</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Name</dt><dd class="text-slate-950">{{ selectedQuote.customer_name }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Email</dt><dd class="break-all text-slate-950">{{ selectedQuote.customer_email || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Phone</dt><dd class="text-slate-950">{{ selectedQuote.customer_phone || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Company / site</dt><dd class="text-slate-950">{{ selectedQuote.company || 'Not recorded' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">User ID</dt><dd class="text-slate-950">{{ selectedQuote.metadata?.user_id || selectedQuote.actor_id || 'Not recorded' }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4">
            <h4 class="mb-3 font-black text-slate-950">Product</h4>
            <dl class="space-y-2 text-sm">
              <div><dt class="font-semibold text-slate-500">Product</dt><dd class="text-slate-950">{{ selectedQuote.product_title }}</dd></div>
              <div><dt class="font-semibold text-slate-500">Product ID</dt><dd class="text-slate-950">{{ selectedQuote.product_id || 'General request' }}</dd></div>
              <div><dt class="font-semibold text-slate-500">UPC</dt><dd class="text-slate-950">{{ selectedQuote.metadata?.product_upc || 'Not recorded' }}</dd></div>
            </dl>
          </div>

          <div class="rounded-lg border border-slate-200 p-4 md:col-span-2">
            <h4 class="mb-3 font-black text-slate-950">Request message</h4>
            <p class="whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ selectedQuote.message_text || 'No message provided.' }}</p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
