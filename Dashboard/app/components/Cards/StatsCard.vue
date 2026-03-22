<script lang="ts" setup>
defineProps<{
  metric: string;
  current: number | string;
  percentChange: number;
}>();
</script>
<template>
  <UCard>
    <div class="text-sm text-(--ui-text-toned)">
      {{ metric }}
    </div>

    <div class="mt-2 flex items-center justify-start gap-8">
      <p class="font-semibold text-3xl text-highlighted tracking-wide">
        {{ current }}
      </p>

      <div class="flex items-center flex-col items-start text-sm">
        <div class="flex items-center gap-1">
          <UIcon
            :name="
              percentChange > 0 ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'
            "
            :class="percentChange > 0 ? 'text-emerald-500' : 'text-red-500'"
          />
          <div
            :class="percentChange > 0 ? 'text-emerald-500' : 'text-red-500'"
            class="mr-1"
          >
            {{ percentChange }}%
          </div>
        </div>
        <span class="text-(--ui-text-dimmed)">from previous month</span>
      </div>
    </div>
  </UCard>
</template>
