<script setup lang="ts">
const props = withDefaults(defineProps<{
  loading?: boolean
  loadingLabel?: string
  empty?: boolean
  emptyIcon?: string
  emptyTitle?: string
  emptyDescription?: string
  error?: string
}>(), {
  loading: false,
  loadingLabel: 'Loading records',
  empty: false,
  emptyIcon: 'i-lucide-search-x',
  emptyTitle: 'No records found',
  emptyDescription: 'Try another search or clear the filters.',
  error: '',
})
</script>

<template>
  <div v-if="props.loading" class="flex items-center justify-center p-12 text-sm font-semibold text-slate-500">
    <UIcon name="i-lucide-loader-circle" class="mr-2 animate-spin" />
    {{ props.loadingLabel }}
  </div>

  <div v-else-if="props.error" class="p-12 text-center">
    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
      <UIcon name="i-lucide-triangle-alert" />
    </div>
    <h2 class="mt-4 text-lg font-black text-slate-950">
      Could not load records
    </h2>
    <p class="mt-1 text-sm text-slate-500">
      {{ props.error }}
    </p>
  </div>

  <div v-else-if="props.empty" class="p-12 text-center">
    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-[#30328f]">
      <UIcon :name="props.emptyIcon" />
    </div>
    <h2 class="mt-4 text-lg font-black text-slate-950">
      {{ props.emptyTitle }}
    </h2>
    <p class="mt-1 text-sm text-slate-500">
      {{ props.emptyDescription }}
    </p>
  </div>

  <slot v-else />
</template>
