<script setup lang="ts">
import * as z from "zod/v4";
import type { FormSubmitEvent } from "@nuxt/ui";
import type { AttributeItem } from "~/composables/useAttributes";
import { DOMAIN_PRODUCT_CLASS_OPTIONS, STANDARD_PRODUCT_CLASS } from "~/composables/useProduct";

const props = defineProps<{
  values?: Partial<ProductFormSchema>;
  statusOptions: { label: string; value: string; icon: string; color: string }[];
  categories: { label: string; value: string }[];
  productOptions?: { label: string; value: string }[];
  attributeDefinitions?: AttributeItem[];
  searchProducts?: (query: string) => Promise<{ label: string; value: string }[]>;
}>();

const emit = defineEmits<{
  (e: "onSubmit", event: FormSubmitEvent<any>): void;
}>();

const productSchema = z.object({
  name: z
    .string({ error: "Product name is required" })
    .min(1, "Product name cannot be empty"),
  description: z.string().optional(),
  slug: z.string().optional(),
  metaTitle: z.string().optional(),
  metaDescription: z.string().optional(),
  recommendedProductIds: z.array(z.coerce.number()).optional(),
  images: z.array(z.object({ src: z.string(), alt: z.string() })).optional(),
  price: z.number({
    error: (issue) => (issue.input === undefined ? "" : ""),
  }),
  currency: z.string().default("KES"),
  originalPrice: z
    .number({
      error: (issue) => (issue.input === undefined ? "" : ""),
    })
    .optional(),
  chargeTax: z.boolean().default(true),
  sku: z.string().optional(),
  stock: z
    .number({
      error: (issue) =>
        issue.input === undefined
          ? "Stock quantity is required"
          : "stock is not a number",
    })
    .int("Stock quantity must be an integer")
    .min(0, "Stock must be at least 0"),
  weight: z
    .number({
      error: (issue) =>
        issue.input === undefined
          ? "Weight is required"
          : "Weight must be a number",
    })
    .min(0, "Weight must be at least 0")
    .nullable()
    .optional(),
  dimensions: z.string().optional(),
  status: z
    .enum(["active", "draft"], {
      error: "Status is required",
    })
    .default("draft"),
  category: z
    .string()
    .optional()
    .default(""),
  brand: z.string().optional(),
  tags: z.string().optional(),
  attributes: z.record(z.string(), z.union([z.string(), z.number(), z.boolean(), z.null()])).optional(),
  productClass: z.string().optional().default(STANDARD_PRODUCT_CLASS),
  engineeringBrand: z.string().optional(),
  packingDimensions: z.record(z.string(), z.object({
    value: z.union([z.string(), z.number()]).optional(),
    unit: z.string().optional(),
  })).optional(),
  specificationRows: z.array(z.object({
    key: z.string().optional(),
    value: z.union([z.string(), z.number()]).optional(),
    unit: z.string().optional(),
  })).optional(),
});

export type ProductFormSchema = z.infer<typeof productSchema>;

const localFormState = reactive<ProductFormSchema>({
  name: "",
  description: "",
  slug: "",
  metaTitle: "",
  metaDescription: "",
  recommendedProductIds: [],
  images: [],
  price: 0,
  currency: "KES",
  originalPrice: undefined,
  chargeTax: true,
  sku: "",
  stock: 0,
  weight: null,
  dimensions: "",
  status: "draft",
  category: "",
  brand: "",
  tags: "",
  attributes: {},
  productClass: STANDARD_PRODUCT_CLASS,
  engineeringBrand: "",
  packingDimensions: {
    length: { value: "", unit: "cm" },
    width: { value: "", unit: "cm" },
    height: { value: "", unit: "cm" },
    weight: { value: "", unit: "g" },
    quantity: { value: "", unit: "pcs" },
  },
  specificationRows: [],
  ...props.values,
}) as ProductFormSchema;

