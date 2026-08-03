<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

const { getDashboard } = useDashboard();
const { getSearchAnalytics } = useSearchAnalytics();
const toast = useToast();

const selectedRange = ref(30);
const isLoading = ref(false);
const summary = ref<any | null>(null);
const searchSummary = ref<any | null>(null);

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

const daily = computed(() =>
  (summary.value?.daily || []).map((item: any) => ({
    date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    revenue: Number(item.revenue || 0),
    orders: Number(item.orders || 0),
  })),
);

const revenueAndOrdersCategories = {
  revenue: { name: "Revenue", color: "#30328f" },
  orders: { name: "Orders", color: "#0f9f8f" },
};

const revenueCategories = {
  revenue: { name: "Revenue", color: "#30328f" },
};

const orderCategories = {
  orders: { name: "Orders", color: "#0f9f8f" },
};

const revenueTotal = computed(() => Number(summary.value?.kpis?.revenue || 0));
const orderTotal = computed(() => Number(summary.value?.kpis?.orders || 0));
const productTotal = computed(() => Number(summary.value?.kpis?.products || 0));
const activeProductTotal = computed(() => Number(summary.value?.kpis?.active_products || 0));
const stockUnits = computed(() => Number(summary.value?.kpis?.stock_units || 0));
const lowStockTotal = computed(() => Number(summary.value?.kpis?.low_stock_products || 0));
const outOfStockTotal = computed(() => Number(summary.value?.kpis?.out_of_stock_products || 0));

const averageOrderValue = computed(() => orderTotal.value ? revenueTotal.value / orderTotal.value : 0);
const revenuePerActiveProduct = computed(() => activeProductTotal.value ? revenueTotal.value / activeProductTotal.value : 0);
const activeProductRate = computed(() => productTotal.value ? Math.round((activeProductTotal.value / productTotal.value) * 100) : 0);
const stockRiskRate = computed(() => productTotal.value ? Math.round(((lowStockTotal.value + outOfStockTotal.value) / productTotal.value) * 100) : 0);
const searchNoResultRate = computed(() => {
  const total = Number(searchSummary.value?.kpis?.total_searches || 0);
  const zero = Number(searchSummary.value?.kpis?.zero_result_searches || 0);
  return total ? Math.round((zero / total) * 100) : 0;
});

const executiveMetrics = computed(() => [
  {
    label: "Revenue",
    value: formatCurrency(revenueTotal.value),
    helper: `${formatCurrency(averageOrderValue.value)} avg order`,
    icon: "i-lucide-banknote",
    tone: "text-emerald-300",
  },
  {
    label: "Orders",
    value: formatNumber(orderTotal.value),
    helper: `${formatNumber(summary.value?.order_status?.pending || 0)} pending`,
    icon: "i-lucide-shopping-cart",
    tone: "text-blue-300",
  },
  {
    label: "Product health",
    value: `${activeProductRate.value}%`,
    helper: `${formatNumber(activeProductTotal.value)} active of ${formatNumber(productTotal.value)}`,
    icon: "i-lucide-package-check",
    tone: "text-amber-300",
  },
  {
    label: "Search conversion",
    value: `${searchSummary.value?.kpis?.search_to_order_rate || 0}%`,
    helper: `${formatNumber(searchSummary.value?.kpis?.total_searches || 0)} searches`,
    icon: "i-lucide-search-check",
    tone: "text-violet-300",
  },
]);

const operationalMetrics = computed(() => [
  { label: "Completed orders", value: summary.value?.order_status?.completed || 0, color: "success", icon: "i-lucide-circle-check" },
  { label: "Failed/cancelled", value: summary.value?.order_status?.failed || 0, color: "error", icon: "i-lucide-circle-x" },
  { label: "Low stock", value: lowStockTotal.value, color: "warning", icon: "i-lucide-triangle-alert" },
  { label: "Out of stock", value: outOfStockTotal.value, color: "error", icon: "i-lucide-octagon-alert" },
  { label: "Stock units", value: stockUnits.value, color: "neutral", icon: "i-lucide-warehouse" },
  { label: "Stock risk rate", value: `${stockRiskRate.value}%`, color: stockRiskRate.value > 20 ? "warning" : "success", icon: "i-lucide-shield-alert" },
]);

