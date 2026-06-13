<script setup lang="ts">
import type { SupplierProductReviewItem } from '~/composables/useSupplierProductReviews'

const toast = useToast()
const { getReviews, updateReview } = useSupplierProductReviews()

const reviews = ref<SupplierProductReviewItem[]>([])
const selectedReview = ref<SupplierProductReviewItem | null>(null)
const statusFilter = ref('pending_review')
const searchQuery = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const decisionOpen = ref(false)
const decisionStatus = ref('')
const reviewNote = ref('')
const saveError = ref('')
const pagination = ref({ page: 1, page_size: 24, total: 0, num_pages: 1, has_next: false })

const statusOptions = [
  { label: 'All statuses', value: '' },
  { label: 'Pending review', value: 'pending_review' },
  { label: 'Changes requested', value: 'changes_requested' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Suspended', value: 'suspended' },
]

const moderationActions = [
  { label: 'Approve', value: 'approved', color: 'success', icon: 'i-lucide-circle-check' },
  { label: 'Request changes', value: 'changes_requested', color: 'warning', icon: 'i-lucide-message-square-warning' },
  { label: 'Reject', value: 'rejected', color: 'error', icon: 'i-lucide-circle-x' },
  { label: 'Suspend', value: 'suspended', color: 'error', icon: 'i-lucide-ban' },
]

const filteredReviews = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  return reviews.value.filter((review) => {
    return !search
      || review.product?.title?.toLowerCase().includes(search)
      || review.product?.upc?.toLowerCase().includes(search)
      || review.product?.sku?.toLowerCase().includes(search)
      || review.supplier?.company_name?.toLowerCase().includes(search)
      || review.supplier?.partner?.code?.toLowerCase().includes(search)
      || String(review.id).includes(search)
  })
})

const pendingCount = computed(() => reviews.value.filter(review => review.status === 'pending_review').length)
const approvedCount = computed(() => reviews.value.filter(review => review.status === 'approved').length)
const blockedCount = computed(() => reviews.value.filter(review => ['rejected', 'suspended', 'changes_requested'].includes(review.status)).length)

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

function money(product: SupplierProductReviewItem['product']) {
  if (product?.price === null || product?.price === undefined || product?.price === '')
    return 'No price'
  return `${product.currency || 'KES'} ${Number(product.price).toLocaleString()}`
}

async function loadReviews(page = 1) {
  isLoading.value = true
  const result = await getReviews({ status: statusFilter.value, page, pageSize: pagination.value.page_size })

  if (result.success && result.data) {
    reviews.value = result.data.results || []
    pagination.value = result.data.pagination || pagination.value
    if (selectedReview.value) {
      selectedReview.value = reviews.value.find(review => review.id === selectedReview.value?.id) || null
    }
  }
  else {
    reviews.value = []
    toast.add({ title: 'Could not load supplier product reviews', description: result.error || 'Please try again.', color: 'error' })
  }

  isLoading.value = false
}

function openDecision(review: SupplierProductReviewItem, status: string) {
  selectedReview.value = review
  decisionStatus.value = status
  reviewNote.value = ''
  saveError.value = ''
  decisionOpen.value = true
}