watch(
  () => props.values,
  (values) => {
    if (!values) return
    Object.assign(localFormState, {
      name: "",
      description: "",
      slug: "",
      metaTitle: "",
      metaDescription: "",
      recommendedProductIds: [],
      images: [],
      price: 0,
      currency: "KES",
      originalPrice: undefined,
      chargeTax: true,
      sku: "",
      stock: 0,
      weight: null,
      dimensions: "",
      status: "draft",
      category: "",
      brand: "",
      tags: "",
      attributes: {},
      productClass: STANDARD_PRODUCT_CLASS,
      engineeringBrand: "",
      packingDimensions: {
        length: { value: "", unit: "cm" },
        width: { value: "", unit: "cm" },
        height: { value: "", unit: "cm" },
        weight: { value: "", unit: "g" },
        quantity: { value: "", unit: "pcs" },
      },
      specificationRows: [],
      ...values,
    })
    if (!localFormState.attributes)
      localFormState.attributes = {}
    if (!localFormState.packingDimensions)
      localFormState.packingDimensions = {}
    if (!localFormState.specificationRows)
      localFormState.specificationRows = []
  },
  { immediate: true, deep: true },
)

const selectedRecommendedProductId = ref("")
const categorySearch = ref("")
const recommendedProductSearch = ref("")
const isCategoryPickerOpen = ref(false)
const isRecommendedPickerOpen = ref(false)
const isSearchingRecommendedProducts = ref(false)
const productOptionPool = ref<{ label: string; value: string }[]>([])
let recommendedSearchTimer: ReturnType<typeof setTimeout> | null = null
let recommendedSearchRequestId = 0

function mergeProductOptions(options: { label: string; value: string }[] = []) {
  const byId = new Map(productOptionPool.value.map(option => [String(option.value), option]))
  for (const option of options) {
    if (!option?.value)
      continue
    byId.set(String(option.value), {
      label: option.label || `Product #${option.value}`,
      value: String(option.value),
    })
  }
  productOptionPool.value = Array.from(byId.values())
}

watch(
  () => props.productOptions,
  options => mergeProductOptions(options || []),
  { immediate: true, deep: true },
)

watch(
  recommendedProductSearch,
  (value) => {
    if (!props.searchProducts)
      return
    if (recommendedSearchTimer)
      clearTimeout(recommendedSearchTimer)

    const query = value.trim()
    if (query.length < 2) {
      isSearchingRecommendedProducts.value = false
      return
    }

    const requestId = ++recommendedSearchRequestId
    recommendedSearchTimer = setTimeout(async () => {
      isSearchingRecommendedProducts.value = true
      try {
        const results = await props.searchProducts?.(query)
        if (requestId === recommendedSearchRequestId)
          mergeProductOptions(results || [])
      }
      finally {
        if (requestId === recommendedSearchRequestId)
          isSearchingRecommendedProducts.value = false
      }
    }, 250)
  },
)

const filteredCategories = computed(() => {
  const search = categorySearch.value.trim().toLowerCase()
  const items = [{ label: 'Uncategorized', value: '__uncategorized__' }, ...props.categories]
  if (!search)
    return items
  return items.filter(item => item.label.toLowerCase().includes(search) || String(item.value).toLowerCase().includes(search))
})
const selectedCategoryLabel = computed(() => {
  const value = localFormState.category || '__uncategorized__'
  return filteredCategories.value.find(item => item.value === value)?.label
    || [{ label: 'Uncategorized', value: '__uncategorized__' }, ...props.categories].find(item => item.value === value)?.label
    || 'Uncategorized'
})
const selectedRecommendedProducts = computed(() => {
  const selectedIds = new Set((localFormState.recommendedProductIds || []).map(Number))
  return Array.from(selectedIds).map((id) => {
    const option = productOptionPool.value.find(item => Number(item.value) === id)
    return option || { label: `Product #${id}`, value: String(id) }
  })
})
const dynamicAttributeDefinitions = computed(() =>
  (props.attributeDefinitions || [])
    .filter(attribute => !['brand', 'tags', 'dimensions', 'weight_grams'].includes(attribute.code))
    .sort((a, b) => {
      const parentA = a.parent_attribute_id || 0
      const parentB = b.parent_attribute_id || 0
      if (parentA !== parentB)
        return parentA - parentB
      return a.name.localeCompare(b.name)
    }),
)
const domainProductClassOptions = DOMAIN_PRODUCT_CLASS_OPTIONS
const dimensionUnitOptions = [
  { label: 'mm', value: 'mm' },
  { label: 'cm', value: 'cm' },
  { label: 'm', value: 'm' },
]
const weightUnitOptions = [
  { label: 'g', value: 'g' },
  { label: 'kg', value: 'kg' },
  { label: 'mg', value: 'mg' },
]
const quantityUnitOptions = [
  { label: 'pcs', value: 'pcs' },
  { label: 'pc', value: 'pc' },
]
const availableRecommendedProductOptions = computed(() => {
  const selectedIds = new Set((localFormState.recommendedProductIds || []).map(Number))
  const search = recommendedProductSearch.value.trim().toLowerCase()
  return productOptionPool.value.filter((option) => {
    if (selectedIds.has(Number(option.value)))
      return false
    return !search || option.label.toLowerCase().includes(search) || String(option.value).toLowerCase().includes(search)
  })
})

