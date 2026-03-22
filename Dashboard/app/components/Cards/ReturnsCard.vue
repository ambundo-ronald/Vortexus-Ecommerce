<script setup lang="ts">
interface ChartDataItem {
  date: string;
  [key: string]: string | number;
}

const props = defineProps<{
  chartData: ChartDataItem[];
  categories: Record<string, { name: string; color: string }>;
  title: string;
  value: string;
}>();

const xFormatter = (tick: number, _i: number, _ticks: number[]): string => props.chartData[tick]?.date ?? ''
</script>
<template>
  <UCard>
    <div class="flex items-center justify-between">
      <h3 class="text-base font-normal text-lg text-highlighted mb-1">{{ title }}</h3>
    </div>
    <div class="text-default font-medium dark:font-semibold text-2xl">{{ value }}</div>
    <div class="mt-4">
      <AreaChart
        :data="chartData"
        :height="90"
        :x-num-ticks="4"
        :y-num-ticks="1"
        :categories="categories"
        :x-formatter="xFormatter"
        :curve-type="CurveType.Linear"
        :legend-position="LegendPosition.Top"
        :hide-legend="true"
      />
    </div>
  </UCard>
</template>
