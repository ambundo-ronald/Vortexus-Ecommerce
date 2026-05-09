<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  description?: string
  confirmLabel: string
  cancelLabel?: string
  loading?: boolean
  icon?: string
  color?: 'primary' | 'neutral' | 'error' | 'warning' | 'success' | 'info'
}>(), {
  description: '',
  cancelLabel: 'Cancel',
  loading: false,
  icon: 'i-lucide-triangle-alert',
  color: 'error',
})

const emit = defineEmits<{
  cancel: []
  confirm: []
}>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="flex items-center gap-3">
          <div :class="['rounded-full p-2', props.color === 'error' ? 'bg-error/10 text-error' : 'bg-slate-100 text-slate-700']">
            <UIcon :name="props.icon" />
          </div>
          <div>
            <h3 class="font-semibold text-default">
              {{ props.title }}
            </h3>
            <p v-if="props.description" class="text-sm text-dimmed">
              {{ props.description }}
            </p>
          </div>
        </div>
      </template>

      <slot />

      <template #footer>
        <div class="flex justify-end gap-3">
          <UButton color="neutral" variant="outline" :disabled="props.loading" @click="emit('cancel')">
            {{ props.cancelLabel }}
          </UButton>
          <UButton :color="props.color" variant="solid" :loading="props.loading" @click="emit('confirm')">
            {{ props.confirmLabel }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
