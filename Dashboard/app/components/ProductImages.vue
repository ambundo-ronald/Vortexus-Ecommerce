<template>
  <div class="mt-4">
    <div
      class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-2"
    >
      <div
        v-for="(img, idx) in model"
        :key="img.src + idx"
        class="group relative rounded-xl border border-default p-2 flex"
      >
        <img
          class="rounded-lg max-h-[80px] mx-auto max-w-full"
          :alt="img.alt"
          :src="img.src"
        >
        <div
          class="absolute inset-2 bg-black/70 group-hover:flex hidden text-xl items-center justify-center gap-2"
        >
          <UIcon
            name="i-lucide-eye"
            class="text-white hover:text-default cursor-pointer p-1.5"
            @click="previewImage(img.src)"
          />
          <UIcon
            name="i-lucide-trash"
            class="text-white hover:text-default cursor-pointer p-1.5"
            @click="removeImage(idx)"
          />
        </div>
      </div>
      <div
        class="upload upload-draggable hover:border-primary min-h-fit border border-dashed border-default rounded-xl cursor-pointer relative"
      >
        <input
          class="upload-input draggable absolute inset-0 opacity-0 cursor-pointer"
          type="file"
          multiple
          accept="image/*"
          @change="onFilesSelected"
        >
        <div
          class="max-w-full flex flex-col px-4 py-2 justify-center items-center min-h-[80px]"
        >
          <div class="text-4xl text-dimmed">
            <UIcon size="20" name="i-lucide-upload" />
          </div>
          <p class="text-center mt-1 text-xs text-dimmed">
            Drop your image here, or
            <span class="text-primary-500">click to browse</span>
          </p>
        </div>
      </div>
    </div>
  </div>
  <p class="text-xs text-dimmed mt-4">
    Image formats: .jpg, .jpeg, .png, preferred size: 1:1, file size is
    restricted to a maximum of 500kb.
  </p>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface ProductImage {
  src: string
  alt: string
}

const model = defineModel<ProductImage[]>({ default: [] });

const isPreviewOpen = ref(false);
const previewSrc = ref('');

function removeImage(idx: number) {
  model.value.splice(idx, 1)
}

function previewImage(src: string) {
  previewSrc.value = src;
  isPreviewOpen.value = true;
}

function onFilesSelected(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files) return
  for (const file of Array.from(files)) {
    if (!file.type.startsWith('image/')) continue
    if (file.size > 500 * 1024) continue
    const reader = new FileReader()
    reader.onload = (ev) => {
      model.value.push({ src: ev.target?.result as string, alt: file.name })
    }
    reader.readAsDataURL(file)
  }
}
</script>
