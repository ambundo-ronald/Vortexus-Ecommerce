<script setup lang="ts">
import * as z from "zod/v4";
import type { FormSubmitEvent } from "@nuxt/ui";

const props = defineProps<{
  values?: Partial<ProductFormSchema>;
  statusOptions: { label: string; value: string; icon: string; color: string }[];
  categories: { label: string; value: string }[];
}>();

const emit = defineEmits<{
  (e: "onSubmit", event: FormSubmitEvent<any>): void;
}>();

const productSchema = z.object({
  name: z
    .string({ error: "Product name is required" })
    .min(1, "Product name cannot be empty"),
  description: z.string().optional(),
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
});

export type ProductFormSchema = z.infer<typeof productSchema>;

const localFormState = reactive<ProductFormSchema>({
  name: "",
  description: "",
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
  ...props.values,
}) as ProductFormSchema;

watch(
  () => props.values,
  (values) => {
    if (!values) return
    Object.assign(localFormState, {
      name: "",
      description: "",
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
      ...values,
    })
  },
  { immediate: true, deep: true },
)

function generateSKU() {
  localFormState.sku = `SKU-${Math.random()
    .toString(36)
    .substring(7)
    .toUpperCase()}`;
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
                  <USelect
                    v-model="localFormState.category"
                    :items="[{ label: 'Uncategorized', value: '__uncategorized__' }, ...categories]"
                    value-attribute="value"
                    option-attribute="label"
                    size="lg"
                    class="w-full"
                  />
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
