<script setup lang="ts">
import CardsLatestOrdersCard from '../Cards/LatestOrdersCard.vue';
import CardsPopularProductsCard from '../Cards/PopularProductsCard.vue';
import { orders, products } from '~/data/dashboardData';

defineProps<{ childOrder: [0 | 1, 0 | 1] }>();

const cardComponents = [CardsLatestOrdersCard, CardsPopularProductsCard] as const;
</script>
<template>
  <div class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-6 w-full px-4 md:px-8 mb-6">
    <component
      :is="cardComponents[childOrder[0]]"
      v-bind="childOrder[0] === 0 ? { orders } : { products }"
      class="col-span-1 md:col-span-2 xl:col-span-3"
    />
    <component
      :is="cardComponents[childOrder[1]]"
      v-bind="childOrder[1] === 0 ? { orders } : { products }"
      class="col-span-1 md:col-span-2 xl:col-span-3"
    />
  </div>
</template>
