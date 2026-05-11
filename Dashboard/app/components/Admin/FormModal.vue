<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  description?: string
  error?: string
  saving?: boolean
  saveLabel: string
  cancelLabel?: string
  maxWidth?: string
}>(), {
  description: '',
  error: '',
  saving: false,
  cancelLabel: 'Cancel',
  maxWidth: 'max-w-2xl',
})

const emit = defineEmits<{
  close: []
  submit: []
}>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
    <UCard :class="['max-h-[92vh] w-full overflow-y-auto', props.maxWidth]">
      <template #header>
        <div class="flex items-center justify-between gap-4">
          <div>
            <h3 class="font-semibold text-default">
              {{ props.title }}
            </h3>
            <p v-if="props.description" class="text-sm text-dimmed">
              {{ props.description }}
            </p>
          </div>
          <UButton icon="i-lucide-x" color="neutral" variant="ghost" square :disabled="props.saving" @click="emit('close')" />
        </div>
      </template>

      <form @submit.prevent="emit('submit')">
        <div v-if="props.error" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
          {{ props.error }}
        </div>

        <slot />

        <div class="mt-6 flex justify-end gap-3">
          <UButton color="neutral" variant="outline" :disabled="props.saving" @click="emit('close')">
            {{ props.cancelLabel }}
          </UButton>
          <UButton type="submit" color="primary" variant="solid" :loading="props.saving">
            {{ props.saveLabel }}
          </UButton>
        </div>
      </form>
    </UCard>
  </div>
</template>