function generateSKU() {
  localFormState.sku = `SKU-${Math.random()
    .toString(36)
    .substring(7)
    .toUpperCase()}`;
}

function addRecommendedProduct() {
  const productId = Number(selectedRecommendedProductId.value)
  if (!Number.isFinite(productId) || productId <= 0)
    return

  const current = (localFormState.recommendedProductIds || []).map(Number)
  if (!current.includes(productId))
    localFormState.recommendedProductIds = [...current, productId]
  selectedRecommendedProductId.value = ""
}

function selectCategory(value: string) {
  localFormState.category = value
  categorySearch.value = ''
  isCategoryPickerOpen.value = false
}

function selectRecommendedProduct(value: string) {
  selectedRecommendedProductId.value = value
  addRecommendedProduct()
  recommendedProductSearch.value = ''
  isRecommendedPickerOpen.value = false
}

function removeRecommendedProduct(productId: number) {
  localFormState.recommendedProductIds = (localFormState.recommendedProductIds || []).filter(id => id !== productId)
}

function addSpecificationRow() {
  if (!localFormState.specificationRows)
    localFormState.specificationRows = []
  localFormState.specificationRows.push({ key: "", value: "", unit: "" })
}

function removeSpecificationRow(index: number) {
  localFormState.specificationRows?.splice(index, 1)
}

function emitSubmit(data: ProductFormSchema) {
  emit("onSubmit", {
    data: { ...data },
  } as FormSubmitEvent<ProductFormSchema>);
}

function submitForm() {
  const result = productSchema.safeParse(localFormState);
  if (!result.success) {
    // handle errors, e.g. show a toast or set error state
    return;
  }
  emitSubmit(result.data);
}

function onSubmit(e: FormSubmitEvent<ProductFormSchema>) {
  emitSubmit(e.data);
}
</script>

