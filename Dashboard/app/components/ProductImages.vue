<template>
  <div class="mt-4">
    <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="(img, idx) in model"
        :key="`${img.src}-${idx}`"
        class="group relative flex rounded-xl border border-default p-2"
      >
        <img
          class="mx-auto max-h-[80px] max-w-full rounded-lg"
          :alt="img.alt"
          :src="img.src"
        >
        <div
          class="absolute inset-2 hidden items-center justify-center gap-2 bg-black/70 text-xl group-hover:flex"
        >
          <UIcon
            name="i-lucide-eye"
            class="cursor-pointer p-1.5 text-white hover:text-default"
            @click="previewImage(img.src)"
          />
          <UIcon
            name="i-lucide-trash"
            class="cursor-pointer p-1.5 text-white hover:text-default"
            @click="removeImage(idx)"
          />
        </div>
      </div>
      <div
        class="upload upload-draggable hover:border-primary relative min-h-fit cursor-pointer rounded-xl border border-dashed border-default"
      >
        <input
          class="upload-input draggable absolute inset-0 cursor-pointer opacity-0"
          type="file"
          multiple
          accept="image/*"
          @change="onFilesSelected"
        >
        <div
          class="flex min-h-[80px] max-w-full flex-col items-center justify-center px-4 py-2"
        >
          <div class="text-4xl text-dimmed">
            <UIcon size="20" name="i-lucide-upload" />
          </div>
          <p class="mt-1 text-center text-xs text-dimmed">
            Drop your image here, or
            <span class="text-primary-500">click to browse</span>
          </p>
        </div>
      </div>
    </div>
  </div>
  <p class="mt-4 text-xs text-dimmed">
    Image formats: .jpg, .jpeg, .png, .webp. Upload up to 5 images per
    product, with a maximum size of 5MB each.
  </p>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ProductImageItem } from '~/types/ProductImage'

const model = defineModel<ProductImageItem[]>({ default: [] })
const toast = useToast()

const isPreviewOpen = ref(false)
const previewSrc = ref('')

function removeImage(idx: number) {
  const image = model.value[idx]
  if (image?.file && image.src.startsWith('blob:'))
    URL.revokeObjectURL(image.src)
  model.value.splice(idx, 1)
}

function previewImage(src: string) {
  previewSrc.value = src
  isPreviewOpen.value = true
}

function onFilesSelected(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files)
    return

  for (const file of Array.from(files)) {
    if (!file.type.startsWith('image/'))
      continue

    if (model.value.length >= 5) {
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

    model.value.push({
      src: URL.createObjectURL(file),
      alt: file.name,
      file,
    })
  }

  ;(e.target as HTMLInputElement).value = ''
}
</script>
