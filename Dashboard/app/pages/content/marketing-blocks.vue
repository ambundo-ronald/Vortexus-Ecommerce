<script setup lang="ts">
import type { MediaAsset } from '~/composables/useMedia'
import type { MarketingBlock, MarketingBlockPayload } from '~/composables/useMarketingBlocks'

const toast = useToast()
const { createMarketingBlock, deleteMarketingBlock, getMarketingBlocks, updateMarketingBlock } = useMarketingBlocks()
const { getMedia } = useMedia()

const blocks = ref<MarketingBlock[]>([])
const placements = ref<Array<{ value: string, label: string }>>([])
const totalItems = ref(0)
const activeCount = ref(0)
const searchQuery = ref('')
const placementFilter = ref('__all')
const statusFilter = ref('__all')
const isLoading = ref(false)
const isSaving = ref(false)
const editorOpen = ref(false)
const editingBlock = ref<MarketingBlock | null>(null)
const pendingDeleteBlock = ref<MarketingBlock | null>(null)
const saveError = ref('')
const mediaPickerOpen = ref(false)
const mediaItems = ref<MediaAsset[]>([])
const isMediaLoading = ref(false)
const mediaSearch = ref('')

const form = reactive({
  title: '',
  slug: '',
  placement: 'home_hero',
  eyebrow: '',
  headline: '',
  body: '',
  image_url: '',
  image_alt: '',
  cta_text: '',
  cta_url: '',
  background_color: '',
  text_color: '',
  sort_order: 0,
  is_active: true,
  starts_at: '',
  ends_at: '',
})

const placementOptions = computed(() => placements.value.length
  ? placements.value
  : [
      { value: 'home_hero', label: 'Homepage hero' },
      { value: 'announcement', label: 'Announcement strip' },
      { value: 'promo_banner', label: 'Promo banner' },
      { value: 'featured', label: 'Featured block' },
      { value: 'brand_strip', label: 'Brand strip' },
      { value: 'top_category', label: 'Top Category' },
    ])

const inactiveCount = computed(() => Math.max(totalItems.value - activeCount.value, 0))
const currentCount = computed(() => blocks.value.filter(block => block.is_current).length)

