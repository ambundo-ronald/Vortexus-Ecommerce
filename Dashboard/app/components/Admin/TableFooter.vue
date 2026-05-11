<script setup lang="ts">
const props = withDefaults(defineProps<{
  shown: number
  total: number
  label: string
  note?: string
  page?: number
  pageSize?: number
}>(), {
  note: '',
  page: 1,
  pageSize: 0,
})

const emit = defineEmits<{
  'update:page': [value: number]
}>()

const totalPages = computed(() => {
  if (!props.pageSize)
    return 1

  return Math.max(1, Math.ceil(props.total / props.pageSize))
})
</script>

<template>
  <div class="mt-4 flex flex-col gap-3 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
    <p>
      Showing {{ props.shown }} of {{ props.total }} {{ props.label }}<span v-if="props.note">. {{ props.note }}</span>
    </p>

    <UPagination
      v-if="props.pageSize && totalPages > 1"
      :page="props.page"
      :page-count="props.pageSize"
      :total="props.total"
      @update:page="emit('update:page', $event)"
    />
  </div>
</template>
