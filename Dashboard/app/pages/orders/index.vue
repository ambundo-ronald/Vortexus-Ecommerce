<script setup lang="ts">
import { ref, watch } from "vue";
import { getOrderTableColumns } from "../../config/orderTableColumns";
import type { OrderTableRow } from "~/types/OrderTableRow";
import type { SortBy, SortDir } from "~/types/Table";

const UBadge = resolveComponent("UBadge");
const UButton = resolveComponent("UButton");
const UInput = resolveComponent("UInput");
const UIcon = resolveComponent("UIcon");
const UCheckbox = resolveComponent("UCheckbox");

const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");
const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const ALL_STATUSES = "__all__";
const statusFilter = ref(ALL_STATUSES);

const columns = getOrderTableColumns({
  onView: (order) => {
    navigateTo(`/orders/${order.id}`);
  },
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UIcon],
});

const { getOrders } = useOrder();
const toast = useToast();

const orderData = ref<OrderTableRow[]>([]);
const totalItems = ref(0);
const isLoading = ref(false);
const summary = ref({
  total: 0,
  pending: 0,
  completed: 0,
  failed: 0,
});

const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)));

const statusOptions = [
  { label: "All statuses", value: ALL_STATUSES },
  { label: "Pending", value: "Pending" },
  { label: "Processing", value: "Processing" },
  { label: "Packed", value: "Packed" },
  { label: "Paid", value: "Paid" },
  { label: "Shipped", value: "Shipped" },
  { label: "Delivered", value: "Delivered" },
  { label: "Cancelled", value: "Cancelled" },
];

async function loadOrders() {
  isLoading.value = true;
  const result = await getOrders({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    status: statusFilter.value === ALL_STATUSES ? "" : statusFilter.value,
    sortBy: sortBy.value,
    sortDir: sortDir.value,
  });

  if (result.success) {
    orderData.value = result.data?.results ?? [];
    totalItems.value = result.data?.pagination?.total ?? 0;
    summary.value = result.data?.summary ?? summary.value;
  }
  else {
    orderData.value = [];
    totalItems.value = 0;
    summary.value = { total: 0, pending: 0, completed: 0, failed: 0 };
    toast.add({
      title: "Could not load orders",
      description: result.error || "Please try again.",
      color: "error",
    });
  }

  isLoading.value = false;
}

watch([currentPage, pageSize, searchQuery, sortBy, sortDir, statusFilter], loadOrders, { immediate: true });
watch([searchQuery, statusFilter, pageSize], () => {
  currentPage.value = 1;
});

function openOrder(row: any) {
  const order = row?.original || row;
  if (order?.id)
    navigateTo(`/orders/${order.id}`);
}
</script>

<template>
  <div class="px-4 py-8 sm:px-6 lg:px-10">
    <div class="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <h1 class="text-3xl font-black tracking-tight text-slate-950">
          Orders
        </h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-600">
          Track customer orders, payment progress, fulfilment status, and shipping updates from one workspace.
        </p>
      </div>

      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <UInput
          v-model="searchQuery"
          class="w-full sm:w-72"
          size="lg"
          variant="outline"
          icon="i-lucide-search"
          placeholder="Search order, email, customer..."
          :ui="{ leadingIcon: 'size-4' }"
        />
        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="w-full sm:w-44"
          size="lg"
          variant="outline"
        />
        <UButton variant="outline" size="lg" :loading="isLoading" @click="loadOrders">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <CardsKpiCard2
        name="Total orders"
        :value="summary.total"
        :budget="totalItems"
        color="var(--color-info)"
        icon="i-lucide-shopping-cart"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Pending"
        :value="summary.pending"
        :budget="summary.total"
        color="var(--color-warning)"
        icon="i-lucide-clock"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Completed"
        :value="summary.completed"
        :budget="summary.total"
        color="var(--color-success)"
        icon="i-lucide-check-circle"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Failed"
        :value="summary.failed"
        :budget="summary.total"
        color="var(--color-error)"
        icon="i-lucide-x-circle"
        :loading="isLoading"
      />
    </div>

    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <UTable
        class="cursor-pointer"
        :data="orderData"
        :columns="columns"
        :loading="isLoading"
        @select="openOrder"
      />

      <div
        v-if="!isLoading && !orderData.length"
        class="border-t border-slate-200 px-6 py-16 text-center"
      >
        <div class="mx-auto flex size-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <UIcon name="i-lucide-receipt-text" class="size-7" />
        </div>
        <h2 class="mt-5 text-xl font-black text-slate-950">
          No orders found
        </h2>
        <p class="mx-auto mt-2 max-w-md text-sm text-slate-600">
          Try another search term, clear the status filter, or wait for new storefront orders.
        </p>
      </div>

      <div class="flex flex-col gap-3 border-t border-slate-200 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm text-slate-500">
          Page {{ currentPage }} of {{ totalPages }} · {{ totalItems }} orders
        </p>
        <UPagination
          :page="currentPage"
          :page-count="pageSize"
          :total="totalItems"
          @update:page="(page: number) => currentPage = page"
        />
      </div>
    </div>
  </div>
</template>
