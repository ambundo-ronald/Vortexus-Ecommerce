<script setup lang="ts">
import type { MediaAsset } from "~/composables/useMedia";

const { deleteMedia, getMedia, uploadMedia } = useMedia();
const toast = useToast();

const currentPage = ref(1);
const pageSize = ref(24);
const searchQuery = ref("");
const productIdFilter = ref("");
const uploadProductId = ref("");
const uploadAlt = ref("");
const mediaTypeFilter = ref<"all" | "product" | "marketing_block">("all");
const uploadMediaType = ref<"product" | "marketing_block">("product");

const isLoading = ref(false);
const isUploading = ref(false);
const isDragging = ref(false);
const isGridView = ref(true);
const fileInput = ref<HTMLInputElement | null>(null);

const mediaItems = ref<MediaAsset[]>([]);
const selectedItems = ref<MediaAsset[]>([]);
const stagedFiles = ref<File[]>([]);
const totalItems = ref(0);
const summary = ref({ total: 0, matching: 0 });
const previewItem = ref<MediaAsset | null>(null);
const isDeleteConfirmOpen = ref(false);
const isDeleting = ref(false);

const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)));
const hasSelection = computed(() => selectedItems.value.length > 0);
const stagedSize = computed(() =>
  stagedFiles.value.reduce((total, file) => total + file.size, 0),
);

