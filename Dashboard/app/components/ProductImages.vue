<template>
  <div class="mt-4">
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="(img, idx) in model"
        :key="`${img.src}-${idx}`"
        class="group relative flex aspect-square overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
      >
        <img
          class="h-full w-full object-cover"
          :alt="img.alt"
          :src="img.src"
        >
        <div
          class="absolute inset-0 hidden items-center justify-center gap-2 bg-slate-950/70 text-xl group-hover:flex"
        >
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full bg-white text-slate-950 shadow-sm"
            aria-label="Preview image"
            @click="previewImage(img.src)"
          >
            <UIcon
            name="i-lucide-eye"
            />
          </button>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full bg-white text-red-600 shadow-sm"
            aria-label="Remove image"
            @click="removeImage(idx)"
          >
            <UIcon name="i-lucide-trash" />
          </button>
        </div>
      </div>
      <div
        class="upload upload-draggable relative aspect-square cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 transition hover:border-[#30328f] hover:bg-blue-50"
        :class="{ 'border-[#30328f] bg-blue-50': isDragging }"
        @dragenter.prevent="isDragging = true"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onFilesDropped"
      >
        <input
          class="upload-input draggable absolute inset-0 cursor-pointer opacity-0"
          type="file"
          multiple
          accept="image/*"
          @change="onFilesSelected"
        >
        <div
          class="flex h-full max-w-full flex-col items-center justify-center px-4 py-2"
        >
          <div class="text-4xl text-slate-400">
            <UIcon size="20" name="i-lucide-upload" />
          </div>
          <p class="mt-2 text-center text-xs text-slate-500">
            Drop image here, or
            <span class="font-semibold text-[#30328f]">browse</span>
          </p>
        </div>
      </div>
    </div>
  </div>
  <p class="mt-4 text-xs text-slate-500">
    Image formats: .jpg, .jpeg, .png, .webp. Upload up to 5 images per
    product, with a maximum size of 5MB each.
  </p>

  <div
    v-if="isPreviewOpen"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/80 p-4"
    @click.self="isPreviewOpen = false"
  >
    <div class="relative max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-2xl bg-white p-3 shadow-2xl">
      <button
        type="button"
        class="absolute right-5 top-5 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-950 shadow"
        aria-label="Close preview"
        @click="isPreviewOpen = false"
      >
        <UIcon name="i-lucide-x" />
      </button>
      <img :src="previewSrc" alt="Product image preview" class="max-h-[82vh] w-full rounded-xl object-contain">
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ProductImageItem } from '~/types/ProductImage'

const model = defineModel<ProductImageItem[]>({ default: [] })
const toast = useToast()

const isPreviewOpen = ref(false)
const previewSrc = ref('')
const isDragging = ref(false)

function removeImage(idx: number) {
  const nextImages = [...model.value]
  const [image] = nextImages.splice(idx, 1)
  if (image?.file && image.src.startsWith('blob:'))
    URL.revokeObjectURL(image.src)
  model.value = nextImages
}

function previewImage(src: string) {
  previewSrc.value = src
  isPreviewOpen.value = true
}

function addFiles(files: FileList | File[]) {
  if (!files)
    return

  const nextImages = [...model.value]

  for (const file of Array.from(files)) {
    if (!file.type.startsWith('image/'))
      continue

    if (nextImages.length >= 5) {
      toast.add({
        title: 'Image limit reached',
        description: 'You can upload up to 5 product images per item.',
        color: 'warning',
      })
      break
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.add({
        title: 'Image too large',
        description: `${file.name} exceeds the 5MB upload limit.`,
        color: 'error',
      })
      continue
    }

    nextImages.push({
      src: URL.createObjectURL(file),
      alt: file.name,
      file,
    })
  }

  model.value = nextImages
}

function onFilesSelected(e: Event) {
  addFiles((e.target as HTMLInputElement).files || [])

  ;(e.target as HTMLInputElement).value = ''
}

function onFilesDropped(e: DragEvent) {
  isDragging.value = false
  addFiles(e.dataTransfer?.files || [])
}
</script>
