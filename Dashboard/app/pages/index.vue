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

const numberFormatter = new Intl.NumberFormat("en-US");

const moneyFormatter = computed(() =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: summary.value?.currency || "KES",
    maximumFractionDigits: 0,
  }),
);

const dailyChartData = computed(() =>
  (summary.value?.daily || []).map((item: any) => ({
    date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    revenue: Number(item.revenue || 0),
    orders: Number(item.orders || 0),
  })),
);

const revenueCategories = {
  revenue: { name: "Revenue", color: "#30328f" },
};

const orderCategories = {
  orders: { name: "Orders", color: "#0f9f8f" },
};

const kpiCards = computed(() => [
  {
    label: "Revenue",
    value: formatCurrency(summary.value?.kpis?.revenue || 0),
    helper: `${formatNumber(summary.value?.kpis?.recent_orders || 0)} recent order(s)`,
    icon: "i-lucide-banknote",
    tone: "text-emerald-300",
    bg: "bg-emerald-400/10",
    to: "/finance",
  },
  {
    label: "Orders",
    value: formatNumber(summary.value?.kpis?.orders || 0),
    helper: `${formatNumber(summary.value?.order_status?.pending || 0)} need action`,
    icon: "i-lucide-receipt-text",
    tone: "text-blue-300",
    bg: "bg-blue-400/10",
    to: "/orders",
  },
  {
    label: "Catalogue",
    value: formatNumber(summary.value?.kpis?.products || 0),
    helper: `${formatNumber(summary.value?.kpis?.active_products || 0)} active products`,
    icon: "i-lucide-package",
    tone: "text-amber-300",
    bg: "bg-amber-400/10",
    to: "/products",
  },
  {
    label: "Customers",
    value: formatNumber(summary.value?.kpis?.users || 0),
    helper: `${formatNumber(summary.value?.kpis?.staff_users || 0)} staff account(s)`,
    icon: "i-lucide-users",
    tone: "text-violet-300",
    bg: "bg-violet-400/10",
    to: "/users",
  },
]);

const actionQueue = computed(() => [
  {
    label: "Pending orders",
    value: summary.value?.order_status?.pending || 0,
    icon: "i-lucide-clock-3",
    color: "warning",
    to: "/orders",
  },
  {
    label: "Low stock",
    value: summary.value?.kpis?.low_stock_products || 0,
    icon: "i-lucide-triangle-alert",
    color: "warning",
    to: "/catalog/stock-alerts",
  },
  {
    label: "Out of stock",
    value: summary.value?.kpis?.out_of_stock_products || 0,
    icon: "i-lucide-octagon-alert",
    color: "error",
    to: "/catalog/stock-alerts",
  },
  {
    label: "Failed/cancelled",
    value: summary.value?.order_status?.failed || 0,
    icon: "i-lucide-circle-x",
    color: "error",
    to: "/orders",
  },
]);

const quickActions = [
  { label: "Add product", icon: "i-lucide-plus", to: "/products/create" },
  { label: "Review orders", icon: "i-lucide-receipt", to: "/orders" },
  { label: "Check finance", icon: "i-lucide-wallet-cards", to: "/finance" },
  { label: "Upload media", icon: "i-lucide-image-plus", to: "/media" },
];

const latestOrderColumns: TableColumn<any>[] = [
  { accessorKey: "number", header: "Order", cell: ({ row }) => `#${row.original.number}` },
  { accessorKey: "customer", header: "Customer" },
  {
    accessorKey: "date",
    header: "Placed",
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
      label: `${formatNumber(row.original.stock || 0)} units`,
      color: Number(row.original.stock) === 0 ? "error" : Number(row.original.stock) < 10 ? "warning" : "success",
      variant: "soft",
    }),
  },
];

function statusColor(status: string) {
  const normalized = (status || "").toLowerCase();
  if (["paid", "shipped", "delivered", "complete", "completed"].includes(normalized))
    return "success";
  if (["failed", "cancelled", "canceled", "refunded", "returned"].includes(normalized))
    return "error";
  return "warning";
}

function formatNumber(value: number | string) {
  return numberFormatter.format(Number(value || 0));
}

