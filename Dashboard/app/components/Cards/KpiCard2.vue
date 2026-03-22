<script setup lang="ts">
interface KpiCategory {
  name: string;
  value: number;
  budget: number;
  color: string;
  trend?: number;
}

defineProps<KpiCategory>();

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};
</script>

<template>
  <UCard>
    <div class="mb-2 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="h-2 w-2 rounded-full" :style="{ backgroundColor: color }" />
        <span class="font-medium text-default">{{ name }}</span>
      </div>
      <div v-if="trend" class="flex items-center gap-2 text-sm">
        <span :class="trend >= 0 ? 'text-red-500' : 'text-(--ui-primary)'">
          {{ trend >= 0 ? "+" : "" }}{{ trend }}%
        </span>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <div class="text-lg font-semibold text-default">
        {{ formatCurrency(value) }}
      </div>
      <div class="text-sm text-toned dark:text-muted">
        {{ Math.round((value / budget) * 100) }}% of total
      </div>
    </div>

    <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-elevated">
      <div
        class="h-full rounded-full transition-all duration-300"
        :style="{
          backgroundColor: color,
          width: `${Math.min((value / budget) * 100, 100)}%`,
        }"
      />
    </div>
  </UCard>
</template>
