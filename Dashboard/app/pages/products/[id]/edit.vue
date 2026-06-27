<script setup lang="ts">
import { computed } from "vue";
import type { FormSubmitEvent } from "@nuxt/ui";
import ProductForm, {
  type ProductFormSchema,
} from "~/components/Forms/ProductForm.vue";
import type { ProductImageItem } from "~/types/ProductImage";

const { deleteProduct, getProduct, getCategoryOptions, getProductOptions, syncProductImages, updateProduct } = useProduct();
const { getAttributes } = useAttributes();

const route = useRoute();

const product = ref<any>(null)
const categories = ref<{ label: string; value: string }[]>([])
const productOptions = ref<{ label: string; value: string }[]>([])
const attributeDefinitions = ref<any[]>([])
const originalImages = ref<ProductImageItem[]>([])
const isDeleteModalOpen = ref(false)
const isDeleting = ref(false)
const isSaving = ref(false)
const isLoadingProduct = ref(true)
const loadError = ref("")

onMounted(async () => {
  isLoadingProduct.value = true
  const [productResult, categoryResult, attributeResult] = await Promise.all([
    getProduct(route.params.id as string),
    getCategoryOptions(),
    getAttributes({ pageSize: 500 }),
  ])

  if (productResult.success)
    product.value = productResult.data
  else
    loadError.value = productResult.error || "Could not load this product."

  if (categoryResult.success)
    categories.value = categoryResult.data
  if (attributeResult.success)
    attributeDefinitions.value = attributeResult.data?.results ?? []

  isLoadingProduct.value = false

  const productOptionsResult = await getProductOptions({
    excludeId: route.params.id as string,
    maxPages: 10,
    pageSize: 100,
  })
  if (productOptionsResult.success)
    productOptions.value = productOptionsResult.data
})

const pageTitle = computed(() => "Edit Product");

function discardChanges() {
  navigateTo("/products");
}
async function submit(event: FormSubmitEvent<ProductFormSchema>) {
  if (isSaving.value)
    return

  isSaving.value = true
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
      isSaving.value = false
      return
    }
    images.value = imageResult.data || images.value
    originalImages.value = [...images.value]
    const refreshedProduct = await getProduct(route.params.id as string)
    if (refreshedProduct.success) {
      product.value = refreshedProduct.data
      images.value = refreshedProduct.data?.images || []
      originalImages.value = [...images.value]
    }
    toast.add({
      title: "Product updated",
      description: "The storefront will reflect the saved product data.",
      color: "success",
    });
    await navigateTo("/products");
  } else {
    toast.add({
      title: "Update failed",
      description: result.error || 'Could not update product.',
      color: "error",
    });
  }
  isSaving.value = false
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
const images = ref<ProductImageItem[]>([]);

watch(product, (value) => {
  images.value = value?.images || []
  originalImages.value = [...images.value]
}, { immediate: true })
</script>

<template>
  <div class="w-full">
    <div v-if="isLoadingProduct" class="mx-auto max-w-screen-xl space-y-4 py-8">
      <USkeleton class="h-10 w-64" />
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <USkeleton class="h-80 lg:col-span-2" />
        <USkeleton class="h-80" />
      </div>
    </div>

    <div v-else-if="loadError" class="mx-auto max-w-screen-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-600">
        <UIcon name="i-lucide-triangle-alert" />
      </div>
      <h1 class="mt-4 text-xl font-black text-slate-950">Product unavailable</h1>
      <p class="mt-2 text-sm text-slate-500">{{ loadError }}</p>
      <UButton class="mt-6" color="primary" variant="solid" @click="discardChanges">
        Back to products
      </UButton>
    </div>

    <ProductForm
      v-else
      :values="product"
      :status-options="statusOptions"
      :categories="categories"
      :product-options="productOptions"
      :attribute-definitions="attributeDefinitions"
      @on-submit="submit"
    >
      <template #header="{ submit }">
        <div class="mx-auto max-w-screen-xl py-4">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
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
              <h1 class="truncate text-2xl font-black text-slate-950">
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
              <UButton color="primary" variant="solid" :loading="isSaving" @click="submit">
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
