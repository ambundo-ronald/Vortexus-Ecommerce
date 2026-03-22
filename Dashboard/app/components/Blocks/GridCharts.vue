<script setup lang="ts">
import { RevenueData, RevenueCategoriesMultiple, xFormatter, yFormatter, DonutData } from '~/data/dashboardData';
import { computed } from 'vue';

const props = defineProps<{ childOrder: [0 | 1, 0 | 1] }>();

const flexDirection = computed(() =>
  props.childOrder[0] === 1 ? 'md:flex-row-reverse' : 'md:flex-row'
);
</script>
<template>
  <div :class="`flex flex-col ${flexDirection} w-full px-4 md:px-8 mb-6 gap-6`">
    <div class="w-full md:w-8/12">
      <CardsRevenueBarChartCard
        title="Revenue"
        total-value="$4589.00"
        :data="RevenueData"
        :categories="RevenueCategoriesMultiple"
        :y-axis="['total']"
        :x-formatter="xFormatter"
        :y-formatter="yFormatter"
      />
    </div>
    <div class="w-full md:w-4/12 relative">
      <CardsDonutChartCard
        title="Revenue"
        total-value="$4589.00"
        :data="DonutData"
      />
    </div>
  </div>
</template>