async function submitDecision() {
  if (!selectedReview.value || !decisionStatus.value)
    return

  saveError.value = ''
  const needsNote = ['rejected', 'changes_requested', 'suspended'].includes(decisionStatus.value)
  if (needsNote && !reviewNote.value.trim()) {
    saveError.value = 'A review note is required for this decision.'
    return
  }

  isSaving.value = true
  const result = await updateReview(selectedReview.value.id, {
    status: decisionStatus.value,
    review_note: reviewNote.value.trim(),
  })

  if (result.success && result.data) {
    toast.add({
      title: 'Review updated',
      description: `${result.data.product.title} is now ${formatStatus(result.data.status)}.`,
      color: 'success',
    })
    selectedReview.value = result.data
    decisionOpen.value = false
    await loadReviews(pagination.value.page)
  }
  else {
    saveError.value = result.error || 'Could not update review.'
    toast.add({ title: 'Decision failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

watch(statusFilter, () => loadReviews(1))

onMounted(() => loadReviews())
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Supplier Product Reviews</h1>
        <p class="mt-1 text-sm text-slate-500">Approve, reject, or request changes before supplier products reach the storefront.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search product, supplier, SKU..."
        />
        <USelect v-model="statusFilter" :items="statusOptions" class="w-52" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadReviews(pagination.page)">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <CardsKpiCard2 name="Loaded reviews" :value="reviews.length" :budget="pagination.total || reviews.length" color="#3d7cff" icon="i-lucide-list-checks" :loading="isLoading" />
      <CardsKpiCard2 name="Pending" :value="pendingCount" :budget="reviews.length" color="#f59e0b" icon="i-lucide-clock" :loading="isLoading" />
      <CardsKpiCard2 name="Blocked" :value="blockedCount" :budget="reviews.length" color="#dc2626" icon="i-lucide-ban" :loading="isLoading" />
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <div class="overflow-hidden rounded-lg border border-slate-200 bg-white xl:col-span-3">
        <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
          <div class="col-span-5">Product</div>
          <div class="col-span-3">Supplier</div>
          <div class="col-span-2">Status</div>
          <div class="col-span-2 text-right">Actions</div>
        </div>

        <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
          <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
          Loading reviews
        </div>

        <div v-else-if="filteredReviews.length === 0" class="p-12 text-center">
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
            <UIcon name="i-lucide-package-search" />
          </div>
          <h2 class="mt-4 text-lg font-black text-slate-950">No product reviews found</h2>
          <p class="mt-1 text-sm text-slate-500">Try another status filter or search term.</p>
        </div>

        <div
          v-for="review in filteredReviews"
          v-else
          :key="review.id"
          class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
          :class="{ 'bg-blue-50/60': selectedReview?.id === review.id }"
        >
          <div class="col-span-5 min-w-0">
            <div class="flex min-w-0 items-center gap-3">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100 text-slate-500">
                <img v-if="review.product?.image || review.product?.thumbnail" :src="review.product.image || review.product.thumbnail" alt="" class="h-full w-full object-cover">
                <UIcon v-else name="i-lucide-box" />
              </div>
              <div class="min-w-0">
                <p class="truncate font-semibold text-slate-950">{{ review.product?.title || 'Untitled product' }}</p>
                <p class="truncate text-xs text-slate-500">{{ review.product?.upc || review.product?.sku || 'No SKU' }} · {{ money(review.product) }}</p>
              </div>
            </div>
          </div>
          <div class="col-span-3 min-w-0">
            <p class="truncate text-sm font-semibold text-slate-700">{{ review.supplier?.company_name || 'Unknown supplier' }}</p>
            <p class="truncate text-xs text-slate-500">{{ review.supplier?.partner?.code || 'No partner code' }}</p>
          </div>
          <div class="col-span-2">
            <UBadge :color="statusColor(review.status)" variant="soft">{{ formatStatus(review.status) }}</UBadge>
          </div>
          <div class="col-span-2 flex justify-end gap-1">
            <UTooltip text="View details">
              <UButton icon="i-lucide-panel-right-open" color="neutral" variant="ghost" square @click="selectedReview = review" />
            </UTooltip>
            <UTooltip v-if="review.status !== 'approved'" text="Approve">
              <UButton icon="i-lucide-circle-check" color="success" variant="ghost" square :loading="isSaving" @click="openDecision(review, 'approved')" />
            </UTooltip>
            <UTooltip text="Request changes">
              <UButton icon="i-lucide-message-square-warning" color="warning" variant="ghost" square :loading="isSaving" @click="openDecision(review, 'changes_requested')" />
            </UTooltip>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white xl:col-span-2">
        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="font-black text-slate-950">Review Detail</h2>
          <p class="mt-1 text-sm text-slate-500">{{ selectedReview ? selectedReview.product?.title : 'Select a product to inspect moderation details.' }}</p>
        </div>

        <div v-if="!selectedReview" class="p-8 text-center text-sm text-slate-500">
          Choose a supplier product from the queue.
        </div>

        <div v-else class="p-4">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-lg font-black text-slate-950">{{ selectedReview.product?.title }}</p>
              <p class="truncate text-sm text-slate-500">Review #{{ selectedReview.id }}</p>
            </div>
            <UBadge :color="statusColor(selectedReview.status)" variant="soft">{{ formatStatus(selectedReview.status) }}</UBadge>
          </div>

          <dl class="space-y-3 text-sm">
            <div>
              <dt class="font-semibold text-slate-500">Supplier</dt>
              <dd class="mt-1 text-slate-950">{{ selectedReview.supplier?.company_name }}</dd>
              <dd class="text-xs text-slate-500">{{ selectedReview.supplier?.user?.email }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Partner</dt>
              <dd class="mt-1 text-slate-950">{{ selectedReview.supplier?.partner?.name }}</dd>
              <dd class="text-xs text-slate-500">{{ selectedReview.supplier?.partner?.code }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Price</dt>
              <dd class="mt-1 text-slate-950">{{ money(selectedReview.product) }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Submitted</dt>
              <dd class="mt-1 text-slate-950">{{ formatDate(selectedReview.submitted_at) }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Reviewed</dt>
              <dd class="mt-1 text-slate-950">{{ formatDate(selectedReview.reviewed_at) }}</dd>
              <dd v-if="selectedReview.reviewed_by" class="text-xs text-slate-500">{{ selectedReview.reviewed_by.email }}</dd>
            </div>
            <div>
              <dt class="font-semibold text-slate-500">Review note</dt>
              <dd class="mt-1 whitespace-pre-wrap text-slate-950">{{ selectedReview.review_note || 'No review note recorded.' }}</dd>
            </div>
          </dl>

          <div class="mt-5 flex flex-wrap gap-2">
            <UButton
              v-for="action in moderationActions"
              :key="action.value"
              :color="action.color as any"
              variant="outline"
              :loading="isSaving"
              @click="openDecision(selectedReview, action.value)"
            >
              <UIcon :name="action.icon" />
              {{ action.label }}
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4 flex flex-col gap-3 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
      <p>Showing {{ filteredReviews.length }} of {{ pagination.total || reviews.length }} reviews.</p>
      <div class="flex gap-2">
        <UButton color="neutral" variant="outline" :disabled="pagination.page <= 1 || isLoading" @click="loadReviews(pagination.page - 1)">Previous</UButton>
        <UButton color="neutral" variant="outline" :disabled="!pagination.has_next || isLoading" @click="loadReviews(pagination.page + 1)">Next</UButton>
      </div>
    </div>

    <div v-if="decisionOpen && selectedReview" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-xl">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ formatStatus(decisionStatus) }}</h3>
              <p class="text-sm text-dimmed">{{ selectedReview.product?.title }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="decisionOpen = false" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

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
