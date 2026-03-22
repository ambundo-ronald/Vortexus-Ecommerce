<script lang="ts" setup>
interface DateAggregateData {
  date: string;
  impressions: number;
  clicks: number;
  ctr: number;
  averagePosition: number;
}

const props = defineProps<{
  chartData: DateAggregateData[];
  categories: Record<string, { name: string; color: string }>;
}>();

const xFormatter = (tick: number, _i: number, _ticks: number[]): string => {
  return String(props.chartData[tick]?.date ?? "");
};
</script>

<template>
  <UCard>
    <div class="mb-8 space-y-2">
      <h3 class="font-semibold text-lg text-highlighted">Search Performance</h3>
    </div>

    <LineChart
      :data="chartData"
      :height="275"
      :x-num-ticks="4"
      :y-num-ticks="4"
      :x-formatter="xFormatter"
      :categories="categories"
      :grid-line-y="true"
      :curve-type="CurveType.Linear"
      :legend-position="LegendPosition.Bottom"
    />
  </UCard>
</template>
