<script setup lang="ts">
interface KpiCategory {
  name: string;
  value: number | string;
  budget: number | string;
  color: string;
  format?: "number" | "currency";
  currency?: string;
  trend?: number;
}

const props = withDefaults(defineProps<KpiCategory>(), {
  format: "number",
  currency: "USD",
});

const numericValue = computed(() => {
  const value = Number(props.value);
  return Number.isFinite(value) ? value : 0;
});

const numericBudget = computed(() => {
  const value = Number(props.budget);
  return Number.isFinite(value) ? value : 0;
});

const formatValue = (value: number | string) => {
  if (typeof value === "string")
    return value;

  if (props.format === "number")
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value || 0);

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: props.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value || 0);
};

const percentOfTotal = computed(() => {
  if (!numericBudget.value)
    return 0;
  return Math.min(Math.round((numericValue.value / numericBudget.value) * 100), 100);
});
</script>

<template>
  <UCard class="rounded-xl">
    <div class="mb-2 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="h-2 w-2 rounded-full" :style="{ backgroundColor: color }" />
        <span class="font-semibold text-slate-950">{{ name }}</span>
      </div>
      <div v-if="trend" class="flex items-center gap-2 text-sm">
        <span :class="trend >= 0 ? 'text-red-500' : 'text-(--ui-primary)'">
          {{ trend >= 0 ? "+" : "" }}{{ trend }}%
        </span>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <div class="text-2xl font-black text-slate-950">
        {{ formatValue(value) }}
      </div>
      <div class="text-sm text-slate-500">
        {{ percentOfTotal }}% of total
      </div>
    </div>

    <div class="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">
      <div
        class="h-full rounded-full transition-all duration-300"
        :style="{
          backgroundColor: color,
          width: `${percentOfTotal}%`,
        }"
      />
    </div>
  </UCard>
</template>