function formatFileSize(bytes: number) {
  if (!bytes)
    return "0 KB";

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string) {
  if (!value)
    return "Not available";

  return new Date(value).toLocaleString("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

async function loadMedia() {
  isLoading.value = true;
  const result = await getMedia({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    productId: productIdFilter.value,
    mediaType: mediaTypeFilter.value === "all" ? undefined : mediaTypeFilter.value,
  });

  if (result.success) {
    mediaItems.value = result.data?.results ?? [];
    totalItems.value = result.data?.pagination?.total ?? 0;
    summary.value = result.data?.summary ?? summary.value;
    selectedItems.value = [];
  }
  else {
    mediaItems.value = [];
    totalItems.value = 0;
    toast.add({
      title: "Could not load media",
      description: result.error || "Please try again.",
      color: "error",
    });
  }
  isLoading.value = false;
}

function isSelected(file: MediaAsset) {
  return selectedItems.value.some(item => item.id === file.id);
}

function toggleFileSelection(file: MediaAsset) {
  const index = selectedItems.value.findIndex(item => item.id === file.id);
  if (index >= 0)
    selectedItems.value.splice(index, 1);
  else
    selectedItems.value.push(file);
}

function clearSelection() {
  selectedItems.value = [];
}

function addFilesToStage(files?: FileList | null) {
  if (!files)
    return;

  for (const file of Array.from(files)) {
    if (!file.type.startsWith("image/")) {
      toast.add({
        title: "Unsupported file",
        description: `${file.name} is not an image.`,
        color: "error",
      });
      continue;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.add({
        title: "File too large",
        description: `${file.name} exceeds 10MB.`,
        color: "error",
      });
      continue;
    }

    stagedFiles.value.push(file);
  }
}

function onFileSelect(event: Event) {
  addFilesToStage((event.target as HTMLInputElement).files);
  if (fileInput.value)
    fileInput.value.value = "";
}

function onDrop(event: DragEvent) {
  isDragging.value = false;
  addFilesToStage(event.dataTransfer?.files);
}

function removeStagedFile(index: number) {
  stagedFiles.value.splice(index, 1);
}

async function uploadFiles() {
  if (uploadMediaType.value === "product" && !uploadProductId.value) {
    toast.add({
      title: "Product required",
      description: "Enter the product ID this media belongs to.",
      color: "error",
    });
    return;
  }

  if (!stagedFiles.value.length)
    return;

  isUploading.value = true;
  let uploadedCount = 0;

  for (const file of stagedFiles.value) {
    const result = await uploadMedia(file, uploadProductId.value, uploadAlt.value, uploadMediaType.value);
    if (!result.success) {
      toast.add({
        title: "Upload failed",
        description: result.error || `Could not upload ${file.name}.`,
        color: "error",
      });
      isUploading.value = false;
      return;
    }
    uploadedCount += 1;
  }

  toast.add({
    title: "Media uploaded",
    description: `${uploadedCount} image(s) uploaded successfully.`,
    color: "success",
  });

  stagedFiles.value = [];
  uploadAlt.value = "";
  await loadMedia();
  isUploading.value = false;
}

async function deleteSelectedImages() {
  if (!selectedItems.value.length)
    return;

  isDeleting.value = true;
  const ids = selectedItems.value.map(item => item.id);

  for (const id of ids) {
    const result = await deleteMedia(id);
    if (!result.success) {
      toast.add({
        title: "Delete failed",
        description: result.error || "Could not delete selected media.",
        color: "error",
      });
      isDeleting.value = false;
      return;
    }
  }

  toast.add({
    title: "Media deleted",
    description: `${ids.length} item(s) removed.`,
    color: "success",
  });

  isDeleteConfirmOpen.value = false;
  isDeleting.value = false;
  await loadMedia();
}

watch([currentPage, pageSize, searchQuery, productIdFilter, mediaTypeFilter], loadMedia, { immediate: true });
watch([searchQuery, productIdFilter, mediaTypeFilter, pageSize], () => {
  currentPage.value = 1;
});
</script>

<template>
  <div class="px-4 py-8 sm:px-6 lg:px-10">
    <div class="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <h1 class="text-3xl font-black tracking-tight text-slate-950">
          Media
        </h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-600">
          Upload, preview, search, and remove product images used by the storefront.
        </p>
      </div>

      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <UInput
          v-model="searchQuery"
          class="w-full sm:w-72"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search image or product..."
        />
        <UInput
          v-model="productIdFilter"
          class="w-full sm:w-44"
          color="neutral"
          variant="outline"
          size="lg"
          type="number"
          icon="i-lucide-package"
          placeholder="Product ID"
        />
        <USelect
          v-model="mediaTypeFilter"
          class="w-full sm:w-48"
          color="neutral"
          variant="outline"
          size="lg"
          :items="[
            { label: 'All media', value: 'all' },
            { label: 'Product images', value: 'product' },
            { label: 'Marketing blocks', value: 'marketing_block' },
          ]"
          value-attribute="value"
          option-attribute="label"
        />
        <UButton variant="outline" size="lg" :loading="isLoading" @click="loadMedia">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <CardsKpiCard2 name="Total assets" :value="summary.total" :budget="summary.total" color="#3d7cff" icon="i-lucide-images" :loading="isLoading" />
      <CardsKpiCard2 name="Matching" :value="summary.matching" :budget="summary.total" color="#16a34a" icon="i-lucide-search-check" :loading="isLoading" />
      <CardsKpiCard2 name="Selected" :value="selectedItems.length" :budget="mediaItems.length" color="#f59e0b" icon="i-lucide-check-circle-2" :loading="isLoading" />
    </div>

    <section class="mb-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div class="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_190px_180px_1fr_auto]">
        <div
          :class="[
            'cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition-colors',
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-400 hover:bg-slate-50',
          ]"
          @click="fileInput?.click()"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="onFileSelect"
          >
          <div class="mx-auto flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <UIcon name="i-lucide-image-up" class="size-6" />
          </div>
          <p class="mt-3 text-sm font-semibold text-slate-950">
            Click to upload or drag images here
          </p>
          <p class="mt-1 text-xs text-slate-500">
            JPG, PNG, WEBP up to 10MB
          </p>
        </div>

        <UFormField label="Media category">
          <USelect
            v-model="uploadMediaType"
            color="neutral"
            variant="outline"
            size="lg"
            :items="[
              { label: 'Product image', value: 'product' },
              { label: 'Marketing block', value: 'marketing_block' },
            ]"
            value-attribute="value"
            option-attribute="label"
          />
        </UFormField>

        <UFormField label="Product ID" :required="uploadMediaType === 'product'">
          <UInput
            v-model="uploadProductId"
            color="neutral"
            variant="outline"
            size="lg"
            type="number"
            placeholder="123"
            :disabled="uploadMediaType !== 'product'"
          />
        </UFormField>

        <UFormField label="Alt text">
          <UInput v-model="uploadAlt" color="neutral" variant="outline" size="lg" placeholder="Optional image description" />
        </UFormField>

        <div class="flex items-end">
          <UButton
            color="primary"
            size="lg"
            :disabled="stagedFiles.length === 0"
            :loading="isUploading"
            @click="uploadFiles"
          >
            <UIcon name="i-lucide-upload" />
            Upload {{ stagedFiles.length || "" }}
          </UButton>
        </div>
      </div>

      <div v-if="stagedFiles.length" class="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <p class="text-sm font-semibold text-slate-950">
            {{ stagedFiles.length }} staged · {{ formatFileSize(stagedSize) }}
          </p>
          <UButton color="neutral" variant="ghost" size="sm" @click="stagedFiles = []">
            Clear
          </UButton>
        </div>
        <div class="flex flex-wrap gap-2">
          <UBadge
            v-for="(file, index) in stagedFiles"
            :key="`${file.name}-${index}`"
            color="neutral"
            variant="soft"
            class="gap-2"
          >
            {{ file.name }}
            <button type="button" class="text-slate-400 hover:text-slate-950" @click.stop="removeStagedFile(index)">
              <UIcon name="i-lucide-x" class="size-3" />
            </button>
          </UBadge>
        </div>
      </div>
    </section>

    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-lg font-black text-slate-950">
            Library
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Page {{ currentPage }} of {{ totalPages }} · {{ totalItems }} images
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <UButton
            v-if="hasSelection"
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            @click="clearSelection"
          >
            Clear selection
          </UButton>
          <UButton
            v-if="hasSelection"
            icon="i-lucide-trash-2"
            color="error"
            variant="soft"
            @click="isDeleteConfirmOpen = true"
          >
            Delete {{ selectedItems.length }}
          </UButton>
          <UButton
            :icon="isGridView ? 'i-lucide-list' : 'i-lucide-layout-grid'"
            color="neutral"
            variant="outline"
            aria-label="Toggle view"
            @click="isGridView = !isGridView"
          />
        </div>
      </div>

      <div v-if="isLoading" class="grid grid-cols-2 gap-4 p-5 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
        <USkeleton v-for="item in 12" :key="item" class="aspect-square rounded-xl" />
      </div>

      <div
        v-else-if="mediaItems.length > 0"
        :class="isGridView
          ? 'grid grid-cols-2 gap-4 p-5 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6'
          : 'divide-y divide-slate-200'"
      >
        <article
          v-for="file in mediaItems"
          :key="file.id"
          :class="[
            isGridView
              ? 'group overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:border-blue-300 hover:shadow-md'
              : 'flex items-center gap-4 px-5 py-4 transition hover:bg-slate-50',
            isSelected(file) ? 'ring-2 ring-blue-500' : '',
          ]"
        >
          <button
            type="button"
            :class="isGridView ? 'relative block aspect-square w-full overflow-hidden bg-slate-50' : 'relative h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-slate-50'"
            @click="previewItem = file"
          >
            <img :src="file.url" :alt="file.alt || file.name" class="h-full w-full object-cover">
            <div class="absolute inset-0 hidden items-center justify-center bg-slate-950/30 text-white group-hover:flex">
              <UIcon name="i-lucide-zoom-in" class="size-6" />
            </div>
          </button>

          <div :class="isGridView ? 'space-y-3 p-3' : 'min-w-0 flex-1'">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-bold text-slate-950">
                  {{ file.name }}
                </p>
                <p class="truncate text-xs text-slate-500">
                  {{ file.mediaType === 'marketing_block' ? 'Marketing block' : `${file.productTitle} · #${file.productId}` }}
                </p>
              </div>
              <button
                type="button"
                class="flex size-8 shrink-0 items-center justify-center rounded-full border border-slate-200 transition"
                :class="isSelected(file) ? 'bg-blue-600 text-white' : 'bg-white text-slate-500 hover:text-slate-950'"
                @click="toggleFileSelection(file)"
              >
                <UIcon :name="isSelected(file) ? 'i-lucide-check' : 'i-lucide-plus'" class="size-4" />
              </button>
            </div>
            <p v-if="isGridView" class="text-xs text-slate-400">
              {{ formatDate(file.createdAt) }}
            </p>
          </div>
        </article>
      </div>

      <div v-else class="px-6 py-20 text-center">
        <div class="mx-auto flex size-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <UIcon name="i-lucide-folder-open" class="size-8" />
        </div>
        <h3 class="mt-5 text-xl font-black text-slate-950">
          No media found
        </h3>
        <p class="mt-2 text-sm text-slate-500">
          Try another search, clear product filtering, or upload product images.
        </p>
      </div>

      <div class="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm text-slate-500">
          Showing {{ mediaItems.length }} of {{ totalItems }} images
        </p>
        <UPagination
          :page="currentPage"
          :page-count="pageSize"
          :total="totalItems"
          @update:page="(page: number) => currentPage = page"
        />
      </div>
    </section>

    <div
      v-if="previewItem"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4"
      @click.self="previewItem = null"
    >
      <div class="w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div class="min-w-0">
            <h2 class="truncate text-lg font-black text-slate-950">
              {{ previewItem.name }}
            </h2>
            <p class="truncate text-sm text-slate-500">
              {{ previewItem.mediaType === 'marketing_block' ? 'Marketing block media' : `${previewItem.productTitle} · Product #${previewItem.productId}` }}
            </p>
          </div>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" square @click="previewItem = null" />
        </div>
        <div class="max-h-[72vh] bg-slate-100 p-4">
          <img :src="previewItem.url" :alt="previewItem.alt || previewItem.name" class="mx-auto max-h-[68vh] rounded-xl object-contain">
        </div>
      </div>
    </div>

    <div
      v-if="isDeleteConfirmOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4"
    >
      <UCard class="w-full max-w-md border border-slate-200 bg-white">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="flex size-10 items-center justify-center rounded-2xl bg-red-50 text-red-600">
              <UIcon name="i-lucide-trash-2" class="size-5" />
            </div>
            <div>
              <h3 class="text-base font-black text-slate-950">
                Delete selected media
              </h3>
              <p class="text-sm text-slate-500">
                This removes selected product or marketing media.
              </p>
            </div>
          </div>
        </template>

        <p class="text-sm text-slate-600">
          Delete {{ selectedItems.length }} selected image(s)? This cannot be undone.
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton color="neutral" variant="outline" :disabled="isDeleting" @click="isDeleteConfirmOpen = false">
              Cancel
            </UButton>
            <UButton color="error" variant="solid" :loading="isDeleting" @click="deleteSelectedImages">
              Delete media
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
