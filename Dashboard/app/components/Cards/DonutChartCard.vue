<script setup lang="ts">
interface DonutChartData {
  name: string;
  value: number;
  color: string;
}

defineProps<{
  data: DonutChartData[];
  title: string;
  totalValue: string;
}>();
</script>
<template>
  <UCard>
    <div>
      <div class="flex items-center justify-between">
        <h3 class="text-base font-normal text-lg text-highlighted mb-1">{{ title }}</h3>
      </div>
      <div class="text-default font-medium dark:font-semibold text-2xl">
        {{ totalValue }}
      </div>
    </div>
    <DonutChart
      :data="data.map((i) => i.value)"
      :height="200"
      :labels="data"
      :hide-legend="true"
      :radius="0"
    >
      <div class="absolute text-center">
        <div class="font-semibold">Categories</div>
        <div class="">Last 24 hours</div>
      </div>
    </DonutChart>
    <div class="w-full space-y-2 divide-y divide-default">
      <div
        class="flex justify-between text-sm text-left py-4 font-medium text-toned tracking-tight"
      >
        <div>Category</div>
        <div>Share</div>
      </div>
      <div
        v-for="(cat, idx) in data"
        :key="idx"
        class="flex w-full items-center justify-between pb-2 text-sm text-toned dark:text-muted"
      >
        <div class="flex items-center gap-4">
          <div
            class="h-4 w-1 rounded"
            :style="{ backgroundColor: cat.color }"
          />
          <div>{{ cat.name }}</div>
        </div>
        <div>{{ cat.value }}%</div>
      </div>
    </div>
  </UCard>
</template>
