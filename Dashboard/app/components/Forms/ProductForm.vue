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
    .enum(["active", "draft", "archived"], {
      error: "Status is required",
    })
    .default("draft"),
  category: z
    .string({ error: "Category is required" })
    .min(1, "Category cannot be empty"),
  brand: z.string().optional(),
  tags: z.string().optional(),
});

export type ProductFormSchema = z.infer<typeof productSchema>;

const localFormState = reactive<ProductFormSchema>({
  name: "",
  description: "",
  images: [],
  price: 0,
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

function generateSKU() {
  localFormState.sku = `SKU-${Math.random()
    .toString(36)
    .substring(7)
    .toUpperCase()}`;
}

function onSubmit(e: FormSubmitEvent<any>) {
  const result = productSchema.safeParse(localFormState);
  if (!result.success) {
    // handle errors, e.g. show a toast or set error state
    return;
  }
  emit("onSubmit", e);
}
</script>

<template>
  <div>
    <slot name="header"/>
    <UForm :schema="productSchema" :state="localFormState" @submit="onSubmit">
      <slot :submit="onSubmit" />
      <div class="max-w-screen-xl mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2 space-y-6 pb-24">
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Product Information
                </h3>
              </template>
              <div class="space-y-4">
                <UFormField label="Product Name" name="name" required>
                  <UInput
                    v-model="localFormState.name"
                    placeholder="e.g. Summer T-Shirt"
                    size="md"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Description" name="description">
                  <UTextarea
                    v-model="localFormState.description"
                    placeholder="Describe your product..."
                    :rows="6"
                    size="md"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Pricing
                </h3>
              </template>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="Price" name="price" required>
                  <UInput
                    v-model.number="localFormState.price"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    size="md"
                    class="w-full"
                  >
                    <template #leading>
                      <span class="text-dimmed text-xs">USD</span>
                    </template>
                  </UInput>
                </UFormField>
                <UFormField label="Original Price" name="originalPrice">
                  <UInput
                    v-model.number="localFormState.originalPrice"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    size="md"
                    class="w-full"
                  >
                    <template #leading>
                      <span class="text-dimmed text-xs">USD</span>
                    </template>
                  </UInput>
                </UFormField>
              </div>
              <div class="mt-4 border-t border-default pt-4">
                <UFormField name="chargeTax">
                  <UCheckbox
                    v-model="localFormState.chargeTax"
                    label="Charge tax on this product"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Inventory
                </h3>
              </template>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="SKU (Stock Keeping Unit)" name="sku">
                  <UInput
                    v-model="localFormState.sku"
                    placeholder="e.g. TSHIRT-RED-LG"
                    size="md"
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
                    size="md"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </UCard>
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Shipping
                </h3>
              </template>
              <UFormField label="Weight (grams)" name="weight">
                <UInput
                  v-model.number="localFormState.weight"
                  type="number"
                  placeholder="0"
                  size="md"
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
                  size="md"
                  class="w-full"
                />
              </UFormField>
            </UCard>
          </div>
          <div class="lg:col-span-1 space-y-6">
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Status
                </h3>
              </template>
              <UFormField name="status" required>
                <USelect
                  v-model="localFormState.status"
                  :items="statusOptions"
                  value-attribute="value"
                  option-attribute="label"
                  size="md"
                  class="w-full"
                />
              </UFormField>
            </UCard>
            <UCard>
              <template #header>
                <h3 class="text-base font-semibold leading-6 text-default">
                  Product Images
                </h3>
              </template>
              <p class="text-sm text-dimmed mb-2">Choose a product photo or simply drag and drop up to 5 photos here.</p>
              <slot name="images" :images="localFormState.images" @update:images="localFormState.images = $event" />
            </UCard>
            <slot name="stock" />
          </div>
        </div>
      </div>
    </UForm>
  </div>
</template>