<template>
  <div>
    <slot name="header" :submit="submitForm" />
    <UForm :schema="productSchema" :state="localFormState" @submit="onSubmit">
      <slot :submit="submitForm" />
      <div class="mx-auto max-w-screen-xl">
        <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div class="lg:col-span-2 space-y-6 pb-24">
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Product Information
                </h3>
              </template>
              <div class="space-y-4">
                <UFormField label="Product Name" name="name" required>
                  <UInput
                    v-model="localFormState.name"
                    placeholder="e.g. 1000LPH RO System Assembly"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Description" name="description">
                  <UTextarea
                    v-model="localFormState.description"
                    placeholder="Describe the product, use case, and important buying details..."
                    :rows="6"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Catalogue
                </h3>
              </template>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <UFormField label="Category" name="category">
                  <div class="relative">
                    <UInput
                      v-model="categorySearch"
                      icon="i-lucide-search"
                      :placeholder="selectedCategoryLabel || 'Search categories...'"
                      size="lg"
                      class="w-full"
                      @focus="isCategoryPickerOpen = true"
                      @input="isCategoryPickerOpen = true"
                    />
                    <div
                      v-if="isCategoryPickerOpen"
                      class="absolute z-20 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white p-1 shadow-lg"
                    >
                      <button
                        v-for="item in filteredCategories"
                        :key="item.value"
                        type="button"
                        class="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-blue-50"
                        :class="localFormState.category === item.value ? 'bg-blue-50 font-semibold text-blue-700' : 'text-slate-700'"
                        @click="selectCategory(item.value)"
                      >
                        <span class="truncate">{{ item.label }}</span>
                        <UIcon v-if="localFormState.category === item.value" name="i-lucide-check" class="size-4" />
                      </button>
                      <p v-if="filteredCategories.length === 0" class="px-3 py-2 text-sm text-slate-500">
                        No matching categories.
                      </p>
                    </div>
                  </div>
                  <p v-if="!categories.length" class="mt-2 text-xs text-amber-600">
                    Category management is waiting for the backend admin category API. You can still save the product without a category.
                  </p>
                </UFormField>
                <UFormField label="Brand" name="brand">
                  <UInput
                    v-model="localFormState.brand"
                    placeholder="e.g. Hidrotek"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Tags" name="tags" class="sm:col-span-2">
                  <UInput
                    v-model="localFormState.tags"
                    placeholder="pump, reverse osmosis, tank"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Engineering Specs
                </h3>
              </template>
              <div class="space-y-4">
                <UFormField label="Product class" name="productClass">
                  <USelect
                    v-model="localFormState.productClass"
                    :items="domainProductClassOptions"
                    value-attribute="value"
                    option-attribute="label"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Engineering brand">
                  <UInput
                    v-model="localFormState.engineeringBrand"
                    placeholder="e.g. Grundfos, Norwa, Hidrotek"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>

                <div class="rounded-lg border border-slate-200 p-4">
                  <div class="mb-4 flex items-center gap-2">
                    <UIcon name="i-lucide-ruler" class="size-4 text-blue-600" />
                    <h4 class="text-sm font-bold text-slate-950">
                      Packing dimensions
                    </h4>
                  </div>
                  <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <UFormField label="Length">
                      <UInput v-model="localFormState.packingDimensions.length.value" type="number" step="0.01" placeholder="0" size="lg">
                        <template #trailing>
                          <USelect v-model="localFormState.packingDimensions.length.unit" :items="dimensionUnitOptions" value-attribute="value" option-attribute="label" variant="ghost" class="w-20" />
                        </template>
                      </UInput>
                    </UFormField>
                    <UFormField label="Width">
                      <UInput v-model="localFormState.packingDimensions.width.value" type="number" step="0.01" placeholder="0" size="lg">
                        <template #trailing>
                          <USelect v-model="localFormState.packingDimensions.width.unit" :items="dimensionUnitOptions" value-attribute="value" option-attribute="label" variant="ghost" class="w-20" />
                        </template>
                      </UInput>
                    </UFormField>
                    <UFormField label="Height">
                      <UInput v-model="localFormState.packingDimensions.height.value" type="number" step="0.01" placeholder="0" size="lg">
                        <template #trailing>
                          <USelect v-model="localFormState.packingDimensions.height.unit" :items="dimensionUnitOptions" value-attribute="value" option-attribute="label" variant="ghost" class="w-20" />
                        </template>
                      </UInput>
                    </UFormField>
                    <UFormField label="Weight">
                      <UInput v-model="localFormState.packingDimensions.weight.value" type="number" step="0.01" placeholder="0" size="lg">
                        <template #trailing>
                          <USelect v-model="localFormState.packingDimensions.weight.unit" :items="weightUnitOptions" value-attribute="value" option-attribute="label" variant="ghost" class="w-20" />
                        </template>
                      </UInput>
                    </UFormField>
                    <UFormField label="Quantity">
                      <UInput v-model="localFormState.packingDimensions.quantity.value" type="number" step="1" placeholder="0" size="lg">
                        <template #trailing>
                          <USelect v-model="localFormState.packingDimensions.quantity.unit" :items="quantityUnitOptions" value-attribute="value" option-attribute="label" variant="ghost" class="w-20" />
                        </template>
                      </UInput>
                    </UFormField>
                  </div>
                </div>

                <div class="rounded-lg border border-slate-200 p-4">
                  <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div class="flex items-center gap-2">
                      <UIcon name="i-lucide-list-plus" class="size-4 text-blue-600" />
                      <h4 class="text-sm font-bold text-slate-950">
                        Technical specifications
                      </h4>
                    </div>
                    <UButton icon="i-lucide-plus" size="sm" variant="outline" type="button" @click="addSpecificationRow">
                      Add spec
                    </UButton>
                  </div>
                  <div v-if="localFormState.specificationRows?.length" class="space-y-3">
                    <div
                      v-for="(row, index) in localFormState.specificationRows"
                      :key="index"
                      class="grid grid-cols-1 gap-2 sm:grid-cols-[1.2fr_1fr_120px_auto]"
                    >
                      <UInput v-model="row.key" placeholder="Spec name e.g. max_flow_rate" size="lg" />
                      <UInput v-model="row.value" placeholder="Value e.g. 60" size="lg" />
                      <UInput v-model="row.unit" placeholder="Unit e.g. lpm" size="lg" />
                      <UButton
                        icon="i-lucide-trash-2"
                        color="error"
                        variant="ghost"
                        square
                        type="button"
                        :aria-label="`Remove specification ${index + 1}`"
                        @click="removeSpecificationRow(index)"
                      />
                    </div>
                  </div>
                  <p v-else class="text-sm text-slate-500">
                    Add flow rate, pressure, voltage, material, temperature, or other product-specific specs.
                  </p>
                </div>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Upselling
                </h3>
              </template>
              <div class="space-y-4">
                <div class="flex flex-col gap-3 sm:flex-row">
                  <UFormField label="Recommended product" class="min-w-0 flex-1">
                    <div class="relative">
                      <UInput
                        v-model="recommendedProductSearch"
                        icon="i-lucide-search"
                        placeholder="Search products to recommend..."
                        size="lg"
                        class="w-full"
                        @focus="isRecommendedPickerOpen = true"
                        @input="isRecommendedPickerOpen = true"
                      />
                      <div
                        v-if="isRecommendedPickerOpen"
                        class="absolute z-20 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white p-1 shadow-lg"
                      >
                        <button
                          v-for="item in availableRecommendedProductOptions"
                          :key="item.value"
                          type="button"
                          class="w-full rounded-md px-3 py-2 text-left text-sm text-slate-700 hover:bg-blue-50"
                          @click="selectRecommendedProduct(item.value)"
                        >
                          <span class="block truncate">{{ item.label }}</span>
                        </button>
                        <p v-if="availableRecommendedProductOptions.length === 0" class="px-3 py-2 text-sm text-slate-500">
                          {{ isSearchingRecommendedProducts ? 'Searching products...' : 'No matching products.' }}
                        </p>
                      </div>
                    </div>
                  </UFormField>
                  <div class="flex items-end">
                    <UButton
                      icon="i-lucide-plus"
                      color="primary"
                      variant="outline"
                      :disabled="!selectedRecommendedProductId"
                      @click="addRecommendedProduct"
                    >
                      Add
                    </UButton>
                  </div>
                </div>
                <div v-if="selectedRecommendedProducts.length" class="space-y-2">
                  <div
                    v-for="item in selectedRecommendedProducts"
                    :key="item.value"
                    class="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2"
                  >
                    <span class="min-w-0 truncate text-sm font-medium text-slate-700">{{ item.label }}</span>
                    <UButton
                      icon="i-lucide-x"
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      square
                      :aria-label="`Remove ${item.label}`"
                      @click="removeRecommendedProduct(Number(item.value))"
                    />
                  </div>
                </div>
                <p v-else class="text-sm text-slate-500">
                  No upsell products selected.
                </p>
              </div>
            </UCard>
            <UCard v-if="dynamicAttributeDefinitions.length" class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Product Attributes
                </h3>
              </template>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <UFormField
                  v-for="attribute in dynamicAttributeDefinitions"
                  :key="attribute.id"
                  :label="`${attribute.name}${attribute.uom ? ` (${attribute.uom})` : ''}`"
                  :required="attribute.required"
                >
                  <UCheckbox
                    v-if="attribute.type === 'boolean'"
                    v-model="localFormState.attributes[attribute.code]"
                    :label="attribute.name"
                  />
                  <UInput
                    v-else
                    v-model="localFormState.attributes[attribute.code]"
                    :type="['integer', 'float'].includes(attribute.type) ? 'number' : 'text'"
                    :step="attribute.type === 'float' ? '0.01' : undefined"
                    :placeholder="attribute.parent_attribute_name ? `Child of ${attribute.parent_attribute_name}` : 'Enter value'"
                    size="lg"
                    class="w-full"
                  >
                    <template v-if="attribute.uom" #trailing>
                      <span class="text-dimmed text-xs">{{ attribute.uom }}</span>
                    </template>
                  </UInput>
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  SEO
                </h3>
              </template>
              <div class="space-y-4">
                <UFormField label="URL slug" name="slug">
                  <UInput
                    v-model="localFormState.slug"
                    placeholder="1000lph-ro-system-assembly"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Meta title" name="metaTitle">
                  <UInput
                    v-model="localFormState.metaTitle"
                    placeholder="1000LPH RO System Assembly"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Meta description" name="metaDescription">
                  <UTextarea
                    v-model="localFormState.metaDescription"
                    placeholder="Short search result description for this product."
                    :rows="3"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Pricing
                </h3>
              </template>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_150px]">
                <UFormField label="Price" name="price" required>
                  <UInput
                    v-model.number="localFormState.price"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    size="lg"
                    class="w-full"
                  >
                    <template #leading>
                      <span class="text-xs text-slate-500">{{ localFormState.currency }}</span>
                    </template>
                  </UInput>
                </UFormField>
                <UFormField label="Currency" name="currency">
                  <USelect
                    v-model="localFormState.currency"
                    :items="[
                      { label: 'KES', value: 'KES' },
                      { label: 'USD', value: 'USD' },
                    ]"
                    value-attribute="value"
                    option-attribute="label"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
              </div>
              <div class="mt-4 border-t border-slate-200 pt-4">
                <UFormField name="chargeTax">
                  <UCheckbox
                    v-model="localFormState.chargeTax"
                    label="Charge tax on this product"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Inventory
                </h3>
              </template>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="SKU (Stock Keeping Unit)" name="sku">
                  <UInput
                    v-model="localFormState.sku"
                    placeholder="e.g. RO-SYSTEM-1000"
                    size="lg"
                    class="w-full"
                  >
                    <template #trailing>
                      <UIcon
                        name="i-lucide-refresh-cw"
                        color="neutral"
                        variant="ghost"
                        square
                        aria-label="Generate SKU"
                        @click="generateSKU"
                      />
                    </template>
                  </UInput>
                </UFormField>
                <UFormField label="Stock Quantity" name="stock" required>
                  <UInput
                    v-model.number="localFormState.stock"
                    type="number"
                    placeholder="0"
                    size="lg"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Shipping
                </h3>
              </template>
              <UFormField label="Weight (grams)" name="weight">
                <UInput
                  v-model.number="localFormState.weight"
                  type="number"
                  placeholder="0"
                  size="lg"
                  class="w-full"
                >
                  <template #trailing>
                    <span class="text-dimmed text-xs">grams</span>
                  </template>
                </UInput>
              </UFormField>
              <UFormField
                label="Dimensions (L x W x H)"
                name="dimensions"
                class="mt-4"
              >
                <UInput
                  v-model="localFormState.dimensions"
                  placeholder="e.g. 20 x 15 x 5 cm"
                  size="lg"
                  class="w-full"
                />
              </UFormField>
            </UCard>
          </div>
          <div class="lg:col-span-1 space-y-6">
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Status
                </h3>
              </template>
              <UFormField name="status" required>
                <USelect
                  v-model="localFormState.status"
                  :items="statusOptions"
                  value-attribute="value"
                  option-attribute="label"
                  size="lg"
                  class="w-full"
                />
              </UFormField>
            </UCard>
            <UCard class="rounded-xl">
              <template #header>
                <h3 class="text-base font-black leading-6 text-slate-950">
                  Product Images
                </h3>
              </template>
              <p class="mb-2 text-sm text-slate-500">Choose product photos or drag and drop up to 5 images here.</p>
              <slot name="images" :images="localFormState.images" @update:images="localFormState.images = $event" />
            </UCard>
            <slot name="stock" />
          </div>
        </div>
      </div>
    </UForm>
  </div>
</template>