const searchMetrics = computed(() => [
  { label: "Text searches", value: searchSummary.value?.kpis?.total_searches || 0, icon: "i-lucide-search" },
  { label: "Image searches", value: searchSummary.value?.kpis?.image_searches || 0, icon: "i-lucide-camera" },
  { label: "No-result rate", value: `${searchNoResultRate.value}%`, icon: "i-lucide-circle-alert" },
  { label: "Product clicks", value: searchSummary.value?.kpis?.product_clicks || 0, icon: "i-lucide-mouse-pointer-click" },
  { label: "Search to cart", value: `${searchSummary.value?.kpis?.search_to_cart_rate || 0}%`, icon: "i-lucide-shopping-bag" },
  { label: "Search to order", value: `${searchSummary.value?.kpis?.search_to_order_rate || 0}%`, icon: "i-lucide-receipt" },
]);

const categoryColumns: TableColumn<any>[] = [
  { accessorKey: "name", header: "Category" },
  { accessorKey: "value", header: "Share", cell: ({ row }) => `${row.original.value}%` },
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

const topTermColumns: TableColumn<any>[] = [
  { accessorKey: "query", header: "Search term" },
  { accessorKey: "count", header: "Searches" },
  { accessorKey: "avg_results", header: "Avg results" },
];

const zeroResultColumns: TableColumn<any>[] = [
  { accessorKey: "query", header: "Missing demand" },
  { accessorKey: "count", header: "Count" },
  { accessorKey: "last_seen", header: "Last seen", cell: ({ row }) => formatDate(row.original.last_seen) },
];

const clickedProductColumns: TableColumn<any>[] = [
  { accessorKey: "product_title", header: "Product" },
  { accessorKey: "clicks", header: "Clicks" },
  { accessorKey: "last_seen", header: "Last seen", cell: ({ row }) => formatDate(row.original.last_seen) },
];

const latestOrderColumns: TableColumn<any>[] = [
  { accessorKey: "number", header: "Order", cell: ({ row }) => `#${row.original.number}` },
  { accessorKey: "customer", header: "Customer" },
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

const eventColumns: TableColumn<any>[] = [
  { accessorKey: "created_at", header: "Time", cell: ({ row }) => formatDate(row.original.created_at) },
  { accessorKey: "event_type", header: "Event" },
  { accessorKey: "query", header: "Query" },
  { accessorKey: "product_title", header: "Product" },
  { accessorKey: "user_email", header: "Customer" },
];

function statusColor(status: string) {
  const normalized = (status || "").toLowerCase();
  if (["paid", "shipped", "delivered", "complete", "completed"].includes(normalized))
    return "success";
  if (["failed", "cancelled", "canceled", "refunded", "returned"].includes(normalized))
    return "error";
  return "warning";
}

function formatDate(value: string) {
  if (!value)
    return "-";
  return new Date(value).toLocaleString("en-KE", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatNumber(value: number | string) {
  return numberFormatter.format(Number(value || 0));
}

function formatCurrency(value: number | string) {
  return moneyFormatter.value.format(Number(value || 0));
}

async function loadAnalytics() {
  isLoading.value = true;
  const [dashboardResult, searchResult] = await Promise.all([
    getDashboard(selectedRange.value),
    getSearchAnalytics(selectedRange.value),
  ]);

  if (dashboardResult.success)
    summary.value = dashboardResult.data;
  else
    toast.add({
      title: "Could not load store analytics",
      description: dashboardResult.error || "Please try again.",
      color: "error",
    });

  if (searchResult.success)
    searchSummary.value = searchResult.data;
  else
    toast.add({
      title: "Could not load search analytics",
      description: searchResult.error || "Search data will be unavailable on this view.",
      color: "warning",
    });

  isLoading.value = false;
}

watch(selectedRange, loadAnalytics, { immediate: true });
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="px-4 py-4 md:px-8">
      <div class="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p class="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
              Business intelligence
            </p>
            <h1 class="mt-1 text-2xl font-black text-slate-950 dark:text-white">
              Analytics Dashboard
            </h1>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Sales performance, customer demand, search behavior, catalogue health, and stock risk in one workspace.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <NuxtLink to="/search-analytics">
              <UButton color="neutral" variant="outline" icon="i-lucide-search-check">
                Search detail
              </UButton>
            </NuxtLink>
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
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-4">
      <UCard v-for="metric in executiveMetrics" :key="metric.label">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase text-toned">{{ metric.label }}</p>
            <p class="mt-3 text-2xl font-black">{{ metric.value }}</p>
            <p class="mt-1 text-sm text-toned">{{ metric.helper }}</p>
          </div>
          <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900" :class="metric.tone">
            <UIcon :name="metric.icon" class="h-5 w-5" />
          </div>
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-3">
      <UCard class="xl:col-span-2">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="text-base font-semibold">Revenue and order momentum</h3>
              <p class="text-sm text-toned">Daily movement across the selected period.</p>
            </div>
            <UBadge color="neutral" variant="soft">{{ selectedRange }} days</UBadge>
          </div>
        </template>
        <AreaChart
          :data="daily"
          :height="320"
          :categories="revenueAndOrdersCategories"
          :x-formatter="(tick: number) => daily[tick]?.date || ''"
          :y-formatter="(value: number) => String(value)"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Commercial efficiency</h3>
            <p class="text-sm text-toned">Simple ratios from current data.</p>
          </div>
        </template>
        <div class="space-y-3">
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p class="text-xs font-bold uppercase text-toned">Average order value</p>
            <p class="mt-1 text-xl font-black">{{ formatCurrency(averageOrderValue) }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p class="text-xs font-bold uppercase text-toned">Revenue per active product</p>
            <p class="mt-1 text-xl font-black">{{ formatCurrency(revenuePerActiveProduct) }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p class="text-xs font-bold uppercase text-toned">No-result search rate</p>
            <p class="mt-1 text-xl font-black">{{ searchNoResultRate }}%</p>
          </div>
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-6">
      <UCard v-for="metric in operationalMetrics" :key="metric.label">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase text-toned">{{ metric.label }}</p>
            <p class="mt-2 text-xl font-black">{{ typeof metric.value === 'number' ? formatNumber(metric.value) : metric.value }}</p>
          </div>
          <UBadge :color="metric.color as any" variant="soft">
            <UIcon :name="metric.icon" />
          </UBadge>
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-3">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Orders by day</h3>
            <p class="text-sm text-toned">Volume trend independent of revenue.</p>
          </div>
        </template>
        <BarChart
          :data="daily"
          :height="260"
          :categories="orderCategories"
          :y-axis="['orders']"
          :x-formatter="(tick: number) => daily[tick]?.date || ''"
          :y-formatter="(value: number) => String(value)"
          :hide-legend="true"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Revenue by day</h3>
            <p class="text-sm text-toned">Daily active-order revenue.</p>
          </div>
        </template>
        <BarChart
          :data="daily"
          :height="260"
          :categories="revenueCategories"
          :y-axis="['revenue']"
          :x-formatter="(tick: number) => daily[tick]?.date || ''"
          :y-formatter="(value: number) => moneyFormatter.format(value)"
          :hide-legend="true"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Category mix</h3>
            <p class="text-sm text-toned">Catalogue share by category.</p>
          </div>
        </template>
        <UTable :columns="categoryColumns" :data="summary?.category_share || []" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:grid-cols-2 md:px-8 xl:grid-cols-6">
      <UCard v-for="metric in searchMetrics" :key="metric.label">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase text-toned">{{ metric.label }}</p>
            <p class="mt-2 text-xl font-black">{{ typeof metric.value === 'number' ? formatNumber(metric.value) : metric.value }}</p>
          </div>
          <UIcon :name="metric.icon" class="h-5 w-5 text-primary" />
        </div>
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold">Top search terms</h3>
              <p class="text-sm text-toned">What customers are actively looking for.</p>
            </div>
            <NuxtLink to="/search-analytics">
              <UButton color="neutral" variant="ghost" size="sm">Open detail</UButton>
            </NuxtLink>
          </div>
        </template>
        <UTable :columns="topTermColumns" :data="searchSummary?.top_terms || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">No-result demand</h3>
            <p class="text-sm text-toned">Terms that may require new catalogue coverage.</p>
          </div>
        </template>
        <UTable :columns="zeroResultColumns" :data="searchSummary?.zero_result_terms || []" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 md:px-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Clicked products from search</h3>
            <p class="text-sm text-toned">Products customers choose after searching.</p>
          </div>
        </template>
        <UTable :columns="clickedProductColumns" :data="searchSummary?.clicked_products || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Top products and stock</h3>
            <p class="text-sm text-toned">Best movers with stock visibility.</p>
          </div>
        </template>
        <UTable :columns="productColumns" :data="summary?.popular_products || []" :loading="isLoading" />
      </UCard>
    </div>

    <div class="mt-4 grid grid-cols-1 gap-4 px-4 pb-8 md:px-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Latest orders</h3>
            <p class="text-sm text-toned">Recent order activity included in analytics.</p>
          </div>
        </template>
        <UTable :columns="latestOrderColumns" :data="summary?.latest_orders || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Recent search events</h3>
            <p class="text-sm text-toned">Fresh customer intent across search and image search.</p>
          </div>
        </template>
        <UTable :columns="eventColumns" :data="searchSummary?.recent_events || []" :loading="isLoading" />
      </UCard>
    </div>
  </div>
</template>
