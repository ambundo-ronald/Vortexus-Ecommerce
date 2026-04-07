<script setup lang="ts">
import { getProductTableColumns } from "~/config/productTableColumns";
import type { SortBy, SortDir } from "~/types/Table";

const UBadge = resolveComponent("UBadge");
const UCheckbox = resolveComponent("UCheckbox");
const UAvatar = resolveComponent("UAvatar");
const UButton = resolveComponent("UButton");

const sortBy = ref<SortBy>();
const sortDir = ref<SortDir>("asc");

const columns = getProductTableColumns({
  sortBy,
  sortDir,
  components: [UButton, UBadge, UCheckbox, UAvatar],
});

const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const { getProducts } = useProduct()

const productData = ref([])
const totalItems = ref(0)
const isLoading = ref(false)

async function loadProducts() {
  isLoading.value = true
  const result = await getProducts({
    page: currentPage.value,
    pageSize: pageSize.value,
    search: searchQuery.value,
    sortBy: sortBy.value,
    sortDir: sortDir.value,
  })

  if (result.success) {
    productData.value = result.data?.results ?? []
    totalItems.value = result.data?.pagination?.total ?? 0
  }
  else {
    productData.value = []
    totalItems.value = 0
  }
  isLoading.value = false
}

watch([currentPage, pageSize, searchQuery, sortBy, sortDir], loadProducts, { immediate: true })
</script>

<template>
  <div>
    <div class="flex justify-between items-center p-8 mb-4 pb-4">
      <h1 class="text-xl font-semibold">Products</h1>
      <div class="flex items-center justify-end gap-2 w-full">
        <UInput
          v-model="searchQuery"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search products..."
          :ui="{ leadingIcon: 'size-4' }"
        />
        <UButton variant="outline">
          <UIcon name="i-lucide-settings" />
          Settings
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
  </div>
</template>
