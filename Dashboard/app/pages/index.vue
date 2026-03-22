<script lang="ts" setup>

const selectedRange = ref("Last 30 days");
const gridOrder = ref([0, 1, 2]);
const childOrders = ref([
  [0, 1], 
  [0, 1], 
  [0, 1],
]);

function shuffleGrids() {
  // Shuffle grid order
  gridOrder.value = gridOrder.value
    .map((v) => ({ v, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map(({ v }) => v);
  // Shuffle child order for each grid
  childOrders.value = childOrders.value.map(order =>
    order
      .map((v) => ({ v, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(({ v }) => v)
  );
}

const GridKPI = defineAsyncComponent(() => import('~/components/Blocks/GridKPI.vue'));
const GridCharts = defineAsyncComponent(() => import('~/components/Blocks/GridCharts.vue'));
const GridTables = defineAsyncComponent(() => import('~/components/Blocks/GridTables.vue'));
const gridComponents = shallowRef([GridKPI, GridCharts, GridTables]);
</script>
<template>
  <div class="min-h-screen bg-default">
    <div
      class="flex flex-col md:flex-row md:justify-between md:items-center py-4 px-4 md:px-8 gap-4 md:gap-0"
    >
      <div>
        <h1 class="text-xl font-semibold">Analytics</h1>
        <!-- <p class="text-toned">
          This is an overview of your site data and traffic
        </p> -->
      </div>
      <div
        class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto"
      >
        <UButton variant="outline" class="w-full sm:w-auto">
          <UIcon name="i-lucide-list-filter-plus" />
          Filter
        </UButton>
        <USelect
          v-model="selectedRange"
          :items="['Last 30 days', 'Last 7 days', 'Last 90 days']"
          class="w-full sm:w-36"
        />
        <UButton variant="soft" class="w-full sm:w-auto" @click="shuffleGrids">
          <UIcon name="i-lucide-shuffle" />
          Shuffle Grids
        </UButton>
      </div>
    </div>
    <component
      :is="gridComponents[gridIdx]"
      v-for="(gridIdx, i) in gridOrder"
      :key="i"
      v-bind="{ childOrder: childOrders[i] }"
    />
  </div>
</template>
