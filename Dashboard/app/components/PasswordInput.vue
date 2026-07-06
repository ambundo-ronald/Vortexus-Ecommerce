<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue?: string | number
}>(), {
  modelValue: "",
})

const emit = defineEmits<{
  "update:modelValue": [value: string | number]
}>()

const isVisible = ref(false)
</script>

<template>
  <UInput
    v-bind="$attrs"
    :model-value="props.modelValue"
    :type="isVisible ? 'text' : 'password'"
    @update:model-value="emit('update:modelValue', $event as string | number)"
  >
    <template #trailing>
      <UButton
        color="neutral"
        variant="ghost"
        size="xs"
        square
        :aria-label="isVisible ? 'Hide password' : 'Show password'"
        :aria-pressed="isVisible"
        :icon="isVisible ? 'i-lucide-eye-off' : 'i-lucide-eye'"
        @click="isVisible = !isVisible"
      />
    </template>
  </UInput>
</template>
