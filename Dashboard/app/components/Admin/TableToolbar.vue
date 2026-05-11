<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  description?: string
  search?: string
  searchPlaceholder?: string
  loading?: boolean
  createLabel?: string
  createIcon?: string
  refreshLabel?: string
}>(), {
  description: '',
  search: '',
  searchPlaceholder: 'Search...',
  loading: false,
  createLabel: '',
  createIcon: 'i-lucide-plus',
  refreshLabel: 'Refresh',
})

const emit = defineEmits<{
  'update:search': [value: string]
  refresh: []
  create: []
}>()
</script>

<template>
  <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
    <div>
      <h1 class="text-2xl font-black text-slate-950">
        {{ props.title }}
      </h1>
      <p v-if="props.description" class="mt-1 text-sm text-slate-500">
        {{ props.description }}
      </p>
    </div>

    <div class="flex w-full flex-wrap items-center gap-2 lg:w-auto lg:justify-end">
      <UInput
        :model-value="props.search"
        class="min-w-56 flex-1 lg:max-w-sm"
        color="neutral"
        variant="outline"
        size="lg"
        icon="i-lucide-search"
        :placeholder="props.searchPlaceholder"
        @update:model-value="emit('update:search', String($event || ''))"
      />

      <slot name="filters" />

      <UButton color="neutral" variant="outline" :loading="props.loading" @click="emit('refresh')">
        <UIcon name="i-lucide-refresh-cw" />
        {{ props.refreshLabel }}
      </UButton>

      <UButton v-if="props.createLabel" color="primary" variant="solid" @click="emit('create')">
        <UIcon :name="props.createIcon" />
        {{ props.createLabel }}
      </UButton>

      <slot name="actions" />
    </div>
  </div>
</template>
