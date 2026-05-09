<script setup lang="ts">
import type { ReviewItem, ReviewPayload } from '~/composables/useReviews'

const ALL_STATUSES = '__all_statuses__'
const ALL_RATINGS = '__all_ratings__'

const STATUS_MODERATION = 0
const STATUS_APPROVED = 1
const STATUS_REJECTED = 2

const toast = useToast()
const { deleteReview, getReviews, updateReview } = useReviews()

const reviews = ref<ReviewItem[]>([])
const totalItems = ref(0)
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')
const statusFilter = ref(ALL_STATUSES)
const ratingFilter = ref(ALL_RATINGS)
const dateFromFilter = ref('')
const dateToFilter = ref('')
const selectedReview = ref<ReviewItem | null>(null)
const editingReview = ref<ReviewItem | null>(null)
const pendingDeleteReview = ref<ReviewItem | null>(null)
const pendingStatus = ref<{ review: ReviewItem, status: number } | null>(null)
const saveError = ref('')

const form = reactive({
  title: '',
  body: '',
  score: 5,
  status: STATUS_MODERATION,
})

const statusOptions = [
  { label: 'All statuses', value: ALL_STATUSES },
  { label: 'Requires moderation', value: String(STATUS_MODERATION) },
  { label: 'Approved', value: String(STATUS_APPROVED) },
  { label: 'Rejected', value: String(STATUS_REJECTED) },
]

const reviewStatusOptions = statusOptions.filter(option => option.value !== ALL_STATUSES)

const ratingOptions = [
  { label: 'All ratings', value: ALL_RATINGS },
  { label: '5 stars', value: '5' },
  { label: '4 stars', value: '4' },
  { label: '3 stars', value: '3' },
  { label: '2 stars', value: '2' },
  { label: '1 star', value: '1' },
]

const filteredReviews = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  const fromTime = dateFromFilter.value ? new Date(`${dateFromFilter.value}T00:00:00`).getTime() : null
  const toTime = dateToFilter.value ? new Date(`${dateToFilter.value}T23:59:59`).getTime() : null

  return reviews.value.filter((review) => {
    const createdTime = review.date_created ? new Date(review.date_created).getTime() : 0
    const matchesSearch = !search
      || String(review.id).includes(search)
      || String(review.product_id || '').includes(search)
      || String(review.product_title || '').toLowerCase().includes(search)
      || String(review.title || '').toLowerCase().includes(search)
      || String(review.body || '').toLowerCase().includes(search)
      || String(review.name || '').toLowerCase().includes(search)
      || String(review.email || '').toLowerCase().includes(search)
    const matchesStatus = statusFilter.value === ALL_STATUSES || String(review.status) === statusFilter.value
    const matchesRating = ratingFilter.value === ALL_RATINGS || String(review.score) === ratingFilter.value
    const matchesFrom = !fromTime || createdTime >= fromTime
    const matchesTo = !toTime || createdTime <= toTime
    return matchesSearch && matchesStatus && matchesRating && matchesFrom && matchesTo
  })
})

const moderationCount = computed(() => reviews.value.filter(review => Number(review.status) === STATUS_MODERATION).length)
const approvedCount = computed(() => reviews.value.filter(review => Number(review.status) === STATUS_APPROVED).length)
const rejectedCount = computed(() => reviews.value.filter(review => Number(review.status) === STATUS_REJECTED).length)
const averageRating = computed(() => {
  if (!reviews.value.length)
    return 0
  const total = reviews.value.reduce((sum, review) => sum + Number(review.score || 0), 0)
  return Number((total / reviews.value.length).toFixed(1))
})

function statusLabel(status?: number | string) {
  const value = Number(status)
  if (value === STATUS_APPROVED)
    return 'Approved'
  if (value === STATUS_REJECTED)
    return 'Rejected'
  return 'Requires moderation'
}

function statusColor(status?: number | string) {
  const value = Number(status)
  if (value === STATUS_APPROVED)
    return 'success'
  if (value === STATUS_REJECTED)
    return 'error'
  return 'warning'
}

