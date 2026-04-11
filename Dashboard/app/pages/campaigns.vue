<script setup lang="ts">
import type { TableColumn } from "@nuxt/ui";

const { getCampaigns } = useCampaigns();
const toast = useToast();

const selectedRange = ref(30);
const isLoading = ref(false);
const summary = ref<any | null>(null);

const rangeOptions = [
  { label: "Last 7 days", value: 7 },
  { label: "Last 30 days", value: 30 },
  { label: "Last 90 days", value: 90 },
];

const numberFormatter = new Intl.NumberFormat("en-US");
const moneyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const campaignColumns: TableColumn<any>[] = [
  {
    accessorKey: "name",
    header: "Campaign",
    cell: ({ row }) => h("div", [
      h("p", { class: "font-medium text-default" }, row.original.name),
      h("p", { class: "text-xs text-muted" }, row.original.description),
    ]),
  },
  { accessorKey: "channel", header: "Channel" },
  {
    accessorKey: "audience",
    header: "Audience",
    cell: ({ row }) => numberFormatter.format(Number(row.original.audience || 0)),
  },
  {
    accessorKey: "priority",
    header: "Priority",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: row.original.priority,
      color: row.original.priority === "High" ? "error" : row.original.priority === "Medium" ? "warning" : "neutral",
      variant: "soft",
    }),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: row.original.status,
      color: row.original.status === "ready" ? "success" : row.original.status === "blocked" ? "error" : "neutral",
      variant: "subtle",
    }),
  },
];

const opportunityColumns: TableColumn<any>[] = [
  { accessorKey: "name", header: "Product" },
  { accessorKey: "category", header: "Category" },
  {
    accessorKey: "units_sold",
    header: "Sold",
    cell: ({ row }) => numberFormatter.format(Number(row.original.units_sold || 0)),
  },
  {
    accessorKey: "revenue",
    header: "Revenue",
    cell: ({ row }) => moneyFormatter.format(Number(row.original.revenue || 0)),
  },
  {
    accessorKey: "stock",
    header: "Stock",
    cell: ({ row }) => h(resolveComponent("UBadge"), {
      label: `${row.original.stock || 0} units`,
      color: Number(row.original.stock || 0) < 10 ? "warning" : "success",
      variant: "soft",
    }),
  },
  { accessorKey: "signal", header: "Signal" },
];

async function loadCampaigns() {
  isLoading.value = true;
  const result = await getCampaigns(selectedRange.value);
  if (result.success)
    summary.value = result.data;
  else
    toast.add({
      title: "Could not load campaigns",
      description: result.error || "Please try again.",
      color: "error",
    });
  isLoading.value = false;
}

watch(selectedRange, loadCampaigns, { immediate: true });
</script>

<template>
  <div class="min-h-screen bg-default">
    <div class="flex flex-col gap-4 p-8 pb-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-xl font-semibold">Campaigns</h1>
        <p class="text-sm text-toned">
          Practical campaign opportunities calculated from live quote, order, product, and stock data.
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
        <UButton variant="outline" :loading="isLoading" @click="loadCampaigns">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 px-8 md:grid-cols-2 xl:grid-cols-4">
      <UCard>
        <p class="text-sm text-toned">Total customers</p>
        <p class="mt-2 text-3xl font-semibold">{{ numberFormatter.format(summary?.kpis?.total_customers || 0) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Active customers</p>
        <p class="mt-2 text-3xl font-semibold">{{ numberFormatter.format(summary?.kpis?.active_customers || 0) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Quote leads</p>
        <p class="mt-2 text-3xl font-semibold">{{ numberFormatter.format(summary?.kpis?.quote_leads || 0) }}</p>
      </UCard>
      <UCard>
        <p class="text-sm text-toned">Draft products</p>
        <p class="mt-2 text-3xl font-semibold">{{ numberFormatter.format(summary?.kpis?.draft_products || 0) }}</p>
      </UCard>
    </div>

    <div class="mt-6 grid grid-cols-1 gap-6 px-8 pb-8">
      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Campaign Queue</h3>
            <p class="text-sm text-toned">These are generated from the current database, not static template cards.</p>
          </div>
        </template>
        <UTable
          :columns="campaignColumns"
          :data="summary?.campaigns || []"
          :loading="isLoading"
        />
      </UCard>

      <UCard>
        <template #header>
          <div>
            <h3 class="text-base font-semibold">Product Opportunities</h3>
            <p class="text-sm text-toned">Top selling products in the selected period and whether stock can support promotion.</p>
          </div>
        </template>
        <UTable
          :columns="opportunityColumns"
          :data="summary?.product_opportunities || []"
          :loading="isLoading"
        />
      </UCard>
    </div>
  </div>
</template>
