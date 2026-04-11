<script setup lang="ts">
import type { MediaAsset } from "~/composables/useMedia";

const { deleteMedia, getMedia, uploadMedia } = useMedia();
const toast = useToast();

const currentPage = ref(1);
const pageSize = ref(24);
const searchQuery = ref("");
const productIdFilter = ref("");
const isLoading = ref(false);
const isUploading = ref(false);
const isGridView = ref(true);
const mediaItems = ref<MediaAsset[]>([]);
const selectedItems = ref<MediaAsset[]>([]);
const totalItems = ref(0);
const summary = ref({ total: 0, matching: 0 });

const stagedFiles = ref<File[]>([]);
const uploadProductId = ref("");
const uploadAlt = ref("");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

async function loadMedia() {
  isLoading.value = true;
  const result = await getMedia({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    productId: productIdFilter.value,
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

function toggleFileSelection(file: MediaAsset) {
  const index = selectedItems.value.findIndex(item => item.id === file.id);
  if (index >= 0)
    selectedItems.value.splice(index, 1);
  else
    selectedItems.value.push(file);
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
}

function onDrop(event: DragEvent) {
  isDragging.value = false;
  addFilesToStage(event.dataTransfer?.files);
}

function removeStagedFile(index: number) {
  stagedFiles.value.splice(index, 1);
}

async function uploadFiles() {
  if (!uploadProductId.value) {
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
  for (const file of stagedFiles.value) {
    const result = await uploadMedia(file, uploadProductId.value, uploadAlt.value);
    if (!result.success) {
      toast.add({
        title: "Upload failed",
        description: result.error || `Could not upload ${file.name}.`,
        color: "error",
      });
      isUploading.value = false;
      return;
    }
  }

  toast.add({
    title: "Media uploaded",
    description: `${stagedFiles.value.length} image(s) uploaded successfully.`,
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
  const ids = selectedItems.value.map(item => item.id);
  for (const id of ids) {
    const result = await deleteMedia(id);
    if (!result.success) {
      toast.add({
        title: "Delete failed",
        description: result.error || "Could not delete selected media.",
        color: "error",
      });
      return;
    }
  }
  toast.add({
    title: "Media deleted",
    description: `${ids.length} item(s) removed.`,
    color: "success",
  });
  await loadMedia();
}

watch([currentPage, pageSize, searchQuery, productIdFilter], loadMedia, { immediate: true });
watch([searchQuery, productIdFilter, pageSize], () => {
  currentPage.value = 1;
});
</script>

<template>
  <div class="flex min-h-screen bg-default text-default">
    <aside class="flex w-64 flex-shrink-0 flex-col border-r border-default bg-default">
      <div class="flex h-16 items-center border-b border-default px-4">
        <h2 class="text-lg font-semibold text-toned">Media Library</h2>
      </div>
      <div class="space-y-4 p-4">
        <CardsKpiCard2
          name="Total Assets"
          :value="summary.total"
          :budget="summary.total"
          color="var(--color-info)"
          icon="i-lucide-images"
          :loading="isLoading"
        />
        <UInput
          v-model="productIdFilter"
          type="number"
          placeholder="Filter by product ID"
          icon="i-lucide-package"
        />
        <UButton
          color="neutral"
          variant="outline"
          block
          :loading="isLoading"
          @click="loadMedia"
        >
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </aside>

    <main class="flex flex-1 flex-col">
      <header class="flex h-16 items-center justify-between border-b border-default bg-default px-6">
        <UInput
          v-model="searchQuery"
          icon="i-lucide-search"
          placeholder="Search media or product..."
          class="w-full max-w-xs"
        />
        <div class="ml-4 flex items-center gap-2">
          <UButton
            v-if="selectedItems.length > 0"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            aria-label="Delete image(s)"
            @click="deleteSelectedImages"
          >
            Delete {{ selectedItems.length }}
          </UButton>
          <UButton
            :icon="isGridView ? 'i-lucide-layout-grid' : 'i-lucide-list'"
            color="neutral"
            variant="ghost"
            aria-label="Toggle view"
            @click="isGridView = !isGridView"
          />
        </div>
      </header>

      <section class="border-b border-default p-6">
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_220px_1fr_auto]">
          <div
            :class="[
              'cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-colors',
              isDragging ? 'border-primary bg-primary/5' : 'border-default hover:border-primary',
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
            <UIcon name="i-lucide-image-up" class="mx-auto mb-2 h-8 w-8 text-toned" />
            <p class="text-sm text-toned">Click to upload or drag images here</p>
            <p class="mt-1 text-xs text-muted">JPG, PNG, WEBP up to 10MB</p>
          </div>

          <UFormField label="Product ID" required>
            <UInput v-model="uploadProductId" type="number" placeholder="123" />
          </UFormField>

          <UFormField label="Alt text">
            <UInput v-model="uploadAlt" placeholder="Optional image description" />
          </UFormField>

          <div class="flex items-end">
            <UButton
              color="primary"
              :disabled="stagedFiles.length === 0"
              :loading="isUploading"
              @click="uploadFiles"
            >
              Upload {{ stagedFiles.length || "" }}
            </UButton>
          </div>
        </div>

        <div v-if="stagedFiles.length" class="mt-4 flex flex-wrap gap-2">
          <UBadge
            v-for="(file, index) in stagedFiles"
            :key="`${file.name}-${index}`"
            color="neutral"
            variant="soft"
          >
            {{ file.name }}
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              @click.stop="removeStagedFile(index)"
            />
          </UBadge>
        </div>
      </section>

      <div class="flex-1 overflow-y-auto p-6">
        <div
          v-if="mediaItems.length > 0"
          :class="isGridView
            ? 'grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5'
            : 'flex flex-col gap-2'"
        >
          <div
            v-for="file in mediaItems"
            :key="file.id"
            :class="[
              isGridView
                ? 'relative cursor-pointer overflow-hidden rounded-lg ring-2 ring-transparent transition hover:ring-primary/50'
                : 'flex cursor-pointer items-center gap-4 rounded-lg bg-default px-4 py-2 ring-2 ring-transparent transition hover:ring-primary/50',
              selectedItems.some(item => item.id === file.id) ? '!ring-primary' : '',
            ]"
            @click="toggleFileSelection(file)"
          >
            <div v-if="isGridView" class="relative">
              <img :src="file.url" :alt="file.alt || file.name" class="h-36 w-full bg-muted object-cover">
              <div
                v-if="selectedItems.some(item => item.id === file.id)"
                class="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white"
              >
                <UIcon name="i-lucide-check" class="h-4 w-4" />
              </div>
              <div class="bg-default/85 p-2 backdrop-blur-sm">
                <p class="truncate text-xs font-medium text-toned">{{ file.name }}</p>
                <p class="truncate text-xs text-muted">{{ file.productTitle }} #{{ file.productId }}</p>
              </div>
            </div>
            <template v-else>
              <img :src="file.url" :alt="file.alt || file.name" class="h-16 w-16 rounded-md bg-muted object-cover">
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-toned">{{ file.name }}</p>
                <p class="truncate text-xs text-muted">{{ file.productTitle }} #{{ file.productId }}</p>
              </div>
              <UIcon
                v-if="selectedItems.some(item => item.id === file.id)"
                name="i-lucide-check-circle"
                class="h-5 w-5 text-primary"
              />
            </template>
          </div>
        </div>

        <div v-else class="flex h-full flex-col items-center justify-center text-toned">
          <UIcon name="i-lucide-folder-open" class="mb-4 h-16 w-16" />
          <h3 class="text-lg font-semibold">No media found</h3>
          <p class="text-sm">Try a different search or upload product images.</p>
        </div>
      </div>

      <div class="flex justify-end border-t border-default p-4">
        <UPagination
          :page="currentPage"
          :page-count="pageSize"
          :total="totalItems"
          @update:page="(page: number) => currentPage = page"
        />
      </div>
    </main>
  </div>
</template>