function formatDate(value?: string | null) {
  if (!value)
    return 'Not set'

  return new Intl.DateTimeFormat('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function ratingText(score?: number) {
  return `${Number(score || 0)} / 5`
}

function openEditReview(review: ReviewItem) {
  editingReview.value = review
  saveError.value = ''
  form.title = review.title || ''
  form.body = review.body || ''
  form.score = Number(review.score || 1)
  form.status = Number(review.status)
}

async function loadReviews() {
  isLoading.value = true
  const result = await getReviews({ pageSize: 200 })

  if (result.success) {
    reviews.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? reviews.value.length
  }
  else {
    reviews.value = []
    totalItems.value = 0
    toast.add({
      title: 'Could not load reviews',
      description: result.error || 'Please try again.',
      color: 'error',
    })
  }

  isLoading.value = false
}

async function submitReview() {
  if (!editingReview.value)
    return

  saveError.value = ''
  if (!form.title.trim() || !form.body.trim()) {
    saveError.value = 'Review title and body are required.'
    return
  }

  isSaving.value = true
  const payload: ReviewPayload = {
    title: form.title.trim(),
    body: form.body.trim(),
    score: Number(form.score || 1),
    status: Number(form.status),
  }
  const result = await updateReview(editingReview.value.id, payload)

  if (result.success) {
    toast.add({ title: 'Review updated', color: 'success' })
    editingReview.value = null
    await loadReviews()
  }
  else {
    saveError.value = result.error || 'Could not save review.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmStatusUpdate() {
  if (!pendingStatus.value)
    return

  isSaving.value = true
  const target = pendingStatus.value
  const result = await updateReview(target.review.id, { status: target.status })

  if (result.success) {
    toast.add({
      title: 'Review moderated',
      description: `Review #${target.review.id} was marked ${statusLabel(target.status).toLowerCase()}.`,
      color: 'success',
    })
    pendingStatus.value = null
    await loadReviews()
  }
  else {
    toast.add({ title: 'Moderation failed', description: result.error || 'Could not update review status.', color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeleteReview() {
  if (!pendingDeleteReview.value)
    return

  isSaving.value = true
  const review = pendingDeleteReview.value
  const result = await deleteReview(review.id)

  if (result.success) {
    toast.add({ title: 'Review deleted', description: `Review #${review.id} was removed.`, color: 'success' })
    pendingDeleteReview.value = null
    if (selectedReview.value?.id === review.id)
      selectedReview.value = null
    await loadReviews()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete review.', color: 'error' })
  }

  isSaving.value = false
}

onMounted(loadReviews)
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Review Moderation</h1>
        <p class="mt-1 text-sm text-slate-500">Moderate customer product reviews and keep storefront feedback clean.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput
          v-model="searchQuery"
          class="min-w-56 flex-1 lg:max-w-sm"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search reviews..."
        />
        <USelect v-model="statusFilter" :items="statusOptions" value-attribute="value" option-attribute="label" class="min-w-48" color="neutral" variant="outline" size="lg" />
        <USelect v-model="ratingFilter" :items="ratingOptions" value-attribute="value" option-attribute="label" class="min-w-36" color="neutral" variant="outline" size="lg" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadReviews">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2">
      <UInput v-model="dateFromFilter" type="date" color="neutral" variant="outline" size="lg" class="min-w-40" />
      <UInput v-model="dateToFilter" type="date" color="neutral" variant="outline" size="lg" class="min-w-40" />
      <UButton
        color="neutral"
        variant="ghost"
        :disabled="!dateFromFilter && !dateToFilter"
        @click="dateFromFilter = ''; dateToFilter = ''"
      >
        <UIcon name="i-lucide-x" />
        Clear Dates
      </UButton>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Needs moderation" :value="moderationCount" :budget="totalItems" color="#f59e0b" icon="i-lucide-message-square-warning" :loading="isLoading" />
      <CardsKpiCard2 name="Approved" :value="approvedCount" :budget="totalItems" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Rejected" :value="rejectedCount" :budget="totalItems" color="#dc2626" icon="i-lucide-circle-x" :loading="isLoading" />
      <CardsKpiCard2 name="Average rating" :value="averageRating" :budget="5" color="#3d7cff" icon="i-lucide-star" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Review</div>
        <div class="col-span-3">Product</div>
        <div class="col-span-1">Rating</div>
        <div class="col-span-2">Customer</div>
        <div class="col-span-1">Status</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <div v-if="isLoading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
        <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
        Loading reviews
      </div>

      <div v-else-if="filteredReviews.length === 0" class="p-12 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#255be8]">
          <UIcon name="i-lucide-message-square-text" />
        </div>
        <h2 class="mt-4 text-lg font-black text-slate-950">No reviews found</h2>
        <p class="mt-1 text-sm text-slate-500">Try another search, clear filters, or wait for customer feedback.</p>
      </div>

      <div
        v-for="review in filteredReviews"
        v-else
        :key="review.id"
        class="grid grid-cols-12 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 hover:bg-slate-50"
      >
        <div class="col-span-3 min-w-0">
          <p class="truncate font-semibold text-slate-950">{{ review.title || 'Untitled review' }}</p>
          <p class="truncate text-xs text-slate-500">#{{ review.id }} / {{ formatDate(review.date_created) }}</p>
        </div>
        <div class="col-span-3 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ review.product_title || 'Unknown product' }}</p>
          <p class="truncate text-xs text-slate-500">Product #{{ review.product_id || 'n/a' }}</p>
        </div>
        <div class="col-span-1">
          <UBadge color="warning" variant="soft">{{ ratingText(review.score) }}</UBadge>
        </div>
        <div class="col-span-2 min-w-0">
          <p class="truncate text-sm font-semibold text-slate-700">{{ review.name || 'Anonymous' }}</p>
          <p class="truncate text-xs text-slate-500">{{ review.email || 'No email' }}</p>
        </div>
        <div class="col-span-1">
          <UBadge :color="statusColor(review.status)" variant="soft">{{ statusLabel(review.status) }}</UBadge>
        </div>
        <div class="col-span-2 flex justify-end gap-1">
          <UTooltip text="View review">
            <UButton icon="i-lucide-eye" color="neutral" variant="ghost" square @click="selectedReview = review" />
          </UTooltip>
          <UTooltip text="Edit review">
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditReview(review)" />
          </UTooltip>
          <UTooltip text="Approve review">
            <UButton icon="i-lucide-check" color="success" variant="ghost" square :disabled="Number(review.status) === STATUS_APPROVED" @click="pendingStatus = { review, status: STATUS_APPROVED }" />
          </UTooltip>
          <UTooltip text="Reject review">
            <UButton icon="i-lucide-ban" color="warning" variant="ghost" square :disabled="Number(review.status) === STATUS_REJECTED" @click="pendingStatus = { review, status: STATUS_REJECTED }" />
          </UTooltip>
          <UTooltip text="Delete review">
            <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteReview = review" />
          </UTooltip>
        </div>
      </div>
    </div>

    <p class="mt-4 text-sm text-slate-500">Showing {{ filteredReviews.length }} of {{ totalItems }} reviews.</p>

    <div v-if="selectedReview" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[92vh] w-full max-w-2xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">{{ selectedReview.title || 'Untitled review' }}</h3>
              <p class="text-sm text-dimmed">{{ selectedReview.product_title || 'Unknown product' }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="selectedReview = null" />
          </div>
        </template>

        <div class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Rating</p><p class="mt-1 font-semibold">{{ ratingText(selectedReview.score) }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Status</p><p class="mt-1 font-semibold">{{ statusLabel(selectedReview.status) }}</p></div>
          <div class="rounded-lg border border-slate-200 bg-slate-50 p-4"><p class="text-xs font-bold uppercase text-slate-500">Created</p><p class="mt-1 font-semibold">{{ formatDate(selectedReview.date_created) }}</p></div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700">{{ selectedReview.body }}</div>

        <template #footer>
          <div class="flex flex-wrap justify-end gap-3">
            <UButton color="neutral" variant="outline" @click="selectedReview = null">Close</UButton>
            <UButton color="success" variant="solid" :disabled="Number(selectedReview.status) === STATUS_APPROVED" @click="pendingStatus = { review: selectedReview, status: STATUS_APPROVED }">Approve</UButton>
            <UButton color="warning" variant="solid" :disabled="Number(selectedReview.status) === STATUS_REJECTED" @click="pendingStatus = { review: selectedReview, status: STATUS_REJECTED }">Reject</UButton>
            <UButton color="primary" variant="solid" @click="openEditReview(selectedReview)">Edit</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="editingReview" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="max-h-[92vh] w-full max-w-2xl overflow-y-auto">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-semibold text-default">Edit review</h3>
              <p class="text-sm text-dimmed">Review #{{ editingReview.id }}</p>
            </div>
            <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="editingReview = null" />
          </div>
        </template>

        <div v-if="saveError" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">{{ saveError }}</div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField label="Title" required class="md:col-span-2"><UInput v-model="form.title" autocomplete="off" /></UFormField>
          <UFormField label="Score" required><UInput v-model.number="form.score" type="number" min="1" max="5" /></UFormField>
          <UFormField label="Status" required><USelect v-model="form.status" :items="reviewStatusOptions" value-attribute="value" option-attribute="label" /></UFormField>
          <UFormField label="Body" required class="md:col-span-2"><UTextarea v-model="form.body" :rows="6" /></UFormField>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="editingReview = null">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="submitReview">Save review</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingStatus" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Moderate review</h3></template>
        <p class="text-sm text-default">Mark review #{{ pendingStatus.review.id }} as <span class="font-semibold">{{ statusLabel(pendingStatus.status).toLowerCase() }}</span>?</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingStatus = null">Cancel</UButton>
            <UButton color="primary" variant="solid" :loading="isSaving" @click="confirmStatusUpdate">Update status</UButton>
          </div>
        </template>
      </UCard>
    </div>

    <div v-if="pendingDeleteReview" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <UCard class="w-full max-w-md">
        <template #header><h3 class="font-semibold text-default">Delete review</h3></template>
        <p class="text-sm text-default">Delete review #{{ pendingDeleteReview.id }}? This removes it from the storefront permanently.</p>
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isSaving" @click="pendingDeleteReview = null">Cancel</UButton>
            <UButton color="error" variant="solid" :loading="isSaving" @click="confirmDeleteReview">Delete review</UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
