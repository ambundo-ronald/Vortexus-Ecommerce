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
];

const moneyFormatter = computed(() =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: summary.value?.currency || "KES",
    maximumFractionDigits: 0,
  }),
);

const numberFormatter = new Intl.NumberFormat("en-US");

const dailyChartData = computed(() =>
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

const latestOrderColumns: TableColumn<any>[] = [
  { accessorKey: "number", header: "Order", cell: ({ row }) => `#${row.original.number}` },
  { accessorKey: "customer", header: "Customer" },
  {
    accessorKey: "date",
    header: "Date",
    cell: ({ row }) => new Date(row.original.date).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
  },
  {
    accessorKey: "total",
    header: "Total",
    cell: ({ row }) => moneyFormatter.value.format(Number(row.original.total || 0)),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: row.original.status || "Pending",
      color: statusColor(row.original.status),
      variant: "subtle",
    }),
  },
];

const productColumns: TableColumn<any>[] = [
  { accessorKey: "name", header: "Product" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "quantity_sold", header: "Sold" },
  {
    accessorKey: "stock",
    header: "Stock",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: `${row.original.stock} units`,
      color: Number(row.original.stock) === 0 ? "error" : Number(row.original.stock) < 10 ? "warning" : "success",
      variant: "soft",
    }),
  },
];

function statusColor(status: string) {
  const normalized = (status || "").toLowerCase();
  if (["paid", "shipped", "delivered", "complete", "completed"].includes(normalized))
    return "success";
  if (["failed", "cancelled", "canceled"].includes(normalized))
    return "error";
  return "warning";
}

function formatNumber(value: number) {
  return numberFormatter.format(Number(value || 0));
}

async function loadDashboard() {
  isLoading.value = true;
  const result = await getDashboard(selectedRange.value);
  if (result.success)
    summary.value = result.data;
  else
    toast.add({
      title: "Could not load dashboard",
      description: result.error || "Please sign in and try again.",
      color: "error",
    });
  isLoading.value = false;
}

watch(selectedRange, loadDashboard, { immediate: true });
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-8">
      <div>
        <h1 class="text-xl font-semibold">Live Dashboard</h1>
        <p class="text-sm text-toned">
          Real-time snapshot from the backend database.
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
        <UButton variant="outline" :loading="isLoading" @click="loadDashboard">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-4">
      <CardsKpiCard2
        name="Revenue"
        :value="summary?.kpis?.revenue || 0"
        :budget="summary?.kpis?.revenue || 0"
        format="currency"
        :currency="summary?.currency || 'KES'"
        color="var(--color-success)"
        icon="i-lucide-banknote"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Orders"
        :value="summary?.kpis?.orders || 0"
        :budget="summary?.kpis?.orders || 0"
        color="var(--color-info)"
        icon="i-lucide-shopping-cart"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Products"
        :value="summary?.kpis?.products || 0"
        :budget="summary?.kpis?.products || 0"
        color="var(--color-warning)"
        icon="i-lucide-box"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Users"
        :value="summary?.kpis?.users || 0"
        :budget="summary?.kpis?.users || 0"
        color="var(--color-primary)"
        icon="i-lucide-users"
        :loading="isLoading"
      />
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 md:px-8 xl:grid-cols-3">
      <UCard class="xl:col-span-2">
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Revenue Trend</h3>
            <p class="text-sm text-toned">Daily revenue for the selected period.</p>
          </div>
        </template>
        <AreaChart
          :data="dailyChartData"
          :height="280"
          :categories="revenueCategories"
          :x-formatter="(tick: number) => dailyChartData[tick]?.date || ''"
          :y-formatter="(value: number) => moneyFormatter.format(value)"
          :hide-legend="true"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Product Mix</h3>
            <p class="text-sm text-toned">Catalogue share by category.</p>
          </div>
        </template>
        <DonutChart
          :data="(summary?.category_share || []).map((item: any) => item.value)"
          :height="220"
          :labels="summary?.category_share || []"
          :hide-legend="true"
        />
        <div class="mt-4 space-y-2">
          <div
            v-for="item in summary?.category_share || []"
            :key="item.name"
            class="flex items-center justify-between text-sm"
          >
            <div class="flex items-center gap-2">
              <span class="h-3 w-1 rounded" :style="{ backgroundColor: item.color }" />
              <span>{{ item.name }}</span>
            </div>
            <span class="font-medium">{{ item.value }}%</span>
          </div>
        </div>
      </UCard>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 md:px-8 xl:grid-cols-3">
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Operations</h3>
        </template>
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Pending workflow</span>
            <UBadge color="warning" variant="soft">{{ summary?.order_status?.pending || 0 }}</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Completed workflow</span>
            <UBadge color="success" variant="soft">{{ summary?.order_status?.completed || 0 }}</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Failed/cancelled workflow</span>
            <UBadge color="error" variant="soft">{{ summary?.order_status?.failed || 0 }}</UBadge>
          </div>
          <USeparator />
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Stock units</span>
            <span class="font-semibold">{{ formatNumber(summary?.kpis?.stock_units || 0) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Low stock products</span>
            <UBadge color="warning" variant="soft">{{ summary?.kpis?.low_stock_products || 0 }}</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-toned">Out of stock products</span>
            <UBadge color="error" variant="soft">{{ summary?.kpis?.out_of_stock_products || 0 }}</UBadge>
          </div>
        </div>
      </UCard>

      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold">Orders Volume</h3>
            <UBadge color="neutral" variant="soft">{{ selectedRange }} days</UBadge>
          </div>
        </template>
        <BarChart
          :data="dailyChartData"
          :height="260"
          :categories="orderCategories"
          :y-axis="['orders']"
          :x-formatter="(tick: number) => dailyChartData[tick]?.date || ''"
          :y-formatter="(value: number) => String(value)"
          :hide-legend="true"
        />
      </UCard>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-4 pb-8 md:px-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold">Latest Orders</h3>
            <NuxtLink to="/orders">
              <UButton color="neutral" variant="ghost" size="sm">View all</UButton>
            </NuxtLink>
          </div>
        </template>
        <UTable
          :columns="latestOrderColumns"
          :data="summary?.latest_orders || []"
          :loading="isLoading"
        />
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold">Top Products / Stock</h3>
            <NuxtLink to="/products">
              <UButton color="neutral" variant="ghost" size="sm">Manage products</UButton>
            </NuxtLink>
          </div>
        </template>
        <UTable
          :columns="productColumns"
          :data="summary?.popular_products || []"
          :loading="isLoading"
        />
      </UCard>
    </div>
  </div>
</template>
