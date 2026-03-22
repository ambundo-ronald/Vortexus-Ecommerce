<script setup lang="ts">
import { computed } from "vue";
import type { FormSubmitEvent } from "@nuxt/ui";
import ProductForm, {
  type ProductFormSchema,
} from "~/components/Forms/ProductForm.vue";
import type { ProductStockData } from "~/types/ProductTableRow";

const { getProduct } = useProduct();

const route = useRoute();

const { data: product } = await getProduct(route.params.id as string);

const pageTitle = computed(() => "Edit Product");

function discardChanges() {
  navigateTo("/products");
}
async function submit(event: FormSubmitEvent<ProductFormSchema>) {
  const toast = useToast();
  toast.add({
    title: "Success!",
    description: "New product saved.",
    color: "success",
  });
  navigateTo("/products");
  console.log(event);
}

const statusOptions = [
  {
    label: "Active",
    value: "active",
    icon: "i-lucide-circle-dot",
    color: "success",
  },
  {
    label: "Draft",
    value: "draft",
    icon: "i-lucide-file-text",
    color: "neutral",
  },
  {
    label: "Archived",
    value: "archived",
    icon: "i-lucide-archive",
    color: "error",
  },
];
const categories = [
  { label: "Electronics", value: "electronics" },
  { label: "Clothing", value: "clothing" },
  { label: "Home & Garden", value: "home-garden" },
  { label: "Books", value: "books" },
];

const stockChartData = ref<ProductStockData[]>(
  Array.from({ length: 30 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (29 - i));
    return {
      date: formatDate(date),
      stock: Math.floor(90 + Math.random() * 40),
    };
  })
);

const stockChartCategories = {
  stock: { name: "Product Stock", color: "#3b82f6" },
};

function formatDate(date: Date) {
  const options: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
  };
  return new Intl.DateTimeFormat("en-US", options).format(date);
}

const images = ref(product?.images || []);
</script>

<template>
  <div class="w-full mt-8">
    <ProductForm
      :values="product"
      :status-options="statusOptions"
      :categories="categories"
      @on-submit="submit"
    >
      <template #header="{ submit }">
        <div class="max-w-screen-xl mx-auto py-4">
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
              <UButton
                icon="i-lucide-arrow-left"
                color="neutral"
                variant="ghost"
                size="md"
                square
                aria-label="Back to products"
                @click="discardChanges"
              />
              <h1 class="text-xl font-semibold text-default truncate">
                {{ pageTitle }}
              </h1>
            </div>
            <div class="flex items-center gap-3">
              <UButton
                label="Discard"
                color="neutral"
                variant="outline"
                @click="discardChanges"
              />
              <UButton color="primary" variant="solid" @click="submit">
                Save
                <UIcon name="i-lucide-save" />
              </UButton>
            </div>
          </div>
        </div>
      </template>
      <template #images>
        <ProductImages v-model="images" />
      </template>
      <template #stock>
        <ChartsProductStock
          :chart-data="stockChartData"
          :categories="stockChartCategories"
        />
      </template>
    </ProductForm>
  </div>
</template>
