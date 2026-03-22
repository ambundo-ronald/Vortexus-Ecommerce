<script setup lang="ts">
import type { ProductStockData } from '~/types/ProductTableRow'

const props = defineProps<{
  chartData: ProductStockData[];
  categories: Record<string, { name: string; color: string }>;
}>();

const formatStock = (tick: number) => `${tick} units`

</script>

<template>
  <div class="mx-auto max-w-xl sm:py-8">
    <UCard class="!bg-(--ui-bg)">
      <template #header>
        <div>
          <h2 class="text-lg font-medium">Stock</h2>
          <p class="text-sm text-(--ui-text-muted)">
            Monitor stock changes over the last 30 days.
          </p>
        </div>
      </template>

      <BarChart
        :data="chartData"
        :y-axis="['stock']"
        :height="120"
        :categories="categories"
        :min-max-ticks-only="true"
        :y-num-ticks="1"
        :curve-type="CurveType.MonotoneX"
        :legend-position="LegendPosition.Top"
        :x-formatter="(i) => `${chartData[i]?.date}`"
        :y-formatter="formatStock"
        :hide-legend="true"
      />
    </UCard>
  </div>
</template>