function formatCurrency(value: number | string) {
  return moneyFormatter.value.format(Number(value || 0));
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
    <div class="px-4 py-4 md:px-8">
      <div class="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p class="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
              Store command centre
            </p>
            <h1 class="mt-1 text-2xl font-black text-slate-950 dark:text-white">
              Reesolmart Overview
            </h1>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Sales, order flow, stock risk, and catalogue health from live backend data.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
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

        <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <NuxtLink
            v-for="action in quickActions"
            :key="action.label"
            :to="action.to"
            class="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-[#30328f] hover:text-[#30328f] dark:border-slate-800 dark:text-slate-200 dark:hover:border-[#ff9f1c] dark:hover:text-[#ff9f1c]"
          >
            <UIcon :name="action.icon" class="h-4 w-4" />
            {{ action.label }}
          </NuxtLink>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-4">
      <NuxtLink
        v-for="card in kpiCards"
        :key="card.label"
        :to="card.to"
        class="rounded-lg border border-slate-200 bg-white p-4 transition hover:-translate-y-0.5 hover:border-[#30328f] dark:border-slate-800 dark:bg-slate-950 dark:hover:border-[#ff9f1c]"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
              {{ card.label }}
            </p>
            <p class="mt-3 text-2xl font-black text-slate-950 dark:text-white">
              {{ card.value }}
            </p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {{ card.helper }}
            </p>
          </div>
          <div class="flex h-11 w-11 items-center justify-center rounded-lg" :class="[card.bg, card.tone]">
            <UIcon :name="card.icon" class="h-5 w-5" />
          </div>
        </div>
      </NuxtLink>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-4">
      <UCard v-for="item in actionQueue" :key="item.label">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900">
              <UIcon :name="item.icon" class="h-5 w-5" />
            </div>
            <div>
              <p class="text-sm font-semibold">{{ item.label }}</p>
              <p class="text-xs text-toned">Needs monitoring</p>
            </div>
          </div>
          <NuxtLink :to="item.to">
            <UBadge :color="item.color as any" variant="soft">
              {{ formatNumber(item.value) }}
            </UBadge>
          </NuxtLink>
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-3">
      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="text-base font-semibold">Revenue trend</h3>
              <p class="text-sm text-toned">Net revenue from active orders in the selected period.</p>
            </div>
            <UBadge color="neutral" variant="soft">{{ selectedRange }} days</UBadge>
          </div>
        </template>
        <AreaChart
          :data="dailyChartData"
          :height="300"
          :categories="revenueCategories"
          :x-formatter="(tick: number) => dailyChartData[tick]?.date || ''"
          :y-formatter="(value: number) => moneyFormatter.format(value)"
          :hide-legend="true"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Store health</h3>
            <p class="text-sm text-toned">The most important operational checks.</p>
          </div>
        </template>
        <div class="space-y-4">
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <span class="text-sm text-toned">Stock units</span>
              <span class="font-black">{{ formatNumber(summary?.kpis?.stock_units || 0) }}</span>
            </div>
          </div>
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <span class="text-sm text-toned">Completed workflow</span>
              <UBadge color="success" variant="soft">{{ formatNumber(summary?.order_status?.completed || 0) }}</UBadge>
            </div>
          </div>
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <span class="text-sm text-toned">Media assets</span>
              <span class="font-black">{{ formatNumber(summary?.kpis?.media_assets || 0) }}</span>
            </div>
          </div>
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <span class="text-sm text-toned">Catalogue active rate</span>
              <span class="font-black">
                {{ summary?.kpis?.products ? Math.round(((summary?.kpis?.active_products || 0) / summary.kpis.products) * 100) : 0 }}%
              </span>
            </div>
          </div>
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-3">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Orders volume</h3>
            <p class="text-sm text-toned">Daily order count in the selected period.</p>
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

      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">Latest orders</h3>
              <p class="text-sm text-toned">Recent customer activity and fulfilment state.</p>
            </div>
            <NuxtLink to="/orders">
              <UButton color="neutral" variant="ghost" size="sm">View all</UButton>
            </NuxtLink>
          </div>
        </template>
        <UTable :columns="latestOrderColumns" :data="summary?.latest_orders || []" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 pb-8 md:px-8 xl:grid-cols-3">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Category mix</h3>
            <p class="text-sm text-toned">Catalogue share by category.</p>
          </div>
        </template>
        <div class="flex justify-center">
          <DonutChart
            :data="(summary?.category_share || []).map((item: any) => item.value)"
            :height="220"
            :labels="summary?.category_share || []"
            :hide-legend="true"
          />
        </div>
        <div class="mt-4 space-y-2">
          <div
            v-for="item in summary?.category_share || []"
            :key="item.name"
            class="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-800"
          >
            <div class="flex min-w-0 items-center gap-2">
              <span class="h-3 w-1 shrink-0 rounded" :style="{ backgroundColor: item.color }" />
              <span class="truncate">{{ item.name }}</span>
            </div>
            <span class="font-semibold">{{ item.value }}%</span>
          </div>
        </div>
      </UCard>

      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">Top products and stock</h3>
              <p class="text-sm text-toned">Products selling now, with stock risk visible.</p>
            </div>
            <NuxtLink to="/products">
              <UButton color="neutral" variant="ghost" size="sm">Manage</UButton>
            </NuxtLink>
          </div>
        </template>
        <UTable :columns="productColumns" :data="summary?.popular_products || []" :loading="isLoading" />
      </UCard>
    </div>
  </div>
</template>
