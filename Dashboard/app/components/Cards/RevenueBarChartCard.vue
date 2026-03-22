<script setup lang="ts">
const LegendPosition = {
  Top: "top",
  Bottom: "bottom",
  Left: "left",
  Right: "right",
};

interface BarChartCategory {
  name: string;
  color: string;
}

defineProps<{
  title: string;
  totalValue: string;
  data: Record<string, string | number>[];
  categories: Record<string, BarChartCategory>;
  yAxis: string[];
  xFormatter: (i: number) => string;
  yFormatter: (i: number) => string;
}>();
</script>
<template>
  <UCard>
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-normal text-lg text-highlighted mb-1">{{ title }}</h3>
      </div>
      <div class="text-default font-medium dark:font-semibold text-2xl">{{ totalValue }}</div>
    </div>
    <BarChart
      :data="data"
      :height="328"
      :categories="categories"
      :y-axis="yAxis"
      :group-padding="0"
      :bar-padding="0.2"
      :x-num-ticks="6"
      :y-num-ticks="5"
      :radius="4"
      :x-formatter="xFormatter"
      :y-formatter="yFormatter"
      :legend-position="LegendPosition.Bottom"
      :hide-legend="false"
      :y-grid-line="false"
    />
  </UCard>
</template>
