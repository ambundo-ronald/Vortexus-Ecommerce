<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

const { getDashboard } = useDashboard();
const toast = useToast();

const selectedRange = ref(30);
const isLoading = ref(false);
const summary = ref<any | null>(null);

const rangeOptions = [
  { label: "Last 7 days", value: 7 },
  { label: "Last 30 days", value: 30 },
  { label: "Last 90 days", value: 90 },
  { label: "Last 365 days", value: 365 },
];

const moneyFormatter = computed(() =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: summary.value?.currency || "KES",
    maximumFractionDigits: 0,
  }),
);

const daily = computed(() =>
  (summary.value?.daily || []).map((item: any) => ({
    date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    revenue: Number(item.revenue || 0),
    orders: Number(item.orders || 0),
  })),
);

const revenueCategories = {
  revenue: { name: "Revenue", color: "#2563eb" },
};

const orderCategories = {
  orders: { name: "Orders", color: "#059669" },
};

const categoryColumns: TableColumn<any>[] = [
  { accessorKey: "name", header: "Category" },
  {
    accessorKey: "value",
    header: "Share",
    cell: ({ row }) => `${row.original.value}%`,
  },
];

async function loadAnalytics() {
  isLoading.value = true;
  const result = await getDashboard(selectedRange.value);
  if (result.success)
    summary.value = result.data;
  else
    toast.add({
      title: "Could not load analytics",
      description: result.error || "Please try again.",
      color: "error",
    });
  isLoading.value = false;
}

watch(selectedRange, loadAnalytics, { immediate: true });
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 p-8 pb-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-xl font-semibold">Operational Analytics</h1>
        <p class="text-sm text-toned">
          Database-backed sales, orders, product mix, and stock signals.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <USelect
          v-model="selectedRange"
          :items="rangeOptions"
          value-attribute="value"
          option-attribute="label"
          class="w-40"
        />
        <UButton variant="outline" :loading="isLoading" @click="loadAnalytics">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 px-8 xl:grid-cols-3">
      <UCard class="xl:col-span-2">
        <template #header>
          <h3 class="text-base font-semibold">Revenue by Day</h3>
        </template>
        <BarChart
          :data="daily"
          :height="320"
          :categories="revenueCategories"
          :y-axis="['revenue']"
          :x-formatter="(tick: number) => daily[tick]?.date || ''"
          :y-formatter="(value: number) => moneyFormatter.format(value)"
        />
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Order Status</h3>
        </template>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Pending / active</span>
            <UBadge color="warning" variant="soft">{{ summary?.order_status?.pending || 0 }}</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Completed</span>
            <UBadge color="success" variant="soft">{{ summary?.order_status?.completed || 0 }}</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Failed / cancelled</span>
            <UBadge color="error" variant="soft">{{ summary?.order_status?.failed || 0 }}</UBadge>
          </div>
        </div>
      </UCard>

      <UCard class="xl:col-span-2">
        <template #header>
          <h3 class="text-base font-semibold">Orders by Day</h3>
        </template>
        <AreaChart
          :data="daily"
          :height="300"
          :categories="orderCategories"
          :x-formatter="(tick: number) => daily[tick]?.date || ''"
          :y-formatter="(value: number) => String(value)"
          :hide-legend="true"
        />
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Category Mix</h3>
        </template>
        <UTable
          :columns="categoryColumns"
          :data="summary?.category_share || []"
          :loading="isLoading"
        />
      </UCard>
    </div>
  </div>
</template>
