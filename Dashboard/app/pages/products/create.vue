<script setup lang="ts">
import type { FormSubmitEvent } from "@nuxt/ui";
import ProductForm, { type ProductFormSchema } from "~/components/Forms/ProductForm.vue";
import type { ProductImageItem } from "~/types/ProductImage";

const pageTitle = computed(() => "New Product");
const { createProduct, getCategoryOptions, getProductOptions, syncProductImages } = useProduct();
const { getAttributes } = useAttributes();
const isSaving = ref(false)

function discardChanges() {
  navigateTo("/products");
}
async function submit(event: FormSubmitEvent<ProductFormSchema>) {
  if (isSaving.value)
    return

  isSaving.value = true
  const toast = useToast();
  const result = await createProduct(event.data);
  if (result.success) {
    const productId = result.data?.id
    if (productId && images.value.length) {
      const imageResult = await syncProductImages(productId, images.value, [])
      if (!imageResult.success) {
        toast.add({
          title: "Product saved with image issues",
          description: imageResult.error || "The product was created, but one or more images failed to upload.",
          color: "warning",
        });
        isSaving.value = false
        return navigateTo(`/products/${productId}/edit`)
      }
    }
    toast.add({ title: "Product created", description: "The product is now saved.", color: "success" });
    await navigateTo("/products");
  } else {
    toast.add({
      title: "Create failed",
      description: result.error || "Could not create product.",
      color: "error",
    });
  }
  isSaving.value = false
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
const categories = ref<{ label: string; value: string }[]>([]);
const productOptions = ref<{ label: string; value: string }[]>([]);
const attributeDefinitions = ref<any[]>([]);

async function searchProductOptions(query: string) {
  const result = await getProductOptions({ search: query, pageSize: 20, maxPages: 1 })
  return result.success ? result.data : []
}

onMounted(async () => {
  const [categoryResult, productOptionsResult, attributeResult] = await Promise.all([
    getCategoryOptions(),
    getProductOptions(),
    getAttributes({ pageSize: 500 }),
  ])
  if (categoryResult.success)
    categories.value = categoryResult.data
  if (productOptionsResult.success)
    productOptions.value = productOptionsResult.data
  if (attributeResult.success)
    attributeDefinitions.value = attributeResult.data?.results ?? []
})

const images = ref<ProductImageItem[]>([]);
</script>

<template>
  <div class="w-full">
    <ProductForm
      :status-options="statusOptions"
      :categories="categories"
      :product-options="productOptions"
      :attribute-definitions="attributeDefinitions"
      :search-products="searchProductOptions"
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
  </div>
</template>
