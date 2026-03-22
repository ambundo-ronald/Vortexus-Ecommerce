<script setup lang="ts">
import { ref, computed } from "vue";
import { getOrderTableColumns } from "../../config/orderTableColumns";
import type { SortBy, SortDir } from "~/types/Table";

const UBadge = resolveComponent("UBadge");
const UButton = resolveComponent("UButton");
const UInput = resolveComponent("UInput");
const UIcon = resolveComponent("UIcon");
const UCheckbox = resolveComponent("UCheckbox");

const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");

const columns = getOrderTableColumns({
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UIcon],
});

const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");

const { data, pending: isLoading } = await useFetch("/api/orders", {
  key: `orders`,
  params: computed(() => ({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    sortBy: sortBy.value,
    sortDir: sortDir.value,
  })),
});

const orderData = computed(() => data.value?.data ?? []);
const totalItems = computed(() => data.value?.totalItems ?? 0);

/**
 * These KPI computed properties will now safely operate on an empty array
 * during load time instead of `undefined`, returning 0.
 */
const totalOrders = computed(() => orderData.value.length);
const pendingOrders = computed(
  () => orderData.value.filter((order) => order.status === "Pending").length
);
const completedOrders = computed(
  () => orderData.value.filter((order) => order.status === "Paid").length
);
const failedOrders = computed(
  () => orderData.value.filter((order) => order.status === "Failed").length
);
</script>

<template>
  <div>
    <div class="flex justify-between items-center p-8 mb-4 pb-4">
      <h1 class="text-xl font-semibold">Orders</h1>
      <div class="flex items-center justify-end gap-2 w-full">
        <UInput
          v-model="searchQuery"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search orders..."
          :ui="{ leadingIcon: 'size-4' }"
        />
        <UButton variant="outline">
          <UIcon name="i-lucide-settings" />
          Settings
        </UButton>
        <UButton color="primary" variant="solid">
          <UIcon name="i-lucide-plus" />
          New Order
        </UButton>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 px-8">
      <CardsKpiCard2
        name="Total Orders"
        :value="totalOrders"
        :budget="totalItems"
        color="var(--color-info)"
        icon="i-lucide-shopping-cart"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Pending Orders"
        :value="pendingOrders"
        :budget="totalItems"
        color="var(--color-warning)"
        icon="i-lucide-clock"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Completed Orders"
        :value="completedOrders"
        :budget="totalItems"
        color="var(--color-success)"
        icon="i-lucide-check-circle"
        :loading="isLoading"
      />
      <CardsKpiCard2
        name="Failed Orders"
        :value="failedOrders"
        :budget="totalItems"
        color="var(--color-error)"
        icon="i-lucide-x-circle"
        :loading="isLoading"
      />
    </div>

    <div class="px-8">
      <UTable
        :data="orderData"
        :columns="columns"
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
