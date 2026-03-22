<script setup lang="ts">
import { h, resolveComponent } from "vue";
import type { TableColumn } from "@nuxt/ui";

interface Product {
  id: number;
  name: string;
  category: string;
  stock: number;
  image: string;
}

defineProps<{
  products: Product[];
}>();

const columns: TableColumn<Product>[] = [
  {
    accessorKey: "image",
    header: "Image",
    cell: (ctx) => {
      const image = ctx.row.getValue("image") as string;
      const name = ctx.row.getValue("name") as string;
      if (image) {
        return h(
          "div",
          {
            class:
              "w-10 h-10 rounded bg-muted flex items-center justify-center overflow-hidden",
          },
          [h("img", { src: image, alt: name, class: "object-contain" })]
        );
      }
      return h(
        "div",
        {
          class:
            "w-10 h-10 rounded bg-muted flex items-center justify-center overflow-hidden",
        },
        [h("span", { class: "i-lucide-image text-2xl text-dimmed" })]
      );
    },
  },
  {
    accessorKey: "name",
    header: "Product",
    cell: (ctx) => ctx.row.getValue("name"),
  },
  {
    accessorKey: "stock",
    header: "Stock",
    cell: (ctx) => {
      const stock = ctx.row.getValue("stock") as number;
      let label = "In stock",
        color = "success";
      if (stock === 0) {
        label = "Out of stock";
        color = "error";
      } else if (stock < 10) {
        label = "Low stock";
        color = "warning";
      }
      return h(resolveComponent("UBadge"), {
        label,
        color,
        variant: "subtle",
        class: "font-medium rounded-full px-3 py-1 capitalize",
      });
    },
  },
];
</script>

<template>
  <UCard class="w-full">
    <div class="flex items-center justify-between">
      <h3 class="text-base font-semibold text-highlighted">Popular Products</h3>
    </div>
    <UTable
      :columns="columns"
      :data="products"
      class="w-full"
      :ui="{
        root: 'bg-transparent dark:bg-transparent !border-hidden dark:border-hidden',
      }"
    />
  </UCard>
</template>
