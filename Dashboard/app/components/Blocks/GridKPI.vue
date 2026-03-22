<script setup lang="ts">
import { SalesData, RevenueDataCard, ReturnsData } from '~/data/dashboardData';

</script>
<template>
  <div class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-6 w-full px-4 md:px-8 mb-6">
    <div class="w-full md:col-span-1 xl:col-span-2">
      <CardsSalesCard
        title="Sales"
        value="1,245"
        :chart-data="SalesData.chartData"
        :categories="SalesData.categories"
      />
    </div>
    <div class="w-full md:col-span-1 xl:col-span-2">
      <CardsRevenueCard
        title="Revenue"
        value="$58,981.00"
        :chart-data="RevenueDataCard.chartData"
        :categories="RevenueDataCard.categories"
      />
    </div>
    <div class="w-full md:col-span-2">
      <CardsReturnsCard
        title="Returns"
        value="32"
        :chart-data="ReturnsData.chartData"
        :categories="ReturnsData.categories"
      />
    </div>
  </div>
</template>
