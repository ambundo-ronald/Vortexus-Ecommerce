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
const statusFilter = ref("");

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

const statusOptions = [
  { label: "All statuses", value: "" },
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
    status: statusFilter.value,
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
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between p-8 pb-4">
      <h1 class="text-xl font-semibold">Orders</h1>
      <div class="flex w-full items-center justify-end gap-2">
        <UInput
          v-model="searchQuery"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search orders..."
          :ui="{ leadingIcon: 'size-4' }"
        />
        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-44"
          size="lg"
        />
        <UButton variant="outline" :loading="isLoading" @click="loadOrders">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-8 px-8 sm:grid-cols-2 lg:grid-cols-4">
      <CardsKpiCard2
        name="Total Orders"
        :value="summary.total"
        :budget="totalItems"
        color="var(--color-info)"
        icon="i-lucide-shopping-cart"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Pending Orders"
        :value="summary.pending"
        :budget="summary.total"
        color="var(--color-warning)"
        icon="i-lucide-clock"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Completed Orders"
        :value="summary.completed"
        :budget="summary.total"
        color="var(--color-success)"
        icon="i-lucide-check-circle"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Failed Orders"
        :value="summary.failed"
        :budget="summary.total"
        color="var(--color-error)"
        icon="i-lucide-x-circle"
        :loading="isLoading"
      />
    </div>

    <div class="px-8">
      <UTable
        class="cursor-pointer"
        :data="orderData"
        :columns="columns"
        :loading="isLoading"
        @select="(order) => navigateTo(`/orders/${order.id}`)"
      />
      <div class="flex justify-end pt-4">
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
