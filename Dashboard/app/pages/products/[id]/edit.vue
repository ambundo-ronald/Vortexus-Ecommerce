<script setup lang="ts">
import { computed } from "vue";
import type { FormSubmitEvent } from "@nuxt/ui";
import ProductForm, {
  type ProductFormSchema,
} from "~/components/Forms/ProductForm.vue";
import type { ProductImageItem } from "~/types/ProductImage";
import type { ProductStockData } from "~/types/ProductTableRow";

const { deleteProduct, getProduct, getCategoryOptions, syncProductImages, updateProduct } = useProduct();

const route = useRoute();

const product = ref<any>(null)
const categories = ref<{ label: string; value: string }[]>([])
const originalImages = ref<ProductImageItem[]>([])
const isDeleteModalOpen = ref(false)
const isDeleting = ref(false)

onMounted(async () => {
  const [productResult, categoryResult] = await Promise.all([
    getProduct(route.params.id as string),
    getCategoryOptions(),
  ])

  if (productResult.success)
    product.value = productResult.data

  if (categoryResult.success)
    categories.value = categoryResult.data
})

const pageTitle = computed(() => "Edit Product");

function discardChanges() {
  navigateTo("/products");
}
async function submit(event: FormSubmitEvent<ProductFormSchema>) {
  const result = await updateProduct(route.params.id as string, event.data)
  const toast = useToast();
  if (result.success) {
    const imageResult = await syncProductImages(route.params.id as string, images.value, originalImages.value)
    if (!imageResult.success) {
      toast.add({
        title: "Product updated with image issues",
        description: imageResult.error || "The product was updated, but some image changes failed.",
        color: "warning",
      });
      return
    }
    images.value = imageResult.data || images.value
    originalImages.value = [...images.value]
    toast.add({
      title: "Success!",
      description: "Product updated.",
      color: "success",
    });
    navigateTo("/products");
  } else {
    toast.add({
      title: "Update failed",
      description: result.error || 'Could not update product.',
      color: "error",
    });
  }
}

async function removeProduct() {
  const toast = useToast()
  isDeleting.value = true
  const result = await deleteProduct(route.params.id as string)
  if (result.success) {
    toast.add({
      title: "Product deleted",
      description: "The product was removed successfully.",
      color: "success",
    })
    return navigateTo("/products")
  }

  isDeleting.value = false
  toast.add({
    title: "Delete failed",
    description: result.error || "Could not delete product.",
    color: "error",
  })
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

const images = ref<ProductImageItem[]>([]);

watch(product, (value) => {
  images.value = value?.images || []
  originalImages.value = [...images.value]
}, { immediate: true })
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
              <UButton color="error" variant="outline" @click="isDeleteModalOpen = true">
                Delete
                <UIcon name="i-lucide-trash-2" />
              </UButton>
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

    <div
      v-if="isDeleteModalOpen"
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
          <span class="font-semibold">{{ product?.name || "this product" }}</span>
          from the catalogue?
        </p>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              color="neutral"
              variant="outline"
              :disabled="isDeleting"
              @click="isDeleteModalOpen = false"
            >
              Cancel
            </UButton>
            <UButton
              color="error"
              variant="solid"
              :loading="isDeleting"
              @click="removeProduct"
            >
              Delete product
            </UButton>
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>