function slugify(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function resetForm() {
  editingBlock.value = null
  saveError.value = ''
  form.title = ''
  form.slug = ''
  form.placement = placementOptions.value[0]?.value || 'home_hero'
  form.eyebrow = ''
  form.headline = ''
  form.body = ''
  form.image_url = ''
  form.image_alt = ''
  form.cta_text = ''
  form.cta_url = ''
  form.background_color = ''
  form.text_color = ''
  form.sort_order = 0
  form.is_active = true
  form.starts_at = ''
  form.ends_at = ''
}

function fillForm(block: MarketingBlock) {
  form.title = block.title || ''
  form.slug = block.slug || ''
  form.placement = block.placement || 'home_hero'
  form.eyebrow = block.eyebrow || ''
  form.headline = block.headline || ''
  form.body = block.body || ''
  form.image_url = block.image_url || ''
  form.image_alt = block.image_alt || ''
  form.cta_text = block.cta_text || ''
  form.cta_url = block.cta_url || ''
  form.background_color = block.background_color || ''
  form.text_color = block.text_color || ''
  form.sort_order = Number(block.sort_order || 0)
  form.is_active = !!block.is_active
  form.starts_at = block.starts_at ? block.starts_at.slice(0, 16) : ''
  form.ends_at = block.ends_at ? block.ends_at.slice(0, 16) : ''
}

function placementLabel(value: string) {
  return placementOptions.value.find(item => item.value === value)?.label || value
}

function openCreateBlock() {
  resetForm()
  editorOpen.value = true
}

function openEditBlock(block: MarketingBlock) {
  editingBlock.value = block
  fillForm(block)
  saveError.value = ''
  editorOpen.value = true
}

function toIsoOrNull(value: string) {
  return value ? new Date(value).toISOString() : null
}

async function loadBlocks() {
  isLoading.value = true
  const selectedPlacement = placementFilter.value === '__all' ? '' : placementFilter.value
  const selectedStatus = statusFilter.value === '__all' ? '' : statusFilter.value
  const result = await getMarketingBlocks({
    pageSize: 100,
    q: searchQuery.value.trim(),
    placement: selectedPlacement,
    status: selectedStatus,
  })

  if (result.success) {
    blocks.value = result.data?.results ?? []
    placements.value = result.data?.placements ?? placements.value
    totalItems.value = result.data?.pagination?.total ?? blocks.value.length
    activeCount.value = result.data?.summary?.active ?? blocks.value.filter(block => block.is_active).length
  }
  else {
    blocks.value = []
    totalItems.value = 0
    activeCount.value = 0
    toast.add({ title: 'Could not load marketing blocks', description: result.error || 'Please try again.', color: 'error' })
  }

  isLoading.value = false
}

async function openMediaPicker() {
  mediaPickerOpen.value = true
  await loadMediaItems()
}

async function loadMediaItems() {
  isMediaLoading.value = true
  const result = await getMedia({
    pageSize: 24,
    search: mediaSearch.value.trim(),
  })

  if (result.success) {
    mediaItems.value = result.data?.results ?? []
  }
  else {
    mediaItems.value = []
    toast.add({ title: 'Could not load media', description: result.error || 'Please try again.', color: 'error' })
  }

  isMediaLoading.value = false
}

function selectMedia(file: MediaAsset) {
  form.image_url = file.url
  form.image_alt = file.alt || file.name || form.image_alt
  mediaPickerOpen.value = false
}

async function submitBlock() {
  saveError.value = ''
  if (!form.title.trim()) {
    saveError.value = 'Title is required.'
    return
  }
  if (!form.placement) {
    saveError.value = 'Placement is required.'
    return
  }

  const payload: MarketingBlockPayload = {
    title: form.title.trim(),
    slug: form.slug.trim() || slugify(form.title),
    placement: form.placement,
    eyebrow: form.eyebrow.trim(),
    headline: form.headline.trim(),
    body: form.body.trim(),
    image_url: form.image_url.trim(),
    image_alt: form.image_alt.trim(),
    cta_text: form.cta_text.trim(),
    cta_url: form.cta_url.trim(),
    background_color: form.background_color.trim(),
    text_color: form.text_color.trim(),
    sort_order: Number(form.sort_order || 0),
    is_active: form.is_active,
    starts_at: toIsoOrNull(form.starts_at),
    ends_at: toIsoOrNull(form.ends_at),
    metadata: {},
  }

  isSaving.value = true
  const result = editingBlock.value
    ? await updateMarketingBlock(editingBlock.value.id, payload)
    : await createMarketingBlock(payload)

  if (result.success && result.data) {
    toast.add({ title: editingBlock.value ? 'Marketing block updated' : 'Marketing block created', description: `${result.data.title} was saved.`, color: 'success' })
    editorOpen.value = false
    resetForm()
    await loadBlocks()
  }
  else {
    saveError.value = result.error || 'Could not save marketing block.'
    toast.add({ title: 'Save failed', description: saveError.value, color: 'error' })
  }

  isSaving.value = false
}

async function confirmDeleteBlock() {
  if (!pendingDeleteBlock.value)
    return

  isSaving.value = true
  const block = pendingDeleteBlock.value
  const result = await deleteMarketingBlock(block.id)

  if (result.success) {
    toast.add({ title: 'Marketing block deleted', description: `${block.title} was removed.`, color: 'success' })
    pendingDeleteBlock.value = null
    await loadBlocks()
  }
  else {
    toast.add({ title: 'Delete failed', description: result.error || 'Could not delete marketing block.', color: 'error' })
  }

  isSaving.value = false
}

watch([searchQuery, placementFilter, statusFilter], loadBlocks, { immediate: true })
watch(mediaSearch, () => {
  if (mediaPickerOpen.value)
    void loadMediaItems()
})
</script>

<template>
  <div>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-950">Marketing Blocks</h1>
        <p class="mt-1 text-sm text-slate-500">Manage storefront heroes, banners, announcements, and featured promotional blocks.</p>
      </div>
      <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
        <UInput v-model="searchQuery" class="min-w-56 flex-1 lg:max-w-sm" color="neutral" variant="outline" size="lg" icon="i-lucide-search" placeholder="Search blocks..." />
        <USelect v-model="placementFilter" class="w-52" :items="[{ value: '__all', label: 'All placements' }, ...placementOptions]" value-key="value" label-key="label" />
        <USelect v-model="statusFilter" class="w-40" :items="[{ value: '__all', label: 'All' }, { value: 'active', label: 'Active' }, { value: 'inactive', label: 'Inactive' }]" value-key="value" label-key="label" />
        <UButton color="neutral" variant="outline" :loading="isLoading" @click="loadBlocks">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <UButton color="primary" variant="solid" @click="openCreateBlock">
          <UIcon name="i-lucide-plus" />
          New Block
        </UButton>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2 name="Total blocks" :value="totalItems" :budget="totalItems || 1" color="#3d7cff" icon="i-lucide-panels-top-left" :loading="isLoading" />
      <CardsKpiCard2 name="Active" :value="activeCount" :budget="totalItems || 1" color="#059669" icon="i-lucide-circle-check" :loading="isLoading" />
      <CardsKpiCard2 name="Current" :value="currentCount" :budget="blocks.length || 1" color="#7c3aed" icon="i-lucide-radio" :loading="isLoading" />
      <CardsKpiCard2 name="Inactive" :value="inactiveCount" :budget="totalItems || 1" color="#f59e0b" icon="i-lucide-circle-pause" :loading="isLoading" />
    </div>

    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div class="grid grid-cols-12 gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500">
        <div class="col-span-3">Block</div>
        <div class="col-span-2">Placement</div>
        <div class="col-span-3">Message</div>
        <div class="col-span-1 text-right">Order</div>
        <div class="col-span-1">Status</div>
        <div class="col-span-2 text-right">Actions</div>
      </div>

      <AdminTableState :loading="isLoading" :empty="blocks.length === 0" loading-label="Loading marketing blocks" empty-title="No marketing blocks found" empty-description="Create the first hero, promo banner, or announcement block.">
        <div v-for="block in blocks" :key="block.id" class="grid grid-cols-12 gap-3 border-b border-slate-100 px-4 py-4 text-sm last:border-b-0">
          <div class="col-span-3 min-w-0">
            <p class="truncate font-bold text-slate-950">{{ block.title }}</p>
            <p class="truncate text-xs text-slate-500">{{ block.slug }}</p>
          </div>
          <div class="col-span-2">
            <UBadge color="neutral" variant="soft">{{ placementLabel(block.placement) }}</UBadge>
          </div>
          <div class="col-span-3 min-w-0">
            <p class="truncate font-semibold text-slate-800">{{ block.headline || block.eyebrow || 'No headline' }}</p>
            <p class="truncate text-xs text-slate-500">{{ block.cta_text || block.cta_url || block.image_url || 'No CTA or image' }}</p>
          </div>
          <div class="col-span-1 text-right font-semibold text-slate-700">{{ block.sort_order }}</div>
          <div class="col-span-1">
            <UBadge :color="block.is_current ? 'success' : block.is_active ? 'warning' : 'neutral'" variant="soft">
              {{ block.is_current ? 'Current' : block.is_active ? 'Scheduled' : 'Off' }}
            </UBadge>
          </div>
          <div class="col-span-2 flex justify-end gap-2">
            <UTooltip text="Edit">
              <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" square @click="openEditBlock(block)" />
            </UTooltip>
            <UTooltip text="Delete">
              <UButton icon="i-lucide-trash-2" color="error" variant="ghost" square @click="pendingDeleteBlock = block" />
            </UTooltip>
          </div>
        </div>
      </AdminTableState>

      <AdminTableFooter :shown="blocks.length" :total="totalItems" label="marketing blocks" />
    </div>

    <AdminFormModal
      v-if="editorOpen"
      :title="editingBlock ? 'Edit Marketing Block' : 'New Marketing Block'"
      :description="editingBlock ? 'Update copy, media, scheduling, and placement.' : 'Create a storefront marketing block.'"
      :saving="isSaving"
      :error="saveError"
      save-label="Save Block"
      max-width="max-w-3xl"
      @submit="submitBlock"
      @close="editorOpen = false"
    >
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <UFormField label="Title" required>
          <UInput v-model="form.title" placeholder="Industrial pumps hero" @blur="!form.slug && (form.slug = slugify(form.title))" />
        </UFormField>
        <UFormField label="Slug" required>
          <UInput v-model="form.slug" placeholder="industrial-pumps-hero" />
        </UFormField>
        <UFormField label="Placement" required>
          <USelect v-model="form.placement" :items="placementOptions" value-key="value" label-key="label" />
        </UFormField>
        <UFormField label="Sort order">
          <UInput v-model.number="form.sort_order" type="number" min="0" />
        </UFormField>
        <UFormField label="Eyebrow">
          <UInput v-model="form.eyebrow" placeholder="New arrivals" />
        </UFormField>
        <UFormField label="Headline">
          <UInput v-model="form.headline" placeholder="Power your next project" />
        </UFormField>
        <UFormField class="md:col-span-2" label="Body">
          <UTextarea v-model="form.body" :rows="4" placeholder="Short promo copy shown on the storefront." />
        </UFormField>
        <UFormField label="Image URL">
          <div class="flex gap-2">
            <UInput v-model="form.image_url" class="min-w-0 flex-1" placeholder="/media/cache/..." />
            <UButton color="neutral" variant="outline" icon="i-lucide-image" @click="openMediaPicker">
              Choose
            </UButton>
          </div>
        </UFormField>
        <UFormField label="Image alt">
          <UInput v-model="form.image_alt" placeholder="Worker inspecting industrial pump" />
        </UFormField>
        <UFormField label="CTA text">
          <UInput v-model="form.cta_text" placeholder="Shop now" />
        </UFormField>
        <UFormField label="CTA URL">
          <UInput v-model="form.cta_url" placeholder="/catalog/products/?category=pumps" />
        </UFormField>
        <UFormField label="Background color">
          <UInput v-model="form.background_color" placeholder="#0f172a" />
        </UFormField>
        <UFormField label="Text color">
          <UInput v-model="form.text_color" placeholder="#ffffff" />
        </UFormField>
        <UFormField label="Starts at">
          <UInput v-model="form.starts_at" type="datetime-local" />
        </UFormField>
        <UFormField label="Ends at">
          <UInput v-model="form.ends_at" type="datetime-local" />
        </UFormField>
        <div class="md:col-span-2">
          <UCheckbox v-model="form.is_active" label="Active" />
        </div>
      </div>
    </AdminFormModal>

    <UModal v-model:open="mediaPickerOpen" title="Choose Media">
      <template #body>
        <div class="space-y-4">
          <div class="flex gap-2">
            <UInput v-model="mediaSearch" class="min-w-0 flex-1" icon="i-lucide-search" placeholder="Search media..." />
            <UButton color="neutral" variant="outline" :loading="isMediaLoading" icon="i-lucide-refresh-cw" @click="loadMediaItems" />
          </div>
          <AdminTableState :loading="isMediaLoading" :empty="mediaItems.length === 0" loading-label="Loading media" empty-title="No media found" empty-description="Upload media from the Media page, then select it here.">
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <button
                v-for="file in mediaItems"
                :key="file.id"
                class="overflow-hidden rounded-lg border border-slate-200 bg-white text-left transition hover:border-primary-400 hover:ring-2 hover:ring-primary-100"
                type="button"
                @click="selectMedia(file)"
              >
                <img :src="file.url" :alt="file.alt || file.name" class="aspect-video w-full object-cover">
                <div class="p-2">
                  <p class="truncate text-xs font-bold text-slate-900">{{ file.name }}</p>
                  <p class="truncate text-xs text-slate-500">{{ file.productTitle || 'Media library' }}</p>
                </div>
              </button>
            </div>
          </AdminTableState>
        </div>
      </template>
    </UModal>

    <AdminConfirmDialog
      v-if="pendingDeleteBlock"
      title="Delete marketing block"
      :description="`Delete ${pendingDeleteBlock.title}? This cannot be undone.`"
      confirm-label="Delete Block"
      icon="i-lucide-trash-2"
      :loading="isSaving"
      @confirm="confirmDeleteBlock"
      @cancel="pendingDeleteBlock = null"
    />
  </div>
</template>
