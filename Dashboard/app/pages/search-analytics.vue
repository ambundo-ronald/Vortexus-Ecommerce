<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

const { getSearchAnalytics } = useSearchAnalytics();
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

const topTermColumns: TableColumn<any>[] = [
  { accessorKey: "query", header: "Search term" },
  { accessorKey: "count", header: "Searches" },
  { accessorKey: "avg_results", header: "Avg. results" },
];

const zeroResultColumns: TableColumn<any>[] = [
  { accessorKey: "query", header: "No-result term" },
  { accessorKey: "count", header: "Count" },
];

const clickedProductColumns: TableColumn<any>[] = [
  { accessorKey: "product_title", header: "Product" },
  { accessorKey: "clicks", header: "Clicks" },
];

const userColumns: TableColumn<any>[] = [
  { accessorKey: "user_email", header: "Customer" },
  { accessorKey: "searches", header: "Searches" },
];

const eventColumns: TableColumn<any>[] = [
  { accessorKey: "created_at", header: "Time", cell: ({ row }) => formatDate(row.original.created_at) },
  { accessorKey: "event_type", header: "Event" },
  { accessorKey: "query", header: "Query" },
  { accessorKey: "product_title", header: "Product" },
  { accessorKey: "user_email", header: "Customer" },
];

const kpiCards = computed(() => [
  { label: "Searches", value: summary.value?.kpis?.total_searches || 0, icon: "i-lucide-search" },
  { label: "Image searches", value: summary.value?.kpis?.image_searches || 0, icon: "i-lucide-camera" },
  { label: "No-result searches", value: summary.value?.kpis?.zero_result_searches || 0, icon: "i-lucide-circle-alert" },
  { label: "Product clicks", value: summary.value?.kpis?.product_clicks || 0, icon: "i-lucide-mouse-pointer-click" },
  { label: "Search to cart", value: `${summary.value?.kpis?.search_to_cart_rate || 0}%`, icon: "i-lucide-shopping-cart" },
  { label: "Search to order", value: `${summary.value?.kpis?.search_to_order_rate || 0}%`, icon: "i-lucide-receipt" },
]);

function formatDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("en-KE", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadAnalytics() {
  isLoading.value = true;
  const result = await getSearchAnalytics(selectedRange.value);
  if (result.success)
    summary.value = result.data;
  else
    toast.add({
      title: "Could not load search analytics",
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
        <h1 class="text-xl font-semibold">Search Analytics</h1>
        <p class="text-sm text-toned">
          Track what customers search, what fails, what gets clicked, and what converts.
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

    <div class="grid grid-cols-1 gap-4 px-8 md:grid-cols-2 xl:grid-cols-6">
      <UCard v-for="card in kpiCards" :key="card.label">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase text-toned">{{ card.label }}</p>
            <p class="mt-2 text-2xl font-semibold">{{ card.value }}</p>
          </div>
          <UIcon :name="card.icon" class="size-6 text-primary" />
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 gap-6 p-8 xl:grid-cols-2">
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Top Search Terms</h3>
        </template>
        <UTable :columns="topTermColumns" :data="summary?.top_terms || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">No-Result Searches</h3>
        </template>
        <UTable :columns="zeroResultColumns" :data="summary?.zero_result_terms || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Clicked Products From Search</h3>
        </template>
        <UTable :columns="clickedProductColumns" :data="summary?.clicked_products || []" :loading="isLoading" />
      </UCard>

      <UCard>
        <template #header>
          <h3 class="text-base font-semibold">Searches by Customer</h3>
        </template>
        <UTable :columns="userColumns" :data="summary?.user_searches || []" :loading="isLoading" />
      </UCard>

      <UCard class="xl:col-span-2">
        <template #header>
          <h3 class="text-base font-semibold">Recent Search Events</h3>
        </template>
        <UTable :columns="eventColumns" :data="summary?.recent_events || []" :loading="isLoading" />
      </UCard>
    </div>
  </div>
</template>
