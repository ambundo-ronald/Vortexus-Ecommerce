<script setup lang="ts">
import { getProductTableColumns } from "~/config/productTableColumns";
import type { ProductTableRow } from "~/types/ProductTableRow";
import type { SortBy, SortDir } from "~/types/Table";

const UBadge = resolveComponent("UBadge");
const UCheckbox = resolveComponent("UCheckbox");
const UAvatar = resolveComponent("UAvatar");
const UButton = resolveComponent("UButton");

const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");
const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const statusFilter = ref<"" | "active" | "draft">("");
const pendingDeleteProduct = ref<ProductTableRow | null>(null);
const deletingProductId = ref<number | null>(null);

const { deleteProduct, getProducts } = useProduct();
const toast = useToast();

const columns = getProductTableColumns({
  onDelete: (product) => {
    pendingDeleteProduct.value = product;
  },
  onEdit: (product) => {
    navigateTo(`/products/${product.id}/edit`);
  },
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UAvatar],
});

const productData = ref<ProductTableRow[]>([]);
const totalItems = ref(0);
const isLoading = ref(false);

const statusOptions = [
  { label: "All statuses", value: "" },
  { label: "Active", value: "active" },
  { label: "Draft", value: "draft" },
];

async function loadProducts() {
  isLoading.value = true;
  const result = await getProducts({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    status: statusFilter.value,
    sortBy: sortBy.value,
    sortDir: sortDir.value,
  });

  if (result.success) {
    productData.value = result.data?.results ?? [];
    totalItems.value = result.data?.pagination?.total ?? 0;
  }
  else {
    productData.value = [];
    totalItems.value = 0;
    toast.add({
      title: "Could not load products",
      description: result.error || "Please try again.",
      color: "error",
    });
  }

  isLoading.value = false;
}

async function confirmDeleteProduct() {
  if (!pendingDeleteProduct.value)
    return;

  deletingProductId.value = pendingDeleteProduct.value.id;
  const result = await deleteProduct(pendingDeleteProduct.value.id);

  if (result.success) {
    toast.add({
      title: "Product deleted",
      description: `${pendingDeleteProduct.value.name} was removed successfully.`,
      color: "success",
    });
    pendingDeleteProduct.value = null;
    if (productData.value.length === 1 && currentPage.value > 1)
      currentPage.value -= 1;
    await loadProducts();
  }
  else {
    toast.add({
      title: "Delete failed",
      description: result.error || "Could not delete product.",
      color: "error",
    });
  }

  deletingProductId.value = null;
}

watch([currentPage, pageSize, searchQuery, sortBy, sortDir, statusFilter], loadProducts, { immediate: true });
watch([searchQuery, statusFilter, pageSize], () => {
  currentPage.value = 1;
});
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between p-8 pb-4">
      <h1 class="text-xl font-semibold">Products</h1>
      <div class="flex w-full items-center justify-end gap-2">
        <UInput
          v-model="searchQuery"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search products..."
          :ui="{ leadingIcon: 'size-4' }"
        />
        <USelect
          v-model="statusFilter"
          :items="statusOptions"
          value-attribute="value"
          option-attribute="label"
          class="min-w-40"
          size="lg"
        />
        <UButton variant="outline" :loading="isLoading" @click="loadProducts">
          <UIcon name="i-lucide-refresh-cw" />
          Refresh
        </UButton>
        <NuxtLink to="/products/create">
          <UButton color="primary" variant="solid">
            <UIcon name="i-lucide-plus" />
            New Product
          </UButton>
        </NuxtLink>
      </div>
    </div>

    <div class="px-8">
      <UTable
        class="cursor-pointer"
        :data="productData"
        :columns="columns"
        :loading="isLoading"
        @select="(product) => navigateTo(`/products/${product.id}/edit`)"
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

    <div
      v-if="pendingDeleteProduct"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <UCard class="w-full max-w-md">
        <template #header>
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-error/10 p-2 text-error">
              <UIcon name="i-lucide-trash-2" />
            </div>
            <div>
              <h3 class="font-semibold text-default">Delete product</h3>
              <p class="text-sm text-dimmed">This action cannot be undone.</p>
            </div>
          </div>
        </template>

        <p class="text-sm text-default">
          Delete
          <span class="font-semibold">{{ pendingDeleteProduct.name }}</span>
          from the catalogue?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              color="neutral"
              variant="outline"
              @click="pendingDeleteProduct = null"
            >
              Cancel
            </UButton>
            <UButton
              color="error"
              variant="solid"
              :loading="deletingProductId === pendingDeleteProduct.id"
              @click="confirmDeleteProduct"
            >
              Delete product
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
